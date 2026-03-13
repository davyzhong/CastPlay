"""
媒体文件相关 Schemas
"""
from pydantic import BaseModel, Field, field_serializer
from typing import Optional
from datetime import datetime


class MediaFileCreate(BaseModel):
    """媒体文件上传响应（不用于创建，仅用于响应）"""
    # 这个 Schema 主要用于响应，创建是通过文件上传实现的
    pass


class MediaFileUpdate(BaseModel):
    """更新媒体文件请求"""
    file_name: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(ready|processing|failed)$")
    slide_duration: Optional[int] = Field(None, ge=1, le=60)


class MediaFileResponse(BaseModel):
    """媒体文件响应"""
    id: int
    file_name: str
    file_type: str
    file_path: str
    file_size: Optional[int] = None
    converted_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    md5_hash: Optional[str] = None
    status: str
    duration: Optional[int] = None
    slide_duration: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @field_serializer('file_path', 'converted_path', 'thumbnail_path')
    def serialize_path_to_url(self, path: Optional[str]) -> Optional[str]:
        """将文件路径转换为可访问的 URL"""
        if path and path.startswith('data/'):
            return path.replace('data/', '/media/', 1)
        return path


class MediaFileListResponse(BaseModel):
    """媒体文件列表响应"""
    items: list[MediaFileResponse]
    total: int
    page: int
    per_page: int
    pages: int


class UploadResponse(BaseModel):
    """文件上传响应"""
    message: str
    media: MediaFileResponse
