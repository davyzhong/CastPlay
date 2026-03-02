"""Media File Model"""
from datetime import datetime
from typing import Dict, Any, Optional, List

from app import db


class MediaFolder(db.Model):
    """媒体文件夹模型"""
    __tablename__ = 'media_folder'

    # 添加表级索引
    __table_args__ = (
        db.Index('ix_media_folder_parent_name', 'parent_id', 'name'),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    parent_id = db.Column(db.Integer, db.ForeignKey(
        'media_folder.id'), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    parent = db.relationship('MediaFolder', remote_side=[
                             id], backref='children')
    media_files = db.relationship(
        'MediaFile', back_populates='folder', lazy='dynamic')

    def to_dict(self, include_children: bool = False) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            'id': self.id,
            'name': self.name,
            'parent_id': self.parent_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'file_count': self.media_files.count()
        }
        if include_children:
            result['children'] = [child.to_dict() for child in self.children]
        return result

    def __repr__(self) -> str:
        return f'<MediaFolder {self.name}>'


class MediaFile(db.Model):
    """媒体文件模型"""
    __tablename__ = 'media_file'

    # 添加表级索引，优化常用查询
    __table_args__ = (
        db.Index('ix_media_file_folder_type', 'folder_id', 'file_type'),
        db.Index('ix_media_file_status_upload', 'status', 'upload_time'),
    )

    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(255), nullable=False, index=True)
    file_type = db.Column(db.String(20), nullable=False,
                          index=True)  # image/video/ppt
    file_path = db.Column(db.String(512), nullable=False)
    converted_path = db.Column(db.String(512))  # PPT转视频后的路径
    file_size = db.Column(db.BigInteger)
    duration = db.Column(db.Integer)  # 视频时长（秒）
    thumbnail_path = db.Column(db.String(512))
    md5_hash = db.Column(db.String(32), index=True)  # 文件MD5哈希，用于去重
    upload_time = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    status = db.Column(db.String(20), default='processing',
                       index=True)  # processing/ready/failed
    folder_id = db.Column(db.Integer, db.ForeignKey(
        'media_folder.id'), nullable=True, index=True)

    # Relationships
    playlist_items = db.relationship(
        'PlaylistItem', back_populates='media_file', cascade='all, delete-orphan')
    folder = db.relationship('MediaFolder', back_populates='media_files')

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'file_name': self.file_name,
            'file_type': self.file_type,
            'file_path': self.file_path,
            'converted_path': self.converted_path,
            'file_size': self.file_size,
            'duration': self.duration,
            'thumbnail_path': self.thumbnail_path,
            'md5_hash': self.md5_hash,
            'upload_time': self.upload_time.isoformat(),
            'status': self.status,
            'folder_id': self.folder_id,
            'folder_name': self.folder.name if self.folder else None
        }

    def __repr__(self) -> str:
        return f'<MediaFile {self.file_name}>'
