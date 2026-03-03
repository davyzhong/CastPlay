"""
Media Folder API Routes (FastAPI 版本)
"""
import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field

from app.database import get_db
from app.api.deps import get_current_user
from app.models.media import MediaFolder, MediaFile

logger = logging.getLogger(__name__)
router = APIRouter()


# ============= Pydantic 模型 =============

class FolderCreate(BaseModel):
    name: str = Field(..., max_length=128)
    parent_id: Optional[int] = None


class FolderUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=128)
    parent_id: Optional[int] = None


class MoveFilesRequest(BaseModel):
    file_ids: List[int]


# ============= API 端点 =============

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_folder(
    folder_data: FolderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """创建文件夹"""
    # 检查父文件夹是否存在
    if folder_data.parent_id:
        result = await db.execute(
            select(MediaFolder).where(MediaFolder.id == folder_data.parent_id)
        )
        parent = result.scalar_one_or_none()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent folder not found"
            )

    # 检查同名文件夹
    result = await db.execute(
        select(MediaFolder).where(
            MediaFolder.name == folder_data.name,
            MediaFolder.parent_id == folder_data.parent_id
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Folder with this name already exists"
        )

    folder = MediaFolder(name=folder_data.name,
                         parent_id=folder_data.parent_id)
    db.add(folder)
    await db.commit()
    await db.refresh(folder)

    return {
        "message": "Folder created successfully",
        "folder": folder.to_dict()
    }


@router.get("")
async def list_folders(
    parent_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """获取文件夹列表"""
    if parent_id:
        query = select(MediaFolder).where(MediaFolder.parent_id == parent_id)
    else:
        query = select(MediaFolder).where(MediaFolder.parent_id.is_(None))

    query = query.order_by(MediaFolder.name)
    result = await db.execute(query)
    folders = result.scalars().all()

    return {
        "folders": [f.to_dict() for f in folders]
    }


@router.get("/tree")
async def get_folder_tree(
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """获取完整的文件夹树"""
    # 获取所有文件夹
    result = await db.execute(
        select(MediaFolder).options(selectinload(MediaFolder.children))
    )
    all_folders = result.scalars().all()

    # 构建文件夹映射
    folder_map = {f.id: f for f in all_folders}

    # 递归构建树
    def build_tree(folder):
        result = folder.to_dict()
        result['children'] = [build_tree(child) for child in folder.children]
        return result

    # 获取根级文件夹
    root_folders = [f for f in all_folders if f.parent_id is None]
    tree = [build_tree(f) for f in root_folders]

    return {"tree": tree}


@router.get("/{folder_id}")
async def get_folder(
    folder_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """获取文件夹详情"""
    query = select(MediaFolder).options(
        selectinload(MediaFolder.children)
    ).where(MediaFolder.id == folder_id)

    result = await db.execute(query)
    folder = result.scalar_one_or_none()

    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )

    # 获取文件夹中的文件
    files_result = await db.execute(
        select(MediaFile).where(MediaFile.folder_id == folder_id)
    )
    files = files_result.scalars().all()

    result_dict = folder.to_dict()
    result_dict['children'] = [child.to_dict() for child in folder.children]
    result_dict['files'] = [f.to_dict() for f in files]

    return result_dict


@router.put("/{folder_id}")
async def update_folder(
    folder_id: int,
    folder_data: FolderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """更新文件夹"""
    result = await db.execute(
        select(MediaFolder).where(MediaFolder.id == folder_id)
    )
    folder = result.scalar_one_or_none()

    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )

    if folder_data.name is not None:
        # 检查同名文件夹
        result = await db.execute(
            select(MediaFolder).where(
                MediaFolder.name == folder_data.name,
                MediaFolder.parent_id == folder.parent_id,
                MediaFolder.id != folder_id
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Folder with this name already exists"
            )
        folder.name = folder_data.name

    if folder_data.parent_id is not None:
        new_parent_id = folder_data.parent_id

        # 防止循环引用
        if new_parent_id:
            async def is_descendant(check_id: int, target_id: int) -> bool:
                result = await db.execute(
                    select(MediaFolder).options(
                        selectinload(MediaFolder.children))
                    .where(MediaFolder.id == check_id)
                )
                parent = result.scalar_one_or_none()
                if not parent:
                    return False
                if parent.id == target_id:
                    return True
                for child in parent.children:
                    if await is_descendant(child.id, target_id):
                        return True
                return False

            if new_parent_id == folder_id or await is_descendant(folder_id, new_parent_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot move folder into its own subfolder"
                )

        folder.parent_id = new_parent_id

    await db.commit()

    return {
        "message": "Folder updated successfully",
        "folder": folder.to_dict()
    }


@router.delete("/{folder_id}")
async def delete_folder(
    folder_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """删除文件夹"""
    result = await db.execute(
        select(MediaFolder).options(selectinload(MediaFolder.children))
        .where(MediaFolder.id == folder_id)
    )
    folder = result.scalar_one_or_none()

    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )

    # 检查是否有子文件夹
    if folder.children:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete folder with subfolders"
        )

    # 检查是否有文件
    files_result = await db.execute(
        select(MediaFile).where(MediaFile.folder_id == folder_id)
    )
    if files_result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete folder with files"
        )

    await db.delete(folder)
    await db.commit()

    return {"message": "Folder deleted successfully"}


@router.post("/{folder_id}/move-files")
async def move_files_to_folder(
    folder_id: int,
    move_data: MoveFilesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """将文件移动到文件夹"""
    if folder_id != 0:
        result = await db.execute(
            select(MediaFolder).where(MediaFolder.id == folder_id)
        )
        target_folder = result.scalar_one_or_none()

        if not target_folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target folder not found"
            )

    if not move_data.file_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="file_ids is required"
        )

    moved_count = 0
    for file_id in move_data.file_ids:
        result = await db.execute(
            select(MediaFile).where(MediaFile.id == file_id)
        )
        media_file = result.scalar_one_or_none()

        if media_file:
            media_file.folder_id = folder_id if folder_id != 0 else None
            moved_count += 1

    await db.commit()

    return {"message": f"Moved {moved_count} files successfully"}
