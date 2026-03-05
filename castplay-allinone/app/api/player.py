"""
播放端 API 路由
供 Android 播放端使用的专用 API
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.database import get_db
from app.models.device import Device, DeviceSchedule
from app.models.playlist import Playlist, PlaylistItem, DevicePlaylist
from app.models.media import MediaFile
from app.utils.logger import logger

router = APIRouter()


@router.post("/init")
def player_init(
    device_id: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """
    播放端初始化

    返回设备信息、激活的播放列表、定时配置和 WebSocket URL

    请求：
    {
        "device_id": "550e8400-e29b-41d4-a716-446655440000"
    }

    响应：
    {
        "device": {...},
        "playlists": [...],
        "schedule": {...},
        "websocket_url": "ws://localhost:5000/ws/{device_id}"
    }
    """
    # 查找设备
    device = db.query(Device).filter(Device.device_id == device_id).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not registered. Please register first."
        )

    # 更新最后在线时间
    device.last_online = datetime.utcnow()
    device.status = "online"
    db.commit()

    # 获取定时配置
    schedule = db.query(DeviceSchedule).filter(
        DeviceSchedule.device_id == device.id
    ).first()

    schedule_data = None
    if schedule:
        schedule_data = {
            "power_on_time": schedule.power_on_time,
            "power_off_time": schedule.power_off_time,
            "is_enabled": schedule.is_enabled,
            "weekdays": schedule.get_weekdays_list(),
            "timezone": device.timezone
        }

    # 获取激活的播放列表
    playlist_assignments = db.query(DevicePlaylist).filter(
        DevicePlaylist.device_id == device.id,
        DevicePlaylist.is_active == True
    ).all()

    playlists_data = []
    for assignment in playlist_assignments:
        playlist = db.query(Playlist).filter(Playlist.id == assignment.playlist_id).first()
        if not playlist:
            continue

        # 获取播放列表项
        items_query = (
            db.query(
                PlaylistItem.id,
                PlaylistItem.media_id,
                MediaFile.file_name,
                MediaFile.file_type,
                MediaFile.file_path,
                MediaFile.converted_path,
                MediaFile.file_size,
                MediaFile.md5_hash,
                PlaylistItem.display_order,
                PlaylistItem.display_duration
            )
            .join(MediaFile, PlaylistItem.media_id == MediaFile.id)
            .filter(PlaylistItem.playlist_id == playlist.id)
            .order_by(PlaylistItem.display_order)
            .all()
        )

        items = [
            {
                "id": item.id,
                "media_id": item.media_id,
                "file_name": item.file_name,
                "file_type": item.file_type,
                "file_url": f"/api/player/media/{item.media_id}/download",
                "display_order": item.display_order,
                "display_duration": item.display_duration,
                "file_size": item.file_size,
                "md5_hash": item.md5_hash
            }
            for item in items_query
        ]

        playlists_data.append({
            "id": playlist.id,
            "name": playlist.name,
            "version": playlist.updated_at.isoformat(),
            "items": items
        })

    logger.info(f"Player initialized for device {device_id} ({device.device_name})")

    return {
        "device": {
            "id": device.id,
            "device_id": device.device_id,
            "device_name": device.device_name,
            "timezone": device.timezone,
            "mac_address": device.mac_address,
            "ip_address": device.ip_address,
            "registration_code": device.registration_code,
            "playback_speed": device.playback_speed
        },
        "playlists": playlists_data,
        "schedule": schedule_data,
        "websocket_url": f"ws://{device.device_id}"  # 暂时占位
    }


@router.post("/playlist/{playlist_id}/check")
def check_playlist_version(
    playlist_id: int,
    version: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """
    检查播放列表版本

    用于判断是否需要更新

    请求：
    {
        "version": "2026-01-29T10:00:00"
    }

    响应：
    {
        "needs_update": true,
        "server_version": "2026-01-29T11:00:00",
        "local_version": "2026-01-29T10:00:00"
    }
    """
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )

    server_version = playlist.updated_at.isoformat()
    needs_update = server_version > version

    return {
        "needs_update": needs_update,
        "server_version": server_version,
        "local_version": version
    }


@router.get("/media/{media_id}/download")
def download_media(media_id: int, db: Session = Depends(get_db)):
    """
    下载媒体文件（用于播放端）

    如果是 PPT 且已转换，返回转换后的视频
    否则返回原始文件
    """
    from fastapi.responses import FileResponse
    import os

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


@router.get("/media/{media_id}/converted")
def download_converted_media(media_id: int, db: Session = Depends(get_db)):
    """
    下载转换后的文件（仅用于 PPT）

    返回 PPT 转换后的视频文件
    """
    from fastapi.responses import FileResponse
    import os

    media = db.query(MediaFile).filter(MediaFile.id == media_id).first()
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media file not found"
        )

    if not media.converted_path or not os.path.exists(media.converted_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Converted file not found"
        )

    return FileResponse(
        media.converted_path,
        filename=f"{os.path.splitext(media.file_name)[0]}.mp4",
        media_type="video/mp4"
    )


@router.post("/status")
def report_player_status(
    device_id: str = Body(..., embed=True),
    player_status: str = Body("playing", embed=True),
    db: Session = Depends(get_db)
):
    """
    上报播放状态

    用于播放端定期上报当前播放状态

    请求：
    {
        "device_id": "550e8400-e29b-41d4-a716-446655440000",
        "status": "playing"
    }
    """
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    # 更新最后在线时间
    device.last_online = datetime.utcnow()
    device.status = "online"
    db.commit()

    return {"message": "Status reported successfully"}
