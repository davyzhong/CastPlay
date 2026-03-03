"""
Pydantic Schemas for Auth API
"""
from typing import Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=128)


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserInfo"


class UserInfo(BaseModel):
    """用户信息"""
    id: int
    username: str
    role: str = "user"


class RefreshRequest(BaseModel):
    """刷新 Token 请求"""
    refresh_token: str


class RefreshResponse(BaseModel):
    """刷新 Token 响应"""
    access_token: str
    token_type: str = "bearer"


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6, max_length=128)


# 解决前向引用
LoginResponse.model_rebuild()
