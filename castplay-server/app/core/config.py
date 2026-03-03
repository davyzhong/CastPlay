"""CastPlay Server - Configuration using Pydantic Settings"""
import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """应用配置 - 使用 Pydantic Settings 自动从环境变量加载"""

    # 应用配置
    DEBUG: bool = True
    PORT: int = 5001
    LOG_LEVEL: str = "INFO"

    # 安全配置
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # 数据库配置
    DATABASE_URL: str = "sqlite+aiosqlite:///./storage/castplay.db"

    # Redis 配置
    REDIS_URL: str = "redis://localhost:6379/0"

    # 存储路径配置
    STORAGE_PATH: str = "./storage"
    UPLOAD_FOLDER: str = "./storage/uploads"
    CONVERTED_FOLDER: str = "./storage/converted"
    THUMBNAIL_FOLDER: str = "./storage/thumbnails"

    # 文件上传限制
    MAX_CONTENT_LENGTH: int = 500 * 1024 * 1024  # 500MB
    ALLOWED_EXTENSIONS: List[str] = [
        "jpg", "jpeg", "png", "gif", "webp",  # 图片
        "mp4", "webm", "mov", "avi",  # 视频
        "mp3", "wav", "ogg",  # 音频
        "pdf", "pptx", "ppt",  # 文档
        "html", "htm"  # 网页
    ]

    # CORS 配置
    CORS_ORIGINS: List[str] = ["http://localhost:5173",
                               "http://localhost:3000", "http://127.0.0.1:5173"]

    # 缩略图配置
    THUMBNAIL_SIZE: tuple = (320, 180)

    @property
    def jwt_secret(self) -> str:
        """JWT 密钥（复用 SECRET_KEY）"""
        return self.SECRET_KEY

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("ALLOWED_EXTENSIONS", mode="before")
    @classmethod
    def parse_allowed_extensions(cls, v):
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取配置实例（用于依赖注入）"""
    return settings
