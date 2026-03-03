"""
Media API Routes (FastAPI 版本)
"""
import logging
import os
import subprocess
import aiofiles
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from app.database import get_db
from app.core.config import settings
from app.api.deps import get_current_user
from app.models.media import MediaFile, MediaFolder

logger = logging.getLogger(__name__)
router = APIRouter()

DEFAULT_PAGE_SIZE = 20


# ============= Pydantic 模型 =============

class MediaUpdate(BaseModel):
    file_name: Optional[str] = None
    folder_id: Optional[int] = None


class PaginatedMediaResponse(BaseModel):
    media: list
    total: int
    page: int
    per_page: int
    pages: int


# ============= 辅助函数 =============

def allowed_file(filename: str, file_type: str) -> bool:
    """检查文件扩展名是否允许"""
    if '.' not in filename:
        return False

    ext = filename.rsplit('.', 1)[1].lower()

    allowed_map = {
        'image': {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'},
        'video': {'mp4', 'webm', 'mov', 'avi', 'mkv'},
        'ppt': {'ppt', 'pptx', 'pdf'}
    }

    return ext in allowed_map.get(file_type, set())


def get_safe_filename(filename: str) -> str:
    """获取安全的文件名"""
    # 移除路径分隔符和其他危险字符
    safe_chars = set(
        'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-')

    # 分离文件名和扩展名
    if '.' in filename:
        name, ext = filename.rsplit('.', 1)
        ext = ''.join(c for c in ext if c in safe_chars)
    else:
        name, ext = filename, ''

    # 清理文件名
    safe_name = ''.join(c if c in safe_chars else '_' for c in name)

    if not safe_name:
        safe_name = f"file_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

    return f"{safe_name}.{ext}" if ext else safe_name


def resolve_file_path(path: str) -> str:
    """安全解析文件路径"""
    # 规范化路径
    abs_path = os.path.abspath(path)

    # 检查是否在允许的目录内
    storage_path = os.path.abspath(settings.STORAGE_PATH)
    if not abs_path.startswith(storage_path):
        raise ValueError(f"Path outside storage directory: {path}")

    return abs_path


# ============= API 端点 =============

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_media(
    file: UploadFile = File(...),
    file_type: str = Form(...),
    folder_id: Optional[int] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """上传媒体文件"""
    if file_type not in ['image', 'video', 'ppt']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file_type"
        )

    if not allowed_file(file.filename, file_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed for {file_type}"
        )

    # 保存原始文件名
    original_filename = file.filename

    # 生成安全文件名
    safe_filename = get_safe_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_filename = f"{timestamp}_{safe_filename}"

    # 保存文件
    file_path = os.path.join(settings.UPLOAD_FOLDER, unique_filename)

    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)

    file_size = os.path.getsize(file_path)

    # 创建数据库记录
    media_file = MediaFile(
        file_name=original_filename,
        file_type=file_type,
        file_path=file_path,
        file_size=file_size,
        folder_id=folder_id,
        status='ready' if file_type != 'ppt' else 'processing'
    )

    db.add(media_file)
    await db.commit()
    await db.refresh(media_file)

    # TODO: 如果是 PPT，触发转换任务 (RQ)

    return {
        "message": "File uploaded successfully",
        "media": media_file.to_dict()
    }


