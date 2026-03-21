"""
媒体文件模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.models.base import Base, TimestampMixin


class MediaFile(Base, TimestampMixin):
    """媒体文件表"""

    __tablename__ = "media_files"

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # 文件信息
    file_name = Column(String(255), nullable=False, doc="文件名")
    file_type = Column(String(20), nullable=False, index=True, doc="类型: image/video/ppt")
    file_path = Column(String(500), nullable=False, doc="文件路径")
    file_size = Column(Integer, nullable=True, doc="文件大小（字节）")

    # 转换后文件（PPT 用）
    converted_path = Column(String(500), nullable=True, doc="转换后视频路径")
    thumbnail_path = Column(String(500), nullable=True, doc="缩略图路径")

    # 校验信息
    md5_hash = Column(String(32), nullable=True, index=True, doc="MD5 哈希值")

    # 状态
    status = Column(
        String(20),
        default='ready',
        index=True,
        doc="状态: ready/processing/failed"
    )

    # 视频时长（秒）
    duration = Column(Integer, nullable=True, doc="视频时长（秒）")

    # PPT 幻灯片间隔时长（秒）
    slide_duration = Column(Integer, nullable=True, default=5, doc="PPT 幻灯片间隔时长（秒）")

    def __repr__(self) -> str:
        return f"<MediaFile(id={self.id}, name='{self.file_name}', type='{self.file_type}')>"
