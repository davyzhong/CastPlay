"""
播放列表相关 Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PlaylistCreate(BaseModel):
    """创建播放列表请求"""
    name: str = Field(..., min_length=1, max_length=200, description="播放列表名称")
    description: Optional[str] = Field(None, max_length=1000, description="描述")


class PlaylistUpdate(BaseModel):
    """更新播放列表请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None


class PlaylistResponse(BaseModel):
    """播放列表响应"""
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PlaylistItemCreate(BaseModel):
    """添加播放列表项请求"""
    media_id: int = Field(..., description="媒体文件 ID")
    display_duration: int = Field(default=5, ge=1, le=3600, description="显示时长（秒）")


class PlaylistItemResponse(BaseModel):
    """播放列表项响应"""
    id: int
    media_id: int
    file_name: str
    file_type: str
    display_order: int
    display_duration: int
    created_at: datetime

    class Config:
        from_attributes = True


class DevicePlaylistResponse(BaseModel):
    """设备播放列表关联响应"""
    id: int
    device_id: int
    playlist_id: int
    is_active: bool
    assigned_at: datetime

    class Config:
        from_attributes = True


class PlaylistDetailResponse(BaseModel):
    """播放列表详情响应"""
    id: int
    name: str
    description: Optional[str] = None
    items: List[PlaylistItemResponse]
    devices: List[dict]  # 简化处理
    created_at: datetime
    updated_at: datetime


class PlaylistListResponse(BaseModel):
    """播放列表列表响应"""
    items: List[PlaylistResponse]
    total: int
    page: int
    per_page: int
    pages: int


class ReorderItemsRequest(BaseModel):
    """重新排序请求"""
    items: List[dict]  # [{"id": 1, "order": 0}, ...]
