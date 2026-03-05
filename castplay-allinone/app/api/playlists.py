"""
播放列表管理 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.playlist import Playlist, PlaylistItem, DevicePlaylist
from app.models.media import MediaFile
from app.schemas.playlist import (
    PlaylistCreate, PlaylistResponse, PlaylistUpdate,
    PlaylistListResponse, PlaylistDetailResponse,
    PlaylistItemCreate, PlaylistItemResponse,
    DevicePlaylistResponse, ReorderItemsRequest
)
from app.api.auth import get_current_user
from app.models.user import User
from app.utils.logger import logger

router = APIRouter()


@router.post("/", response_model=PlaylistResponse, status_code=status.HTTP_201_CREATED)
def create_playlist(
    playlist_data: PlaylistCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建播放列表

    - **name**: 播放列表名称
    - **description**: 描述（可选）
    """
    new_playlist = Playlist(
        name=playlist_data.name,
        description=playlist_data.description
    )
    db.add(new_playlist)
    db.commit()
    db.refresh(new_playlist)

    logger.info(f"Playlist created: {new_playlist.name}")
    return new_playlist


@router.get("/", response_model=PlaylistListResponse)
def list_playlists(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    获取播放列表列表

    - **skip**: 跳过数量（分页）
    - **limit**: 返回数量（分页）
    """
    query = db.query(Playlist)
    total = query.count()
    playlists = query.order_by(Playlist.id.desc()).offset(skip).limit(limit).all()

    pages = (total + limit - 1) // limit if total > 0 else 0

    return {
        "items": playlists,
        "total": total,
        "page": skip // limit + 1,
        "per_page": limit,
        "pages": pages
    }


@router.get("/{playlist_id}", response_model=PlaylistDetailResponse)
def get_playlist(playlist_id: int, db: Session = Depends(get_db)):
    """
    获取播放列表详情（包含媒体项和关联设备）
    """
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )

    # 获取播放列表项
    items_query = (
        db.query(
            PlaylistItem.id,
            PlaylistItem.media_id,
            MediaFile.file_name,
            MediaFile.file_type,
            PlaylistItem.display_order,
            PlaylistItem.display_duration,
            PlaylistItem.created_at
        )
        .join(MediaFile, PlaylistItem.media_id == MediaFile.id)
        .filter(PlaylistItem.playlist_id == playlist_id)
        .order_by(PlaylistItem.display_order)
        .all()
    )

    items = [
        PlaylistItemResponse(
            id=item.id,
            media_id=item.media_id,
            file_name=item.file_name,
            file_type=item.file_type,
            display_order=item.display_order,
            display_duration=item.display_duration,
            created_at=item.created_at
        )
        for item in items_query
    ]

    # 获取关联设备
    device_assignments = db.query(DevicePlaylist).filter(
        DevicePlaylist.playlist_id == playlist_id
    ).all()

    devices = [
        {
            "id": dp.device_id,
            "is_active": bool(dp.is_active),
            "assigned_at": dp.assigned_at
        }
        for dp in device_assignments
    ]

    return PlaylistDetailResponse(
        id=playlist.id,
        name=playlist.name,
        description=playlist.description,
        items=items,
        devices=devices,
        created_at=playlist.created_at,
        updated_at=playlist.updated_at
    )


@router.put("/{playlist_id}", response_model=PlaylistResponse)
def update_playlist(
    playlist_id: int,
    playlist_data: PlaylistUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新播放列表

    需要认证
    """
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )

    if playlist_data.name is not None:
        playlist.name = playlist_data.name
    if playlist_data.description is not None:
        playlist.description = playlist_data.description

    db.commit()
    db.refresh(playlist)

    logger.info(f"Playlist updated: {playlist.name}")
    return playlist


