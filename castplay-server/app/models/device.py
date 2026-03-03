"""
Device Model
"""
import secrets
from datetime import datetime
from typing import Optional, Dict, Any, List
from app import db


class Device(db.Model):
    """设备模型"""
    __tablename__ = 'device'
    __table_args__ = (
        db.Index('ix_device_status_online', 'status', 'last_online'),
    )

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(64), unique=True,
                          nullable=False, index=True)
    hardware_id = db.Column(db.String(128), unique=True,
                            index=True)  # Android ID 或其他硬件标识
    device_name = db.Column(db.String(128), index=True)
    api_key = db.Column(db.String(64), unique=True, index=True)  # 设备认证 Key
    timezone = db.Column(db.String(64), default='Asia/Shanghai')
    last_online = db.Column(db.DateTime, index=True)
    status = db.Column(db.String(20), default='offline',
                       index=True)  # online/offline
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    playlists = db.relationship(
        'DevicePlaylist', back_populates='device', cascade='all, delete-orphan')
    schedule = db.relationship(
        'DeviceSchedule', back_populates='device', cascade='all, delete-orphan', uselist=False)

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'hardware_id': self.hardware_id,
            'device_name': self.device_name,
            'api_key': self.api_key,
            'timezone': self.timezone,
            'last_online': self.last_online.isoformat() if self.last_online else None,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def generate_api_key(self) -> str:
        """
        生成设备 API Key

        Returns:
            新生成的 API Key
        """
        self.api_key = secrets.token_urlsafe(32)
        return self.api_key

    def regenerate_api_key(self) -> str:
        """
        重新生成 API Key（作废旧 Key）

        Returns:
            新生成的 API Key
        """
        return self.generate_api_key()

    def __repr__(self):
        return f'<Device {self.device_id}>'


class DeviceSchedule(db.Model):
    """设备定时配置"""
    __tablename__ = 'device_schedule'

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey(
        'device.id'), nullable=False, index=True)
    power_on_time = db.Column(db.Time)
    power_off_time = db.Column(db.Time)
    is_enabled = db.Column(db.Boolean, default=True, index=True)
    weekdays = db.Column(db.String(20), default='1,2,3,4,5,6,7')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    device = db.relationship('Device', back_populates='schedule')

    def to_dict(self):
        return {
            'id': self.id,
            'device_id': self.device_id,
            'power_on_time': self.power_on_time.strftime('%H:%M') if self.power_on_time else None,
            'power_off_time': self.power_off_time.strftime('%H:%M') if self.power_off_time else None,
            'is_enabled': self.is_enabled,
            'weekdays': self.weekdays.split(',')
        }
