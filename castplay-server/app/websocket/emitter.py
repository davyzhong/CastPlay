"""
WebSocket Event Emitter

提供统一的 WebSocket 事件发送接口
"""
import logging
from typing import Any, Dict, Optional

from app import socketio

logger = logging.getLogger(__name__)


def emit_playlist_update(playlist_id: int, device_id: Optional[int] = None) -> None:
    """
    发送播放列表更新事件

    Args:
        playlist_id: 播放列表 ID
        device_id: 目标设备 ID（可选，不传则广播给所有设备）
    """
    try:
        room = f'device_{device_id}' if device_id else 'all_devices'

        socketio.emit(
            'playlist_update',
            {
                'type': 'playlist_update',
                'playlist_id': playlist_id,
                'action': 'refresh'
            },
            room=room
        )

        logger.info(
            f"Emitted playlist_update for playlist {playlist_id} to room {room}")

    except Exception as e:
        logger.error(f"Failed to emit playlist update: {e}")


def emit_device_status(device_id: int, status: str) -> None:
    """
    发送设备状态更新事件

    Args:
        device_id: 设备 ID
        status: 状态（online/offline/processing/error）
    """
    try:
        socketio.emit(
            'device_status',
            {
                'type': 'device_status',
                'device_id': device_id,
                'status': status
            },
            room=f'device_{device_id}'
        )

        logger.info(f"Emitted device_status {status} for device {device_id}")

    except Exception as e:
        logger.error(f"Failed to emit device status: {e}")


def emit_media_ready(media_id: int, media_type: str) -> None:
    """
    发送媒体文件就绪事件

    Args:
        media_id: 媒体文件 ID
        media_type: 媒体类型（image/video/ppt）
    """
    try:
        socketio.emit(
            'media_ready',
            {
                'type': 'media_ready',
                'media_id': media_id,
                'media_type': media_type
            },
            room='all_clients'
        )

        logger.info(f"Emitted media_ready for media {media_id} ({media_type})")

    except Exception as e:
        logger.error(f"Failed to emit media ready event: {e}")


def emit_schedule_update(device_id: int) -> None:
    """
    发送节目单更新事件

    Args:
        device_id: 设备 ID
    """
    try:
        socketio.emit(
            'schedule_update',
            {
                'type': 'schedule_update',
                'device_id': device_id,
                'action': 'reload'
            },
            room=f'device_{device_id}'
        )

        logger.info(f"Emitted schedule_update for device {device_id}")

    except Exception as e:
        logger.error(f"Failed to emit schedule update: {e}")