@router.delete("/{playlist_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_playlist(
    playlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除播放列表

    需要认证
    """
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )

    db.delete(playlist)
    db.commit()

    logger.info(f"Playlist deleted: {playlist.name}")
    return None


@router.post("/{playlist_id}/items", response_model=PlaylistItemResponse)
def add_playlist_item(
    playlist_id: int,
    item_data: PlaylistItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    添加媒体到播放列表

    - **media_id**: 媒体文件 ID
    - **display_duration**: 显示时长（秒）

    需要认证
    """
    # 检查播放列表是否存在
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )

    # 检查媒体文件是否存在
    media = db.query(MediaFile).filter(MediaFile.id == item_data.media_id).first()
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media file not found"
        )

    # 获取当前最大 display_order
    max_order = db.query(PlaylistItem.display_order).filter(
        PlaylistItem.playlist_id == playlist_id
    ).order_by(PlaylistItem.display_order.desc()).first()

    new_order = (max_order[0] + 1) if max_order else 0

    # 创建播放列表项
    new_item = PlaylistItem(
        playlist_id=playlist_id,
        media_id=item_data.media_id,
        display_order=new_order,
        display_duration=item_data.display_duration
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    logger.info(f"Item added to playlist {playlist_id}: media_id={item_data.media_id}")
    return PlaylistItemResponse(
        id=new_item.id,
        media_id=new_item.media_id,
        file_name=media.file_name,
        file_type=media.file_type,
        display_order=new_item.display_order,
        display_duration=new_item.display_duration,
        created_at=new_item.created_at
    )


@router.delete("/{playlist_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_playlist_item(
    playlist_id: int,
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    从播放列表移除媒体项

    需要认证
    """
    item = db.query(PlaylistItem).filter(
        PlaylistItem.id == item_id,
        PlaylistItem.playlist_id == playlist_id
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist item not found"
        )

    db.delete(item)
    db.commit()

    logger.info(f"Item removed from playlist {playlist_id}: item_id={item_id}")
    return None


@router.put("/{playlist_id}/items/reorder")
def reorder_playlist_items(
    playlist_id: int,
    reorder_data: ReorderItemsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    重新排序播放列表项

    需要认证

    请求格式：
    {
        "items": [
            {"id": 1, "order": 0},
            {"id": 2, "order": 1}
        ]
    }
    """
    # 检查播放列表是否存在
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )

    # 更新顺序
    for item_data in reorder_data.items:
        item = db.query(PlaylistItem).filter(
            PlaylistItem.id == item_data["id"],
            PlaylistItem.playlist_id == playlist_id
        ).first()

        if item:
            item.display_order = item_data["order"]

    db.commit()

    logger.info(f"Playlist {playlist_id} items reordered")
    return {"message": "Playlist items reordered successfully"}


@router.post("/{playlist_id}/devices/{device_id}", response_model=DevicePlaylistResponse)
async def assign_playlist_to_device(
    playlist_id: int,
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    分配播放列表到设备

    需要认证
    """
    # 检查播放列表是否存在
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )

    # 检查设备是否存在
    from app.models.device import Device
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    # 检查是否已分配
    existing = db.query(DevicePlaylist).filter(
        DevicePlaylist.device_id == device_id,
        DevicePlaylist.playlist_id == playlist_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Playlist already assigned to this device"
        )

    # 创建关联
    new_assignment = DevicePlaylist(
        device_id=device_id,
        playlist_id=playlist_id,
        is_active=1
    )
    db.add(new_assignment)
    db.commit()
    db.refresh(new_assignment)

    logger.info(f"Playlist {playlist_id} assigned to device {device_id}")

    # 发送 WebSocket 通知（播放列表更新）
    from app.services.notification import NotificationService
    await NotificationService.notify_playlist_update(device_id)

    return new_assignment


@router.delete("/{playlist_id}/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def unassign_playlist_from_device(
    playlist_id: int,
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    取消设备的播放列表分配

    需要认证
    """
    assignment = db.query(DevicePlaylist).filter(
        DevicePlaylist.device_id == device_id,
        DevicePlaylist.playlist_id == playlist_id
    ).first()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )

    db.delete(assignment)
    db.commit()

    logger.info(f"Playlist {playlist_id} unassigned from device {device_id}")
    return None


@router.put("/{playlist_id}/devices/{device_id}/activate")
def toggle_playlist_activation(
    playlist_id: int,
    device_id: int,
    is_active: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    激活/停用设备上的播放列表

    需要认证

    请求体：
    {
        "is_active": true
    }
    """
    assignment = db.query(DevicePlaylist).filter(
        DevicePlaylist.device_id == device_id,
        DevicePlaylist.playlist_id == playlist_id
    ).first()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )

    assignment.is_active = int(is_active)
    db.commit()

    logger.info(f"Playlist {playlist_id} on device {device_id} {'activated' if is_active else 'deactivated'}")
    return {"message": f"Playlist {'activated' if is_active else 'deactivated'}"}
