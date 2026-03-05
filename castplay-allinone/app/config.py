"""
应用配置模块
使用 Pydantic Settings 进行配置管理
"""
import os
import secrets
import warnings
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent


class Settings(BaseSettings):
    """应用配置类"""

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # 应用信息
    APP_NAME: str = "CastPlay All-in-One"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development, staging, production

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000

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
    SECRET_KEY: Optional[str] = None  # 必须通过环境变量设置
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
    DEFAULT_ADMIN_PASSWORD: Optional[str] = None  # 必须通过环境变量设置

    # 速率限制配置
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_LOGIN: str = "5/minute"  # 登录限制
    RATE_LIMIT_API: str = "100/minute"  # API 限制

    @field_validator('SECRET_KEY', mode='before')
    @classmethod
    def validate_secret_key(cls, v):
        if v is None:
            # 生成随机密钥（仅用于开发环境）
            return secrets.token_urlsafe(32)
        return v

    @field_validator('DEFAULT_ADMIN_PASSWORD', mode='before')
    @classmethod
    def validate_admin_password(cls, v):
        if v is None:
            # 生成随机密码
            return secrets.token_urlsafe(16)
        return v

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 生产环境安全检查（仅在密钥是随机生成的长度时警告）
        if self.ENVIRONMENT == "production":
            # 检查是否使用自动生成的 32 字节密钥（43 个 base64 字符）
            if len(self.SECRET_KEY) == 43:
                warnings.warn(
                    "生产环境检测到自动生成的 SECRET_KEY，建议通过 .env 或环境变量设置固定密钥！"
                    "重启后会导致所有 JWT Token 失效。",
                    UserWarning
                )
            # 检查是否使用自动生成的 16 字节密码（22 个 base64 字符）
            if len(self.DEFAULT_ADMIN_PASSWORD) == 22 and '-' in self.DEFAULT_ADMIN_PASSWORD:
                print(f"ℹ️  管理员密码: {self.DEFAULT_ADMIN_PASSWORD} (请保存此密码)")
            if "*" in self.CORS_ORIGINS:
                warnings.warn(
                    "生产环境不建议使用 CORS_ORIGINS=['*']，请配置具体域名！",
                    UserWarning
                )


# 创建全局配置实例
settings = Settings()

# 确保目录存在
settings.DATA_DIR.mkdir(exist_ok=True)
settings.UPLOADS_DIR.mkdir(exist_ok=True)
settings.CONVERTED_DIR.mkdir(exist_ok=True)
settings.THUMBNAILS_DIR.mkdir(exist_ok=True)
settings.BACKUPS_DIR.mkdir(exist_ok=True)
