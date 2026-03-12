"""
播放列表相关模型
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin


class Playlist(Base, TimestampMixin):
    """播放列表表"""

    __tablename__ = "playlists"

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # 播放列表信息
    name = Column(String(200), nullable=False, doc="播放列表名称")
    description = Column(Text, nullable=True, doc="描述")

    # 系统播放列表（新增）
    is_system = Column(Boolean, default=False, doc="是否系统默认播放列表")
    version = Column(String(50), nullable=True, doc="版本号（用于增量更新）")

    # 关系
    items = relationship(
        "PlaylistItem",
        back_populates="playlist",
        cascade="all, delete-orphan",
        order_by="PlaylistItem.display_order"
    )
    device_assignments = relationship(
        "DevicePlaylist",
        back_populates="playlist",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Playlist(id={self.id}, name='{self.name}')>"


class PlaylistItem(Base, TimestampMixin):
    """播放列表项表"""

    __tablename__ = "playlist_items"

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)

    # 关联
    playlist_id = Column(
        Integer,
        ForeignKey('playlists.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        doc="播放列表 ID"
    )
    media_id = Column(
        Integer,
        ForeignKey('media_files.id', ondelete='CASCADE'),
        nullable=False,
        doc="媒体文件 ID"
    )

    # 排序和时长
    display_order = Column(Integer, nullable=False, doc="显示顺序")
    display_duration = Column(Integer, default=5, doc="显示时长（秒）")

    # 关系
    playlist = relationship("Playlist", back_populates="items")

    def __repr__(self) -> str:
        return f"<PlaylistItem(id={self.id}, playlist_id={self.playlist_id}, order={self.display_order})>"


class DevicePlaylist(Base, TimestampMixin):
    """设备播放列表关联表"""

    __tablename__ = "device_playlists"

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
    playlist_id = Column(
        Integer,
        ForeignKey('playlists.id', ondelete='CASCADE'),
        nullable=False,
        doc="播放列表 ID"
    )

    # 激活状态
    is_active = Column(Boolean, default=True, doc="是否激活")

    # 关系
    playlist = relationship("Playlist", back_populates="device_assignments")

    def __repr__(self) -> str:
        return f"<DevicePlaylist(id={self.id}, device_id={self.device_id}, playlist_id={self.playlist_id})>"
