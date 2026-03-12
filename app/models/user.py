"""
用户模型
"""
from sqlalchemy import Column, Integer, String, Boolean
from app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """用户表"""

    __tablename__ = "users"

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # 用户信息
    username = Column(String(50), unique=True, index=True, nullable=False, doc="用户名")
    password_hash = Column(String(255), nullable=False, doc="密码哈希")
    email = Column(String(100), nullable=True, doc="邮箱")
    full_name = Column(String(100), nullable=True, doc="全名")

    # 权限标志
    is_active = Column(Boolean, default=True, nullable=False, doc="是否激活")
    is_superuser = Column(Boolean, default=False, nullable=False, doc="是否超级管理员")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>"
