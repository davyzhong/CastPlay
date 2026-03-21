"""
数据模型模块
包含所有 SQLAlchemy ORM 模型
"""
from app.models.base import Base, TimestampMixin
from app.models.user import User
from app.models.device import Device, DeviceSchedule, CachedMedia
from app.models.media import MediaFile
from app.models.playlist import Playlist, PlaylistItem, DevicePlaylist
from app.models.alert import AlertConfig, AlertHistory
from app.models.device_enhancement import (
    DeviceNotificationLog,
    PlaylistDownloadTask,
    PlaylistCleanupSchedule,
)
from app.models.schedule import PlaylistSchedule, DayOfWeek

# 导出所有模型
__all__ = [
    "Base",
    "TimestampMixin",
    "User",
    "Device",
    "DeviceSchedule",
    "CachedMedia",
    "MediaFile",
    "Playlist",
    "PlaylistItem",
    "DevicePlaylist",
    "AlertConfig",
    "AlertHistory",
    "DeviceNotificationLog",
    "PlaylistDownloadTask",
    "PlaylistCleanupSchedule",
    "PlaylistSchedule",
    "DayOfWeek",
]
