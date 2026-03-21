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
    is_system: bool = False
    item_count: int = 0
    device_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PlaylistItemCreate(BaseModel):
    """添加播放列表项请求"""
    media_id: int = Field(..., description="媒体文件 ID")
    display_duration: int = Field(default=5, ge=1, le=3600, description="显示时长（秒）")


class PlaylistItemUpdate(BaseModel):
    """更新播放列表项请求"""
    display_duration: int = Field(..., ge=1, le=3600, description="显示时长（秒）")


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
    assigned_at: Optional[datetime] = None  # 使用 created_at 作为分配时间

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_with_assigned_at(cls, obj):
        """从 ORM 对象创建，使用 created_at 作为 assigned_at"""
        return cls(
            id=obj.id,
            device_id=obj.device_id,
            playlist_id=obj.playlist_id,
            is_active=obj.is_active,
            assigned_at=obj.created_at
        )


class PlaylistDetailResponse(BaseModel):
    """播放列表详情响应"""
    id: int
    name: str
    description: Optional[str] = None
    is_system: bool = False
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


class ReorderItemData(BaseModel):
    """单个排序项数据"""
    id: int = Field(..., ge=1, description="播放列表项 ID")
    order: int = Field(..., ge=0, le=10000, description="显示顺序")


class ReorderItemsRequest(BaseModel):
    """重新排序请求"""
    items: List[ReorderItemData] = Field(..., min_length=1, max_length=100, description="排序项列表")


class PlaylistItemBatchCreate(BaseModel):
    """批量添加播放列表项请求"""
    media_ids: List[int] = Field(..., min_length=1, max_length=50, description="媒体文件 ID 列表")
    display_duration: int = Field(default=5, ge=1, le=3600, description="默认显示时长（秒）")


class PlaylistItemBatchResponse(BaseModel):
    """批量添加播放列表项响应"""
    added_count: int
    items: List[PlaylistItemResponse]
    failed_media_ids: List[int] = []
