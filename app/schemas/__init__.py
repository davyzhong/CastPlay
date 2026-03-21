"""
Pydantic Schemas
用于请求和响应的数据验证
"""
from app.schemas.user import (
    UserBase, UserCreate, UserResponse, UserLogin
)
from app.schemas.device import (
    DeviceCreate, DeviceResponse, DeviceUpdate,
    DeviceScheduleCreate, DeviceScheduleResponse
)
from app.schemas.media import (
    MediaFileCreate, MediaFileResponse, MediaFileUpdate
)
from app.schemas.playlist import (
    PlaylistCreate, PlaylistResponse, PlaylistUpdate,
    PlaylistItemCreate, PlaylistItemResponse,
    DevicePlaylistResponse, PlaylistDetailResponse
)

__all__ = [
    # User
    "UserBase", "UserCreate", "UserResponse", "UserLogin",
    # Device
    "DeviceCreate", "DeviceResponse", "DeviceUpdate",
    "DeviceScheduleCreate", "DeviceScheduleResponse",
    # Media
    "MediaFileCreate", "MediaFileResponse", "MediaFileUpdate",
    # Playlist
    "PlaylistCreate", "PlaylistResponse", "PlaylistUpdate",
    "PlaylistItemCreate", "PlaylistItemResponse",
    "DevicePlaylistResponse", "PlaylistDetailResponse",
]
