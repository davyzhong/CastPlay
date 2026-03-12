"""
设备通知相关模型
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from typing import List, Optional
from app.models.base import Base, TimestampMixin
from datetime import datetime


class DeviceNotificationLog(Base, TimestampMixin):
    """设备通知日志表"""

    __tablename__ = "device_notification_logs"

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # 设备 ID
    device_id = Column(String(50), nullable=False, index=True, doc="设备唯一标识")

    # 通知类型
    notification_type = Column(
        String(50), nullable=False, index=True, doc="通知类型")

    # 播放列表 ID（可选）
    playlist_id = Column(
        Integer,
        ForeignKey('playlists.id'),
        nullable=True,
        index=True,  # P0-1 修复：添加索引
        doc="关联的播放列表 ID"
    )

    # 消息内容
    message = Column(Text, nullable=True, doc="错误消息或详细信息")

    # 创建时间
    created_at = Column(DateTime, default=datetime.utcnow,
                        index=True, doc="创建时间")  # P0-1 修复：添加索引

    def __repr__(self) -> str:
        return f"<DeviceNotificationLog(id={self.id}, device_id='{self.device_id}', type='{self.notification_type}')>"


class PlaylistDownloadTask(Base, TimestampMixin):
    """播放列表下载任务表"""

    __tablename__ = "playlist_download_tasks"

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # 设备 ID
    device_id = Column(String(50), nullable=False, index=True, doc="设备唯一标识")

    # 播放列表 ID
    playlist_id = Column(Integer, ForeignKey(
        'playlists.id'), nullable=False, doc="播放列表 ID")

    # 状态
    status = Column(String(20), nullable=False, default='pending', index=True,
                    doc="状态：pending/downloading/completed/failed")

    # 重试次数
    retry_count = Column(Integer, default=0, doc="重试次数")

    # 错误消息
    error_message = Column(Text, nullable=True, doc="错误消息")

    # 创建时间
    created_at = Column(DateTime, default=datetime.utcnow, doc="创建时间")

    # 完成时间
    completed_at = Column(DateTime, nullable=True, doc="完成时间")

    def __repr__(self) -> str:
        return f"<PlaylistDownloadTask(id={self.id}, device_id='{self.device_id}', status='{self.status}')>"


class PlaylistCleanupSchedule(Base, TimestampMixin):
    """播放列表清理计划表"""

    __tablename__ = "playlist_cleanup_schedule"

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # 播放列表 ID
    playlist_id = Column(Integer, ForeignKey(
        'playlists.id'), nullable=False, doc="播放列表 ID")

    # 计划清理时间
    scheduled_time = Column(DateTime, nullable=False,
                            index=True, doc="计划清理时间")  # P0-1 修复：添加索引

    # 是否已执行
    executed = Column(Boolean, default=False, doc="是否已执行")

    # 执行时间
    executed_at = Column(DateTime, nullable=True, doc="执行时间")

    def __repr__(self) -> str:
        return f"<PlaylistCleanupSchedule(id={self.id}, playlist_id={self.playlist_id}, scheduled={self.scheduled_time})>"
