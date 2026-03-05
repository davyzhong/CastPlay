"""
媒体文件管理 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import os

from app.database import get_db
from app.models.media import MediaFile
from app.schemas.media import MediaFileResponse, MediaFileListResponse, UploadResponse
from app.api.auth import get_current_user
from app.models.user import User
from app.utils.file_utils import (
    get_file_extension,
    validate_file_type,
    validate_file_content,
    get_unique_filename,
    calculate_md5,
    generate_thumbnail,
    safe_delete_file,
    format_file_size
)
from app.config import settings
from app.utils.logger import logger
from app.workers import task_manager

router = APIRouter()


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_media(
    file: UploadFile = File(...),
    file_type: str = Query(..., pattern="^(image|video|ppt)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    上传媒体文件

    - **file**: 上传的文件
    - **file_type**: 文件类型（image/video/ppt）

    支持的格式：
    - image: jpg, jpeg, png, gif, bmp
    - video: mp4, avi, mov, mkv, flv
    - ppt: ppt, pptx
    """
    # 验证文件扩展名
    if not validate_file_type(file.filename, file_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension not supported for {file_type}"
        )

    # 读取文件内容
    contents = await file.read()
    file_size = len(contents)

    # 检查文件大小
    if file_size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds limit ({format_file_size(settings.MAX_FILE_SIZE)})"
        )

    # 验证文件实际内容（Magic Number 检查）
    content_valid, content_error = validate_file_content(contents, file_type)
    if not content_valid:
        logger.warning(f"File content validation failed for {file.filename}: {content_error}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File content validation failed: {content_error}"
        )

    # 生成唯一文件名
    filename = get_unique_filename(str(settings.UPLOADS_DIR), file.filename)
    file_path = str(settings.UPLOADS_DIR / filename)

    # 保存文件
    with open(file_path, "wb") as f:
        f.write(contents)

    # 计算 MD5
    md5_hash = calculate_md5(file_path)

    # 生成缩略图（仅图片）
    thumbnail_path = None
    ext = get_file_extension(filename)
    if file_type == "image":
        thumbnail_name = f"thumb_{os.path.splitext(filename)[0]}.jpg"
        thumbnail_path = str(settings.THUMBNAILS_DIR / thumbnail_name)
        generate_thumbnail(file_path, thumbnail_path)

    # 创建数据库记录
    new_media = MediaFile(
        file_name=file.filename,
        file_type=file_type,
        file_path=file_path,
        file_size=file_size,
        thumbnail_path=thumbnail_path,
        md5_hash=md5_hash,
        status="ready" if file_type != "ppt" else "processing"  # PPT 文件初始状态为 processing
    )
    db.add(new_media)
    db.commit()
    db.refresh(new_media)

    logger.info(f"Media uploaded: {file.filename} ({file_type})")

    # 如果是 PPT 文件，提交转换任务
    if file_type == "ppt":
        from app.services.converter import PPTConverter
        converter = PPTConverter()
        available, msg = converter.is_available()
        if not available:
            logger.warning(f"PPT conversion not available: {msg}")
            new_media.status = "failed"
            db.commit()
        else:
            # 提交后台转换任务
            task_manager.submit_task(
                "convert_ppt",
                {
                    "media_id": new_media.id,
                    "file_path": file_path
                }
            )
            logger.info(f"PPT conversion task submitted for media {new_media.id}")

    return {
        "message": "File uploaded successfully",
        "media": new_media
    }


@router.get("/", response_model=MediaFileListResponse)
def list_media(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    file_type: Optional[str] = Query(None, pattern="^(image|video|ppt)$"),
    status_filter: Optional[str] = Query(None, pattern="^(ready|processing|failed)$"),
    db: Session = Depends(get_db)
):
    """
    获取媒体文件列表

    - **skip**: 跳过数量（分页）
    - **limit**: 返回数量（分页）
    - **file_type**: 过滤文件类型
    - **status_filter**: 过滤状态
    """
    query = db.query(MediaFile)

    if file_type:
        query = query.filter(MediaFile.file_type == file_type)

    if status_filter:
        query = query.filter(MediaFile.status == status_filter)

    total = query.count()
    media_list = query.order_by(MediaFile.id.desc()).offset(skip).limit(limit).all()

    pages = (total + limit - 1) // limit if total > 0 else 0

    return {
        "items": media_list,
        "total": total,
        "page": skip // limit + 1,
        "per_page": limit,
        "pages": pages
    }


@router.get("/{media_id}", response_model=MediaFileResponse)
def get_media(media_id: int, db: Session = Depends(get_db)):
    """
    获取媒体文件详情
    """
    media = db.query(MediaFile).filter(MediaFile.id == media_id).first()
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media file not found"
        )
    return media


@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_media(
    media_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除媒体文件

    需要认证
    """
    media = db.query(MediaFile).filter(MediaFile.id == media_id).first()
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media file not found"
        )

    # 删除文件
    safe_delete_file(media.file_path)
    if media.converted_path:
        safe_delete_file(media.converted_path)
    if media.thumbnail_path:
        safe_delete_file(media.thumbnail_path)

    # 删除数据库记录
    db.delete(media)
    db.commit()

    logger.info(f"Media deleted: {media.file_name}")
    return None


@router.get("/{media_id}/download")
def download_media(media_id: int, db: Session = Depends(get_db)):
    """
    下载媒体文件

    如果是 PPT 且已转换，返回转换后的视频
    否则返回原始文件
    """
    from fastapi.responses import FileResponse

    media = db.query(MediaFile).filter(MediaFile.id == media_id).first()
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media file not found"
        )

    # 返回转换后的文件（如果存在）
    file_path = media.converted_path if media.converted_path else media.file_path

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    return FileResponse(
        file_path,
        filename=media.file_name,
        media_type="application/octet-stream"
    )


@router.get("/{media_id}/thumbnail")
def get_thumbnail(media_id: int, db: Session = Depends(get_db)):
    """
    获取媒体文件缩略图
    """
    from fastapi.responses import FileResponse

    media = db.query(MediaFile).filter(MediaFile.id == media_id).first()
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media file not found"
        )

    if not media.thumbnail_path or not os.path.exists(media.thumbnail_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thumbnail not found"
        )

    return FileResponse(
        media.thumbnail_path,
        media_type="image/jpeg"
    )


@router.post("/{media_id}/retry", response_model=MediaFileResponse)
def retry_conversion(
    media_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    重试 PPT 转换

    仅对状态为 failed 且类型为 ppt 的媒体文件有效

    需要认证
    """
    media = db.query(MediaFile).filter(MediaFile.id == media_id).first()
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media file not found"
        )

    if media.file_type != "ppt":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PPT files can be retried"
        )

    if media.status != "failed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot retry: current status is '{media.status}', not 'failed'"
        )

    # 检查转换工具是否可用
    from app.services.converter import PPTConverter
    converter = PPTConverter()
    available, msg = converter.is_available()
    if not available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Conversion tools not available: {msg}"
        )

    # 检查源文件是否存在
    if not media.file_path or not os.path.exists(media.file_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source file not found"
        )

    # 更新状态为处理中
    media.status = "processing"
    db.commit()

    # 提交转换任务
    task_manager.submit_task(
        "convert_ppt",
        {
            "media_id": media.id,
            "file_path": media.file_path
        }
    )
    logger.info(f"PPT conversion retry submitted for media {media.id}")

    return media