@router.get("", response_model=PaginatedMediaResponse)
async def list_media(
    page: int = Query(1, ge=1),
    per_page: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=100),
    file_type: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    folder_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """媒体文件列表"""
    query = select(MediaFile)
    count_query = select(func.count(MediaFile.id))

    if file_type:
        query = query.where(MediaFile.file_type == file_type)
        count_query = count_query.where(MediaFile.file_type == file_type)

    if status_filter:
        query = query.where(MediaFile.status == status_filter)
        count_query = count_query.where(MediaFile.status == status_filter)

    # 文件夹过滤
    if folder_id is not None:
        if folder_id == 'null' or folder_id == '':
            query = query.where(MediaFile.folder_id.is_(None))
            count_query = count_query.where(MediaFile.folder_id.is_(None))
        else:
            try:
                fid = int(folder_id)
                query = query.where(MediaFile.folder_id == fid)
                count_query = count_query.where(MediaFile.folder_id == fid)
            except ValueError:
                pass

    # 获取总数
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # 分页查询
    query = query.order_by(MediaFile.upload_time.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    media_list = result.scalars().all()

    pages = (total + per_page - 1) // per_page

    return PaginatedMediaResponse(
        media=[m.to_dict() for m in media_list],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages
    )


@router.get("/{media_id}")
async def get_media(
    media_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """获取媒体文件详情"""
    result = await db.execute(select(MediaFile).where(MediaFile.id == media_id))
    media = result.scalar_one_or_none()

    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found"
        )

    return media.to_dict()


@router.put("/{media_id}")
async def update_media(
    media_id: int,
    media_data: MediaUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """更新媒体文件信息"""
    result = await db.execute(select(MediaFile).where(MediaFile.id == media_id))
    media = result.scalar_one_or_none()

    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found"
        )

    if media_data.file_name is not None:
        media.file_name = media_data.file_name

    if media_data.folder_id is not None:
        media.folder_id = media_data.folder_id

    await db.commit()

    return {
        "message": "Media updated successfully",
        "media": media.to_dict()
    }


@router.delete("/{media_id}")
async def delete_media(
    media_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """删除媒体文件"""
    result = await db.execute(select(MediaFile).where(MediaFile.id == media_id))
    media = result.scalar_one_or_none()

    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found"
        )

    # 删除物理文件
    try:
        if media.file_path and os.path.exists(media.file_path):
            os.remove(media.file_path)
            logger.info(f"Deleted file: {media.file_path}")
    except Exception as e:
        logger.error(f"Error deleting file: {e}")

    # 删除转换后的文件
    if media.converted_path:
        try:
            if os.path.exists(media.converted_path):
                os.remove(media.converted_path)
        except Exception as e:
            logger.warning(f"Cannot delete converted file: {e}")

    # 删除缩略图
    if media.thumbnail_path:
        try:
            if os.path.exists(media.thumbnail_path):
                os.remove(media.thumbnail_path)
        except Exception as e:
            logger.warning(f"Cannot delete thumbnail: {e}")

    await db.delete(media)
    await db.commit()

    return {"message": "Media deleted successfully"}


@router.get("/{media_id}/download")
async def download_media(
    media_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """下载媒体文件"""
    result = await db.execute(select(MediaFile).where(MediaFile.id == media_id))
    media = result.scalar_one_or_none()

    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found"
        )

    # 如果是 PPT 且已转换，返回转换后的视频
    if media.file_type == 'ppt' and media.converted_path:
        file_path = media.converted_path
    else:
        file_path = media.file_path

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    return FileResponse(
        file_path,
        filename=os.path.basename(file_path),
        media_type='application/octet-stream'
    )


@router.get("/{media_id}/thumbnail")
async def get_thumbnail(
    media_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """获取缩略图"""
    result = await db.execute(select(MediaFile).where(MediaFile.id == media_id))
    media = result.scalar_one_or_none()

    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found"
        )

    # 1. 优先使用已生成的缩略图
    if media.thumbnail_path and os.path.exists(media.thumbnail_path):
        return FileResponse(media.thumbnail_path, media_type='image/jpeg')

    # 2. 图片类型：直接返回原图
    if media.file_type == 'image' and os.path.exists(media.file_path):
        ext = os.path.splitext(media.file_name)[1].lower()
        mime_map = {
            '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
            '.png': 'image/png', '.gif': 'image/gif',
            '.bmp': 'image/bmp', '.webp': 'image/webp'
        }
        mime = mime_map.get(ext, 'image/jpeg')
        return FileResponse(media.file_path, media_type=mime)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Thumbnail not available"
    )
