"""
告警配置模型
存储告警配置，暂缓具体邮件/钉钉发送实现
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Boolean, Integer, Float, DateTime, Text, JSON, Column, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class AlertConfig(Base, TimestampMixin):
    """
    告警配置模型

    存储设备告警的配置信息，包括：
    - 告警触发条件
    - 通知渠道配置（预留）
    - 阈值设置
    """
    __tablename__ = "alert_configs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 设备 ID（为空表示全局配置）
    device_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=True,
        comment="设备 ID，为空表示全局默认配置"
    )

    # ========== 告警开关 ==========
    alert_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="是否启用告警"
    )

    # ========== 离线告警配置 ==========
    offline_alert_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="是否启用设备离线告警"
    )
    offline_threshold_hours: Mapped[int] = mapped_column(
        Integer,
        default=4,
        comment="离线阈值（小时），超过此时间触发告警"
    )

    # ========== 下载失败告警配置 ==========
    download_failure_alert_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="是否启用下载失败告警"
    )
    download_failure_threshold: Mapped[int] = mapped_column(
        Integer,
        default=3,
        comment="下载失败次数阈值"
    )

    # ========== 存储空间告警配置 ==========
    storage_alert_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="是否启用存储空间告警"
    )
    storage_threshold_percent: Mapped[int] = mapped_column(
        Integer,
        default=90,
        comment="存储使用率阈值（百分比）"
    )
    storage_min_free_gb: Mapped[float] = mapped_column(
        Float,
        default=1.0,
        comment="最小剩余空间（GB）"
    )

    # ========== 播放异常告警配置 ==========
    playback_alert_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="是否启用播放异常告警"
    )
    playback_error_threshold: Mapped[int] = mapped_column(
        Integer,
        default=5,
        comment="播放错误次数阈值"
    )

    # ========== 通知渠道配置（预留，暂不实现发送） ==========
    email_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否启用邮件通知"
    )
    email_recipients: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="邮件接收者，逗号分隔"
    )

    dingtalk_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否启用钉钉通知"
    )
    dingtalk_webhook: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="钉钉机器人 Webhook URL"
    )

    # ========== 静默时段配置 ==========
    quiet_hours_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否启用静默时段"
    )
    quiet_hours_start: Mapped[Optional[str]] = mapped_column(
        String(5),
        nullable=True,
        comment="静默开始时间（HH:MM）"
    )
    quiet_hours_end: Mapped[Optional[str]] = mapped_column(
        String(5),
        nullable=True,
        comment="静默结束时间（HH:MM）"
    )

    # ========== 元数据 ==========
    created_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="创建者用户 ID"
    )
    updated_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="最后更新者用户 ID"
    )

    # 关联
    device: Mapped[Optional["Device"]] = relationship(
        "Device",
        back_populates="alert_config"
    )

    def __repr__(self) -> str:
        return f"<AlertConfig(id={self.id}, device_id={self.device_id}, enabled={self.alert_enabled})>"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "device_id": self.device_id,
            "alert_enabled": self.alert_enabled,
            "offline_alert_enabled": self.offline_alert_enabled,
            "offline_threshold_hours": self.offline_threshold_hours,
            "download_failure_alert_enabled": self.download_failure_alert_enabled,
            "download_failure_threshold": self.download_failure_threshold,
            "storage_alert_enabled": self.storage_alert_enabled,
            "storage_threshold_percent": self.storage_threshold_percent,
            "storage_min_free_gb": self.storage_min_free_gb,
            "playback_alert_enabled": self.playback_alert_enabled,
            "playback_error_threshold": self.playback_error_threshold,
            "email_enabled": self.email_enabled,
            "email_recipients": self.email_recipients,
            "dingtalk_enabled": self.dingtalk_enabled,
            "dingtalk_webhook": self.dingtalk_webhook,
            "quiet_hours_enabled": self.quiet_hours_enabled,
            "quiet_hours_start": self.quiet_hours_start,
            "quiet_hours_end": self.quiet_hours_end,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def get_default_config(cls) -> "AlertConfig":
        """获取默认配置"""
        return cls(
            alert_enabled=True,
            offline_alert_enabled=True,
            offline_threshold_hours=4,
            download_failure_alert_enabled=True,
            download_failure_threshold=3,
            storage_alert_enabled=True,
            storage_threshold_percent=90,
            storage_min_free_gb=1.0,
            playback_alert_enabled=True,
            playback_error_threshold=5,
            email_enabled=False,
            dingtalk_enabled=False,
            quiet_hours_enabled=False
        )


class AlertHistory(Base, TimestampMixin):
    """
    告警历史记录

    记录所有触发的告警，用于统计和审计
    """
    __tablename__ = "alert_histories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 设备信息
    device_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
        comment="设备 ID"
    )

    # 告警类型
    alert_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="告警类型：offline/download_failed/storage/playback_error"
    )

    # 告警级别
    severity: Mapped[str] = mapped_column(
        String(20),
        default="warning",
        comment="告警级别：info/warning/error/critical"
    )

    # 告警消息
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="告警消息"
    )

    # 详细信息（JSON）
    details: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="详细信息（JSON 格式）"
    )

    # 处理状态
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        comment="状态：pending/acknowledged/resolved/ignored"
    )

    # 处理人
    acknowledged_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="确认人用户 ID"
    )
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="确认时间"
    )

    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="解决时间"
    )

    # 关联
    device: Mapped["Device"] = relationship(
        "Device",
        back_populates="alert_histories"
    )

    def __repr__(self) -> str:
        return f"<AlertHistory(id={self.id}, device_id={self.device_id}, type={self.alert_type}, status={self.status})>"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "device_id": self.device_id,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "message": self.message,
            "details": self.details,
            "status": self.status,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
