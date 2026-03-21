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
    PlaylistItemCreate, PlaylistItemResponse, PlaylistItemUpdate,
    DevicePlaylistResponse, ReorderItemsRequest,
    PlaylistItemBatchCreate, PlaylistItemBatchResponse
)
from app.api.auth import get_current_user
from app.models.user import User
from app.utils.logger import logger

router = APIRouter(
    tags=["播放列表"],
    responses={
        404: {"description": "播放列表未找到"},
    }
)


@router.post(
    "/",
    response_model=PlaylistResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建播放列表",
    description="""
创建新的播放列表。

**请求体：**
- `name` (必需): 播放列表名称
- `description` (可选): 播放列表描述

**认证：** 需要 Bearer Token
"""
)
def create_playlist(
    playlist_data: PlaylistCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_playlist = Playlist(
        name=playlist_data.name,
        description=playlist_data.description
    )
    db.add(new_playlist)
    db.commit()
    db.refresh(new_playlist)

    logger.info(f"Playlist created: {new_playlist.name}")
    return new_playlist


@router.get(
    "/",
    response_model=PlaylistListResponse,
    summary="获取播放列表列表",
    description="""
获取所有播放列表，包含媒体项数量和关联设备数量。

**查询参数：**
- `skip`: 跳过数量，默认 0
- `limit`: 返回数量，默认 20，最大 100

**返回信息包含：**
- 播放列表基本信息
- 媒体项数量 (item_count)
- 关联设备数量 (device_count)
"""
)
def list_playlists(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    from sqlalchemy import func

    query = db.query(Playlist)
    total = query.count()
    playlists = query.order_by(Playlist.id.desc()).offset(skip).limit(limit).all()

    # 获取每个播放列表的媒体数量
    playlist_ids = [p.id for p in playlists]
    item_counts = dict(
        db.query(PlaylistItem.playlist_id, func.count(PlaylistItem.id))
        .filter(PlaylistItem.playlist_id.in_(playlist_ids))
        .group_by(PlaylistItem.playlist_id)
        .all()
    ) if playlist_ids else {}

    # 获取每个播放列表的设备数量
    device_counts = dict(
        db.query(DevicePlaylist.playlist_id, func.count(DevicePlaylist.id))
        .filter(DevicePlaylist.playlist_id.in_(playlist_ids))
        .group_by(DevicePlaylist.playlist_id)
        .all()
    ) if playlist_ids else {}

    # 构建响应，包含 item_count 和 device_count
    playlist_responses = [
        PlaylistResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            is_system=p.is_system,
            item_count=item_counts.get(p.id, 0),
            device_count=device_counts.get(p.id, 0),
            created_at=p.created_at,
            updated_at=p.updated_at
        )
        for p in playlists
    ]

    pages = (total + limit - 1) // limit if total > 0 else 0

    return {
        "items": playlist_responses,
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

    # 获取关联设备（包含设备名称和状态）
    from app.models.device import Device as DeviceModel

    device_assignments = (
        db.query(DevicePlaylist, DeviceModel)
        .join(DeviceModel, DevicePlaylist.device_id == DeviceModel.id)
        .filter(DevicePlaylist.playlist_id == playlist_id)
        .all()
    )

    devices = [
        {
            "id": dp.id,
            "device_id": dp.device_id,
            "device_name": device.device_name,
            "device_status": device.status,
            "is_active": bool(dp.is_active),
            "assigned_at": dp.created_at.isoformat() if dp.created_at else None
        }
        for dp, device in device_assignments
    ]

    return PlaylistDetailResponse(
        id=playlist.id,
        name=playlist.name,
        description=playlist.description,
        is_system=playlist.is_system,
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
    from app.models.playlist import DevicePlaylist
    from app.models.schedule import PlaylistSchedule

    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )

    # 检查是否有设备正在使用此播放列表
    device_count = db.query(DevicePlaylist).filter(
        DevicePlaylist.playlist_id == playlist_id,
        DevicePlaylist.is_active == True
    ).count()

    if device_count > 0:
        logger.warning(
            f"Attempting to delete playlist {playlist_id} with {device_count} active device assignments"
        )
        # 获取关联设备名称用于提示
        device_assignments = db.query(DevicePlaylist).filter(
            DevicePlaylist.playlist_id == playlist_id
        ).all()
        device_names = []
        for assignment in device_assignments:
            if assignment.device:
                device_names.append(assignment.device.device_name)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete playlist: {device_count} device(s) are using it ({', '.join(device_names[:5])}{' ...' if len(device_names) > 5 else ''})"
        )

    # 检查是否有活跃的调度使用此播放列表
    active_schedule_count = db.query(PlaylistSchedule).filter(
        PlaylistSchedule.playlist_id == playlist_id,
        PlaylistSchedule.enabled == True
    ).count()

    if active_schedule_count > 0:
        logger.warning(
            f"Attempting to delete playlist {playlist_id} with {active_schedule_count} active schedules"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete playlist: {active_schedule_count} active schedule(s) are using it. Please disable or delete the schedules first."
        )

    # 级联删除关联的调度（非启用的）
    db.query(PlaylistSchedule).filter(
        PlaylistSchedule.playlist_id == playlist_id
    ).delete()

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


@router.post("/{playlist_id}/items/batch/", response_model=PlaylistItemBatchResponse)
def add_playlist_items_batch(
    playlist_id: int,
    batch_data: PlaylistItemBatchCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    批量添加媒体到播放列表

    - **media_ids**: 媒体文件 ID 列表（最多 50 个）
    - **display_duration**: 默认显示时长（秒）

    需要认证
    """
    # 检查播放列表是否存在
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )

    # 获取当前最大 display_order
    max_order = db.query(PlaylistItem.display_order).filter(
        PlaylistItem.playlist_id == playlist_id
    ).order_by(PlaylistItem.display_order.desc()).first()

    next_order = (max_order[0] + 1) if max_order else 0

    # 批量查询媒体文件
    media_files = db.query(MediaFile).filter(
        MediaFile.id.in_(batch_data.media_ids)
    ).all()
    media_map = {m.id: m for m in media_files}

    added_items = []
    failed_media_ids = []

    # 添加媒体项
    for media_id in batch_data.media_ids:
        media = media_map.get(media_id)
        if not media:
            failed_media_ids.append(media_id)
            continue

        new_item = PlaylistItem(
            playlist_id=playlist_id,
            media_id=media_id,
            display_order=next_order,
            display_duration=batch_data.display_duration
        )
        db.add(new_item)
        db.flush()  # 获取 ID

        added_items.append(PlaylistItemResponse(
            id=new_item.id,
            media_id=new_item.media_id,
            file_name=media.file_name,
            file_type=media.file_type,
            display_order=new_item.display_order,
            display_duration=new_item.display_duration,
            created_at=new_item.created_at
        ))
        next_order += 1

    db.commit()

    logger.info(f"Batch added {len(added_items)} items to playlist {playlist_id}")
    return PlaylistItemBatchResponse(
        added_count=len(added_items),
        items=added_items,
        failed_media_ids=failed_media_ids
    )


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
            PlaylistItem.id == item_data.id,
            PlaylistItem.playlist_id == playlist_id
        ).first()

        if item:
            item.display_order = item_data.order

    db.commit()

    logger.info(f"Playlist {playlist_id} items reordered")
    return {"message": "Playlist items reordered successfully"}


@router.put("/{playlist_id}/items/{item_id}", response_model=PlaylistItemResponse)
def update_playlist_item(
    playlist_id: int,
    item_id: int,
    item_data: PlaylistItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新播放列表项的显示时长

    需要认证
    """
    # 检查播放列表是否存在
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )

    # 查找播放列表项
    item = db.query(PlaylistItem).filter(
        PlaylistItem.id == item_id,
        PlaylistItem.playlist_id == playlist_id
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist item not found"
        )

    # 获取关联的媒体文件信息
    media = db.query(MediaFile).filter(MediaFile.id == item.media_id).first()
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated media file not found"
        )

    # 更新显示时长
    item.display_duration = item_data.display_duration
    db.commit()
    db.refresh(item)

    logger.info(f"Playlist item updated: playlist_id={playlist_id}, item_id={item_id}, duration={item_data.display_duration}")

    return PlaylistItemResponse(
        id=item.id,
        media_id=item.media_id,
        file_name=media.file_name,
        file_type=media.file_type,
        display_order=item.display_order,
        display_duration=item.display_duration,
        created_at=item.created_at
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


@router.post("/{playlist_id}/devices/{device_id}", response_model=DevicePlaylistResponse, status_code=status.HTTP_201_CREATED)
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
    from app.services.notification import NotificationService

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

    # 获取播放列表媒体项数量和总大小
    from sqlalchemy import func
    item_count = db.query(func.count(PlaylistItem.id)).filter(
        PlaylistItem.playlist_id == playlist_id
    ).scalar() or 0

    # 创建关联
    new_assignment = DevicePlaylist(
        device_id=device_id,
        playlist_id=playlist_id,
        is_active=True
    )
    db.add(new_assignment)
    db.commit()
    db.refresh(new_assignment)

    logger.info(f"Playlist {playlist_id} assigned to device {device_id}")

    # 发送 WebSocket 通知（播放列表已分配）
    # 设备 ID 使用 device.device_id (UUID)
    await NotificationService.notify_playlist_assigned(
        device_id=device.device_id,
        playlist_id=playlist_id,
        playlist_name=playlist.name,
        version=playlist.version or "1.0.0",
        item_count=item_count,
        total_size=0  # TODO: 计算实际总大小
    )

    return DevicePlaylistResponse.from_orm_with_assigned_at(new_assignment)


@router.delete("/{playlist_id}/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unassign_playlist_from_device(
    playlist_id: int,
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    取消设备的播放列表分配

    需要认证
    """
    from app.services.notification import NotificationService

    assignment = db.query(DevicePlaylist).filter(
        DevicePlaylist.device_id == device_id,
        DevicePlaylist.playlist_id == playlist_id
    ).first()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )

    # 获取设备信息（用于发送通知）
    from app.models.device import Device
    device = db.query(Device).filter(Device.id == device_id).first()

    db.delete(assignment)
    db.commit()

    logger.info(f"Playlist {playlist_id} unassigned from device {device_id}")

    # 发送 WebSocket 通知（播放列表已移除）
    if device:
        await NotificationService.notify_playlist_removed(
            device_id=device.device_id,
            playlist_id=playlist_id
        )

    return None


@router.put("/{playlist_id}/devices/{device_id}/activate")
async def toggle_playlist_activation(
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
    from app.services.notification import NotificationService

    assignment = db.query(DevicePlaylist).filter(
        DevicePlaylist.device_id == device_id,
        DevicePlaylist.playlist_id == playlist_id
    ).first()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )

    assignment.is_active = is_active
    db.commit()

    logger.info(f"Playlist {playlist_id} on device {device_id} {'activated' if is_active else 'deactivated'}")

    # 发送 WebSocket 通知（播放列表激活状态变更）
    from app.models.device import Device
    device = db.query(Device).filter(Device.id == device_id).first()
    if device:
        await NotificationService.notify_playlist_activated(
            device_id=device.device_id,
            playlist_id=playlist_id,
            is_active=is_active
        )

    return {"message": f"Playlist {'activated' if is_active else 'deactivated'}"}
