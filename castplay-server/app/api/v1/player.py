"""
Player API Routes - Android 播放端专用接口 (FastAPI 版本)
"""
import os
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from app.database import get_db
from app.core.config import settings
from app.models.device import Device
from app.models.playlist import Playlist
from app.models.media import MediaFile

logger = logging.getLogger(__name__)
router = APIRouter()


# ============= Pydantic 模型 =============

class PlayerInitRequest(BaseModel):
    device_id: str


class StatusRequest(BaseModel):
    device_id: str
    status: str = "online"


class PlaylistCheckRequest(BaseModel):
    version: str


# ============= 辅助函数 =============

def resolve_file_path(path: str) -> str:
    """安全解析文件路径"""
    abs_path = os.path.abspath(path)
    storage_path = os.path.abspath(settings.STORAGE_PATH)

    if not abs_path.startswith(storage_path):
        raise ValueError(f"Path outside storage directory: {path}")

    return abs_path


# ============= API 端点 =============

@router.post("/init")
async def player_init(
    request: PlayerInitRequest,
    db: AsyncSession = Depends(get_db)
):
    """播放端初始化"""
    # 查询设备及关联数据
    query = select(Device).options(
        selectinload(Device.schedule),
        selectinload(Device.playlists)
    ).where(Device.device_id == request.device_id)

    result = await db.execute(query)
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not registered"
        )

    # 更新设备状态
    device.last_online = datetime.utcnow()
    device.status = 'online'

    # 获取设备的播放列表
    active_playlists = []
    for dp in device.playlists:
        if dp.is_active:
            # 加载播放列表详情
            playlist_result = await db.execute(
                select(Playlist).options(
                    selectinload(Playlist.items)
                ).where(Playlist.id == dp.playlist_id)
            )
            playlist = playlist_result.scalar_one_or_none()

            if not playlist:
                continue

            playlist_data = {
                'id': dp.playlist_id,
                'name': playlist.name,
                'version': playlist.updated_at.isoformat() if playlist.updated_at else playlist.created_at.isoformat(),
                'items': []
            }

            for item in playlist.items:
                # 加载媒体文件
                media_result = await db.execute(
                    select(MediaFile).where(MediaFile.id == item.media_id)
                )
                media = media_result.scalar_one_or_none()

                if not media:
                    continue

                # 确定文件URL
                if media.file_type == 'ppt' and media.converted_path:
                    file_url = f"/api/player/media/{media.id}/converted"
                else:
                    file_url = f"/api/player/media/{media.id}/download"

                playlist_data['items'].append({
                    'id': item.id,
                    'media_id': media.id,
                    'file_name': media.file_name,
                    'file_type': media.file_type,
                    'file_url': file_url,
                    'display_order': item.display_order,
                    'display_duration': item.display_duration,
                    'file_size': media.file_size,
                    'md5_hash': media.md5_hash
                })

            active_playlists.append(playlist_data)

    # 获取定时配置
    schedule = None
    if device.schedule and device.schedule.is_enabled:
        schedule = {
            'power_on_time': device.schedule.power_on_time.isoformat() if device.schedule.power_on_time else None,
            'power_off_time': device.schedule.power_off_time.isoformat() if device.schedule.power_off_time else None,
            'weekdays': [int(d) for d in device.schedule.weekdays.split(',')],
            'timezone': device.timezone
        }

    await db.commit()

    return {
        'device': {
            'id': device.id,
            'device_id': device.device_id,
            'device_name': device.device_name,
            'timezone': device.timezone
        },
        'playlists': active_playlists,
        'schedule': schedule,
        'websocket_url': f'ws://localhost:{settings.PORT}'
    }


@router.post("/playlist/{playlist_id}/check")
async def check_playlist_version(
    playlist_id: int,
    request: PlaylistCheckRequest,
    db: AsyncSession = Depends(get_db)
):
    """检查播放列表版本"""
    result = await db.execute(select(Playlist).where(Playlist.id == playlist_id))
    playlist = result.scalar_one_or_none()

    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )

    server_version = playlist.updated_at.isoformat(
    ) if playlist.updated_at else playlist.created_at.isoformat()
    needs_update = request.version != server_version

    return {
        'needs_update': needs_update,
        'server_version': server_version,
        'local_version': request.version
    }


@router.get("/media/{media_id}/download")
async def download_media_for_player(
    media_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取媒体文件（原始文件）"""
    result = await db.execute(select(MediaFile).where(MediaFile.id == media_id))
    media = result.scalar_one_or_none()

    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found"
        )

    try:
        file_path = resolve_file_path(media.file_path)
    except ValueError as e:
        logger.error(f"Path security error: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    if not os.path.exists(file_path):
        logger.error(f'File not found: {file_path}')
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # 根据文件类型设置正确的MIME类型
    mime_types = {
        'image': 'image/jpeg',
        'video': 'video/mp4',
        'ppt': 'application/vnd.ms-powerpoint'
    }

    return FileResponse(
        file_path,
        media_type=mime_types.get(media.file_type, 'application/octet-stream')
    )


@router.get("/media/{media_id}/converted")
async def download_converted_media(
    media_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取转换后的媒体文件（PPT转视频）"""
    result = await db.execute(select(MediaFile).where(MediaFile.id == media_id))
    media = result.scalar_one_or_none()

    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found"
        )

    if not media.converted_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Converted file not found"
        )

    try:
        converted_path = resolve_file_path(media.converted_path)
    except ValueError as e:
        logger.error(f"Path security error: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    if not os.path.exists(converted_path):
        logger.error(f'Converted file not found: {converted_path}')
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Converted file not found"
        )

    return FileResponse(converted_path, media_type='video/mp4')


@router.post("/status")
async def report_player_status(
    request: StatusRequest,
    db: AsyncSession = Depends(get_db)
):
    """播放端上报状态"""
    result = await db.execute(
        select(Device).where(Device.device_id == request.device_id)
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    device.last_online = datetime.utcnow()
    device.status = request.status
    await db.commit()

    return {"message": "Status reported successfully"}


@router.get("/debug/media/{media_id}")
async def debug_media_path(
    media_id: int,
    db: AsyncSession = Depends(get_db)
):
    """调试：检查媒体文件路径 (仅 DEBUG 模式)"""
    if not settings.DEBUG:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Debug endpoint disabled in production"
        )

    result = await db.execute(select(MediaFile).where(MediaFile.id == media_id))
    media = result.scalar_one_or_none()

    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found"
        )

    try:
        resolved_path = resolve_file_path(media.file_path)
        file_exists = os.path.exists(resolved_path)
    except ValueError as e:
        resolved_path = f'BLOCKED: {e}'
        file_exists = False

    result_dict = {
        'id': media.id,
        'file_name': media.file_name,
        'file_type': media.file_type,
        'status': media.status,
        'file_path': media.file_path,
        'resolved_file_path': resolved_path,
        'file_exists': file_exists,
    }

    if media.converted_path:
        try:
            conv_resolved = resolve_file_path(media.converted_path)
            conv_exists = os.path.exists(conv_resolved)
        except ValueError as e:
            conv_resolved = f'BLOCKED: {e}'
            conv_exists = False

        result_dict['converted_path'] = media.converted_path
        result_dict['resolved_converted_path'] = conv_resolved
        result_dict['converted_exists'] = conv_exists

    return result_dict
