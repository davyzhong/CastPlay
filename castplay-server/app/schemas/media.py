"""
Pydantic Schemas for Media API
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class MediaBase(BaseModel):
    """媒体基础模型"""
    filename: str = Field(..., max_length=255, description="文件名")
    file_type: str = Field(..., max_length=50, description="文件类型")


class MediaUploadResponse(BaseModel):
    """媒体上传响应"""
    message: str
    media: "MediaResponse"


class MediaResponse(BaseModel):
    """媒体响应"""
    id: int
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    file_path: str
    converted_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    md5_hash: Optional[str] = None
    status: str
    folder_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MediaListResponse(BaseModel):
    """媒体列表响应"""
    media: List[MediaResponse]
    total: int
    page: int
    per_page: int
    pages: int


class MediaUpdate(BaseModel):
    """更新媒体请求"""
    filename: Optional[str] = Field(None, max_length=255)
    folder_id: Optional[int] = None


# 解决前向引用
MediaUploadResponse.model_rebuild()
