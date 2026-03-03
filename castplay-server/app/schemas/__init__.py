"""
Pydantic Schemas - 统一导出
"""
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    UserInfo,
    RefreshRequest,
    RefreshResponse,
    ChangePasswordRequest,
)

from app.schemas.device import (
    DeviceBase,
    DeviceCreate,
    DeviceUpdate,
    DeviceRegister,
    DeviceResponse,
    DeviceListResponse,
    DeviceRegisterResponse,
    ScheduleBase,
    ScheduleCreate,
    ScheduleResponse,
)

from app.schemas.media import (
    MediaBase,
    MediaResponse,
    MediaListResponse,
    MediaUpdate,
    MediaUploadResponse,
)

from app.schemas.playlist import (
    PlaylistBase,
    PlaylistCreate,
    PlaylistUpdate,
    PlaylistResponse,
    PlaylistListResponse,
    PlaylistItemBase,
    PlaylistItemCreate,
    PlaylistItemResponse,
    PlaylistAssignRequest,
)


# 通用响应模型
from pydantic import BaseModel
from typing import Optional, Any


class MessageResponse(BaseModel):
    """通用消息响应"""
    message: str
    detail: Optional[str] = None


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str
    message: str
    detail: Optional[Any] = None
