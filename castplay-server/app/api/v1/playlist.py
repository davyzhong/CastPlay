"""
Playlist API Routes (FastAPI 版本)
"""
import logging
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field

from app.database import get_db
from app.api.deps import get_current_user
from app.models.playlist import Playlist, PlaylistItem, DevicePlaylist
from app.models.media import MediaFile
from app.models.device import Device

logger = logging.getLogger(__name__)
router = APIRouter()

DEFAULT_PAGE_SIZE = 20
DEFAULT_IMAGE_DISPLAY_DURATION = 10


# ============= Pydantic 模型 =============

class PlaylistCreate(BaseModel):
    name: str = Field(..., max_length=128)
    description: Optional[str] = ""


class PlaylistUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=128)
    description: Optional[str] = None


class PlaylistItemCreate(BaseModel):
    media_id: int
    display_duration: Optional[int] = DEFAULT_IMAGE_DISPLAY_DURATION


class ItemReorder(BaseModel):
    id: int
    order: int


class ReorderRequest(BaseModel):
    items: List[ItemReorder]


class ActivateRequest(BaseModel):
    is_active: bool = True


# ============= API 端点 =============

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_playlist(
    playlist_data: PlaylistCreate,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """创建播放列表"""
    playlist = Playlist(
        name=playlist_data.name,
        description=playlist_data.description or ""
    )

    db.add(playlist)
    await db.commit()
    await db.refresh(playlist)

    return {
        "message": "Playlist created successfully",
        "playlist": playlist.to_dict()
    }


@router.get("")
async def list_playlists(
    page: int = Query(1, ge=1),
    per_page: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """播放列表列表"""
    # 获取总数
    count_result = await db.execute(select(func.count(Playlist.id)))
    total = count_result.scalar()

    # 分页查询
    query = select(Playlist).order_by(Playlist.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    playlists = result.scalars().all()

    pages = (total + per_page - 1) // per_page

    return {
        "playlists": [p.to_dict() for p in playlists],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages
    }


@router.get("/{playlist_id}")
async def get_playlist(
    playlist_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """获取播放列表详情"""
    query = select(Playlist).options(
        selectinload(Playlist.items).selectinload(PlaylistItem.media_file),
        selectinload(Playlist.devices).selectinload(DevicePlaylist.device)
    ).where(Playlist.id == playlist_id)

    result = await db.execute(query)
    playlist = result.scalar_one_or_none()

    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )

    result_dict = playlist.to_dict()

    # 包含播放列表项
    result_dict['items'] = []
    for item in playlist.items:
        media_file = item.media_file
        if media_file:
            if media_file.file_type == 'ppt' and media_file.converted_path and media_file.status == 'ready':
                file_url = f'/api/player/media/{media_file.id}/converted'
            else:
                file_url = f'/api/media/{media_file.id}/download'

            result_dict['items'].append({
                'id': item.id,
                'media_id': item.media_id,
                'media_name': media_file.file_name,
                'media_type': media_file.file_type,
                'display_order': item.display_order,
                'display_duration': item.display_duration,
                'status': media_file.status,
                'file_url': file_url,
                'media': {
                    'id': media_file.id,
                    'file_name': media_file.file_name,
                    'file_type': media_file.file_type,
                    'file_size': media_file.file_size,
                    'status': media_file.status,
                    'thumbnail_path': f'/api/media/{media_file.id}/thumbnail' if media_file.thumbnail_path else None,
                }
            })
        else:
            result_dict['items'].append({
                'id': item.id,
                'media_id': item.media_id,
                'media_name': f'[已删除] ID:{item.media_id}',
                'media_type': 'unknown',
                'display_order': item.display_order,
                'display_duration': item.display_duration,
                'media': None
            })

    # 包含关联的设备
    result_dict['devices'] = [
        {
            'device_id': dp.device_id,
            'device_name': dp.device.device_name if dp.device else None,
            'is_active': dp.is_active
        }
        for dp in playlist.devices
    ]

    return result_dict


@router.put("/{playlist_id}")
async def update_playlist(
    playlist_id: int,
    playlist_data: PlaylistUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """更新播放列表"""
    result = await db.execute(select(Playlist).where(Playlist.id == playlist_id))
    playlist = result.scalar_one_or_none()

    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )

    if playlist_data.name is not None:
        playlist.name = playlist_data.name
    if playlist_data.description is not None:
        playlist.description = playlist_data.description

    playlist.updated_at = datetime.utcnow()
    await db.commit()

    return {
        "message": "Playlist updated successfully",
        "playlist": playlist.to_dict()
    }


@router.delete("/{playlist_id}")
async def delete_playlist(
    playlist_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """删除播放列表"""
    result = await db.execute(select(Playlist).where(Playlist.id == playlist_id))
    playlist = result.scalar_one_or_none()

    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )

    await db.delete(playlist)
    await db.commit()

    return {"message": "Playlist deleted successfully"}


@router.post("/{playlist_id}/items", status_code=status.HTTP_201_CREATED)
async def add_media_to_playlist(
    playlist_id: int,
    item_data: PlaylistItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """添加媒体到播放列表"""
    # 检查播放列表
    result = await db.execute(select(Playlist).where(Playlist.id == playlist_id))
    playlist = result.scalar_one_or_none()

    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )

    # 检查媒体
    result = await db.execute(select(MediaFile).where(MediaFile.id == item_data.media_id))
    media = result.scalar_one_or_none()

    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found"
        )

    # 获取当前最大顺序号
    max_order_result = await db.execute(
        select(func.max(PlaylistItem.display_order))
        .where(PlaylistItem.playlist_id == playlist_id)
    )
    max_order = max_order_result.scalar() or 0

    playlist_item = PlaylistItem(
        playlist_id=playlist_id,
        media_id=item_data.media_id,
        display_order=max_order + 1,
        display_duration=item_data.display_duration
    )

    db.add(playlist_item)
    await db.commit()
    await db.refresh(playlist_item)

    return {
        "message": "Media added to playlist successfully",
        "item": playlist_item.to_dict()
    }


@router.delete("/{playlist_id}/items/{item_id}")
async def remove_media_from_playlist(
    playlist_id: int,
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """从播放列表移除媒体"""
    result = await db.execute(
        select(PlaylistItem).where(
            PlaylistItem.id == item_id,
            PlaylistItem.playlist_id == playlist_id
        )
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )

    await db.delete(item)
    await db.commit()

    return {"message": "Media removed from playlist successfully"}


@router.put("/{playlist_id}/items/reorder")
async def reorder_playlist_items(
    playlist_id: int,
    reorder_data: ReorderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """重新排序播放列表项"""
    # 检查播放列表
    result = await db.execute(select(Playlist).where(Playlist.id == playlist_id))
    playlist = result.scalar_one_or_none()

    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )

    for item_order in reorder_data.items:
        result = await db.execute(
            select(PlaylistItem).where(PlaylistItem.id == item_order.id)
        )
        item = result.scalar_one_or_none()
        if item and item.playlist_id == playlist_id:
            item.display_order = item_order.order

    await db.commit()

    return {"message": "Playlist items reordered successfully"}


@router.post("/{playlist_id}/devices/{device_id}", status_code=status.HTTP_201_CREATED)
async def assign_playlist_to_device(
    playlist_id: int,
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """分配播放列表到设备"""
    # 检查播放列表
    result = await db.execute(select(Playlist).where(Playlist.id == playlist_id))
    playlist = result.scalar_one_or_none()

    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )

    # 检查设备
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    # 检查是否已分配
    result = await db.execute(
        select(DevicePlaylist).where(
            DevicePlaylist.device_id == device_id,
            DevicePlaylist.playlist_id == playlist_id
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        return {"message": "Playlist already assigned to device"}

    device_playlist = DevicePlaylist(
        device_id=device_id,
        playlist_id=playlist_id,
        is_active=True
    )

    db.add(device_playlist)
    await db.commit()
    await db.refresh(device_playlist)

    # TODO: 触发 WebSocket 推送

    return {
        "message": "Playlist assigned to device successfully",
        "assignment": device_playlist.to_dict()
    }


@router.delete("/{playlist_id}/devices/{device_id}")
async def unassign_playlist_from_device(
    playlist_id: int,
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """取消分配播放列表"""
    result = await db.execute(
        select(DevicePlaylist).where(
            DevicePlaylist.device_id == device_id,
            DevicePlaylist.playlist_id == playlist_id
        )
    )
    device_playlist = result.scalar_one_or_none()

    if not device_playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )

    await db.delete(device_playlist)
    await db.commit()

    return {"message": "Playlist unassigned from device successfully"}


@router.put("/{playlist_id}/devices/{device_id}/activate")
async def activate_playlist(
    playlist_id: int,
    device_id: int,
    activate_data: ActivateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """激活/停用播放列表"""
    result = await db.execute(
        select(DevicePlaylist).where(
            DevicePlaylist.device_id == device_id,
            DevicePlaylist.playlist_id == playlist_id
        )
    )
    device_playlist = result.scalar_one_or_none()

    if not device_playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )

    device_playlist.is_active = activate_data.is_active
    await db.commit()

    action = "activated" if activate_data.is_active else "deactivated"
    return {"message": f"Playlist {action} successfully"}
