"""
应用配置模块
使用 Pydantic Settings 进行配置管理
"""
import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""

    # 应用信息
    APP_NAME: str = "CastPlay All-in-One"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 5000

    # 数据库配置
    DATABASE_PATH: str = "data/castplay.db"

    # 文件存储路径
    DATA_DIR: Path = Path("data")
    UPLOADS_DIR: Path = Path("data/uploads")
    CONVERTED_DIR: Path = Path("data/converted")
    THUMBNAILS_DIR: Path = Path("data/thumbnails")
    BACKUPS_DIR: Path = Path("backups")

    # 文件上传限制
    MAX_FILE_SIZE: int = 500 * 1024 * 1024  # 500MB
    ALLOWED_IMAGE_TYPES: List[str] = ["jpg", "jpeg", "png", "gif", "bmp"]
    ALLOWED_VIDEO_TYPES: List[str] = ["mp4", "avi", "mov", "mkv", "flv"]
    ALLOWED_PPT_TYPES: List[str] = ["ppt", "pptx"]

    # JWT 认证配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天

    # WebSocket 配置
    WS_PING_INTERVAL: int = 30  # 秒
    WS_PING_TIMEOUT: int = 10  # 秒

    # 后台任务配置
    NUM_WORKERS: int = 3  # 后台任务线程数
    TASK_TIMEOUT: int = 600  # 任务超时时间（秒）

    # CORS 配置
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True

    # 默认管理员
    DEFAULT_ADMIN_USERNAME: str = "admin"
    DEFAULT_ADMIN_PASSWORD: str = "admin123"  # bcrypt 限制密码最多 72 字节

    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()

# 确保目录存在
settings.DATA_DIR.mkdir(exist_ok=True)
settings.UPLOADS_DIR.mkdir(exist_ok=True)
settings.CONVERTED_DIR.mkdir(exist_ok=True)
settings.THUMBNAILS_DIR.mkdir(exist_ok=True)
settings.BACKUPS_DIR.mkdir(exist_ok=True)
