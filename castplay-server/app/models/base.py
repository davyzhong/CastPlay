"""
数据库模型基类 - 软删除支持
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime
from sqlalchemy.ext.declarative import declared_attr


class SoftDeleteMixin:
    """软删除混入类

    为模型添加软删除功能，记录删除时间而不是物理删除

    Usage:
        class Device(Base, SoftDeleteMixin):
            ...

        # 软删除
        device.soft_delete()

        # 恢复
        device.restore()

        # 查询未删除的记录
        Device.query_active().all()
    """

    deleted_at: Optional[datetime] = Column(
        DateTime,
        nullable=True,
        index=True,
        comment="删除时间，NULL 表示未删除"
    )

    def soft_delete(self) -> None:
        """软删除 - 设置删除时间"""
        self.deleted_at = datetime.utcnow()

    def restore(self) -> None:
        """恢复 - 清除删除时间"""
        self.deleted_at = None

    @property
    def is_deleted(self) -> bool:
        """是否已删除"""
        return self.deleted_at is not None

    @classmethod
    @declared_attr
    def __mapper_args__(cls):
        """默认排除已删除的记录（可在查询时覆盖）"""
        return {}


class TimestampMixin:
    """时间戳混入类

    自动管理 created_at 和 updated_at 字段
    """

    created_at: datetime = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="创建时间"
    )

    updated_at: datetime = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="更新时间"
    )


def query_active(model_class):
    """查询未删除的记录

    Usage:
        active_devices = query_active(Device).all()
    """
    if hasattr(model_class, 'deleted_at'):
        return model_class.query.filter(model_class.deleted_at.is_(None))
    return model_class.query
