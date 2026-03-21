"""
基础模型类
定义通用的基类和混合类
"""
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class TimestampMixin:
    """
    时间戳混合类
    为模型自动添加 created_at 和 updated_at 字段
    """
    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        doc="创建时间"
    )
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="更新时间"
    )
