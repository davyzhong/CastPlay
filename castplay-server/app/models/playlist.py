"""
Playlist Models
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from app import db


class Playlist(db.Model):
    """播放列表模型"""
    __tablename__ = 'playlist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, index=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    items = db.relationship('PlaylistItem', back_populates='playlist',
                            cascade='all, delete-orphan', order_by='PlaylistItem.display_order')
    devices = db.relationship(
        'DevicePlaylist', back_populates='playlist', cascade='all, delete-orphan')

    def to_dict(self, include_items=False):
        """Convert to dictionary"""
        result = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'item_count': len(self.items)
        }

        if include_items:
            result['items'] = [item.to_dict() for item in self.items]

        return result

    def __repr__(self):
        return f'<Playlist {self.name}>'


class PlaylistItem(db.Model):
    """播放列表项"""
    __tablename__ = 'playlist_item'
    __table_args__ = (
        db.Index('ix_playlist_item_playlist_order',
                 'playlist_id', 'display_order'),
    )

    id = db.Column(db.Integer, primary_key=True)
    playlist_id = db.Column(db.Integer, db.ForeignKey(
        'playlist.id'), nullable=False, index=True)
    media_id = db.Column(db.Integer, db.ForeignKey(
        'media_file.id'), nullable=False, index=True)
    display_order = db.Column(db.Integer, nullable=False)
    display_duration = db.Column(db.Integer, default=5)  # 图片显示时长（秒）
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    playlist = db.relationship('Playlist', back_populates='items')
    media_file = db.relationship('MediaFile', back_populates='playlist_items')

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'playlist_id': self.playlist_id,
            'media_id': self.media_id,
            'media': self.media_file.to_dict() if self.media_file else None,
            'display_order': self.display_order,
            'display_duration': self.display_duration
        }

    def __repr__(self):
        return f'<PlaylistItem {self.playlist_id}:{self.media_id}>'


class DevicePlaylist(db.Model):
    """设备播放列表关联"""
    __tablename__ = 'device_playlist'
    __table_args__ = (
        db.UniqueConstraint('device_id', 'playlist_id',
                            name='_device_playlist_uc'),
        db.Index('ix_device_playlist_active', 'device_id', 'is_active'),
    )

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey(
        'device.id'), nullable=False, index=True)
    playlist_id = db.Column(db.Integer, db.ForeignKey(
        'playlist.id'), nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True, index=True)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    device = db.relationship('Device', back_populates='playlists')
    playlist = db.relationship('Playlist', back_populates='devices')

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'playlist_id': self.playlist_id,
            'is_active': self.is_active,
            'assigned_at': self.assigned_at.isoformat()
        }
