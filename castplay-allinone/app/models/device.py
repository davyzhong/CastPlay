"""
设备相关模型
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from typing import List, Optional
from app.models.base import Base, TimestampMixin


class Device(Base, TimestampMixin):
    """设备表"""

    __tablename__ = "devices"

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # 设备信息
    device_id = Column(String(50), unique=True, index=True,
                       nullable=False, doc="设备唯一标识（UUID）")
    device_name = Column(String(100), nullable=False, doc="设备名称")
    timezone = Column(String(50), default='Asia/Shanghai', doc="时区")

    # 网络标识
    mac_address = Column(String(17), unique=True, nullable=True,
                         index=True, doc="MAC 地址 (XX:XX:XX:XX:XX:XX)")
    ip_address = Column(String(45), nullable=True, doc="IP 地址（支持 IPv6）")
    registration_code = Column(
        String(20), unique=True, nullable=True, index=True, doc="注册码")

    # 设备状态
    is_disabled = Column(Boolean, default=False,
                         index=True, doc="是否禁用（禁用后只能播放默认内容）")
    last_online = Column(DateTime, nullable=True, doc="最后在线时间")
    status = Column(String(20), default='offline',
                    index=True, doc="在线状态: online/offline")

    # 设备标识
    api_key = Column(String(100), nullable=True, doc="API 密钥")
    hardware_id = Column(String(100), nullable=True, doc="硬件 ID")
    device_type = Column(String(50), default='web_browser',
                         doc="设备类型：android_tv | web_browser")

    # 播放状态（新增）
    current_playlist_id = Column(Integer, ForeignKey(
        'playlists.id'), nullable=True, doc="当前播放列表 ID")
    last_media_id = Column(Integer, ForeignKey(
        'media_files.id'), nullable=True, doc="最后播放的媒体 ID")

    # 元数据（JSON 格式，可选）
    device_metadata = Column(Text, nullable=True, doc="元数据（JSON 格式）")

    # 关系
    current_playlist = relationship(
        "Playlist", foreign_keys=[current_playlist_id])
    last_media = relationship("MediaFile", foreign_keys=[last_media_id])
    schedules = relationship(
        "DeviceSchedule", back_populates="device", cascade="all, delete-orphan")
    cached_media = relationship(
        "CachedMedia", back_populates="device", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Device(id={self.id}, device_id='{self.device_id}', name='{self.device_name}', disabled={self.is_disabled})>"


class DeviceSchedule(Base, TimestampMixin):
    """设备定时配置表"""

    __tablename__ = "device_schedules"

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)

    # 关联设备
    device_id = Column(
        Integer,
        ForeignKey('devices.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        doc="设备 ID"
    )

    # 定时配置
    power_on_time = Column(String(10), nullable=True, doc="开机时间 HH:MM")
    power_off_time = Column(String(10), nullable=True, doc="关机时间 HH:MM")
    is_enabled = Column(Boolean, default=False, doc="是否启用")

    # 工作日（JSON 数组）- 存储为 JSON 类型，值为 1-7 代表周一到周日
    weekdays = Column(JSON, default=list, doc="工作日: [1,2,3,4,5] 代表周一到周五")

    # 关系
    device = relationship("Device", back_populates="schedules")

    def get_weekdays_list(self) -> List[int]:
        """获取工作日列表"""
        if self.weekdays is None:
            return []
        return self.weekdays if isinstance(self.weekdays, list) else []

    def set_weekdays_list(self, days: Optional[List[int]]):
        """设置工作日列表"""
        self.weekdays = days or []

    def __repr__(self) -> str:
        return f"<DeviceSchedule(id={self.id}, device_id={self.device_id})>"


class CachedMedia(Base, TimestampMixin):
    """设备缓存的媒体文件"""

    __tablename__ = "cached_media"

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)

    # 关联
    device_id = Column(
        Integer,
        ForeignKey('devices.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        doc="设备 ID"
    )
    media_id = Column(
        Integer,
        ForeignKey('media_files.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        doc="媒体文件 ID"
    )

    # 缓存信息
    local_path = Column(String(500), nullable=True, doc="设备本地路径")
    md5_hash = Column(String(32), nullable=True, doc="用于校验")
    file_size = Column(Integer, nullable=True, doc="文件大小（字节）")
    download_status = Column(
        String(20),
        default='pending',
        doc="下载状态: pending/downloading/completed/failed"
    )

    # 关系
    device = relationship("Device", back_populates="cached_media")

    def __repr__(self) -> str:
        return f"<CachedMedia(id={self.id}, device_id={self.device_id}, media_id={self.media_id})>"
