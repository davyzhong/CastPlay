"""
Pydantic Schemas for Playlist API
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class PlaylistItemBase(BaseModel):
    """播放列表项基础模型"""
    media_id: int
    display_order: int = Field(0, ge=0)
    display_duration: int = Field(10, ge=1, description="显示时长（秒）")


class PlaylistItemCreate(PlaylistItemBase):
    """创建播放列表项"""
    pass


class PlaylistItemResponse(PlaylistItemBase):
    """播放列表项响应"""
    id: int
    media_name: Optional[str] = None
    media_type: Optional[str] = None
    file_url: Optional[str] = None

    class Config:
        from_attributes = True


class PlaylistBase(BaseModel):
    """播放列表基础模型"""
    name: str = Field(..., min_length=1, max_length=128, description="播放列表名称")
    description: Optional[str] = Field(None, max_length=500)


class PlaylistCreate(PlaylistBase):
    """创建播放列表"""
    items: List[PlaylistItemCreate] = Field(default_factory=list)


class PlaylistUpdate(BaseModel):
    """更新播放列表"""
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    description: Optional[str] = Field(None, max_length=500)


class PlaylistResponse(PlaylistBase):
    """播放列表响应"""
    id: int
    version: int
    item_count: int
    created_at: datetime
    updated_at: datetime
    items: List[PlaylistItemResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class PlaylistListResponse(BaseModel):
    """播放列表列表响应"""
    playlists: List[PlaylistResponse]
    total: int
    page: int
    per_page: int
    pages: int


class PlaylistAssignRequest(BaseModel):
    """分配播放列表请求"""
    device_ids: List[int] = Field(..., min_length=1)
    is_active: bool = Field(True)
