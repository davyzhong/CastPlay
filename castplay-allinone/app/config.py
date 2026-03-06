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
    @property
    def SECRET_KEY(self) -> str:
        """JWT 密钥 - 内网简化版"""
        env_key = os.getenv("SECRET_KEY")

        if self.ENVIRONMENT == "production":
            # 生产环境必须设置
            if not env_key:
                raise ValueError(
                    "生产环境必须通过环境变量设置 SECRET_KEY"
                )
            return env_key
        else:
            # 开发/内网环境使用固定密钥
            return env_key or "castplay-dev-secret-key-2026-do-not-use-in-production"

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 天

    # WebSocket 配置
    WS_PING_INTERVAL: int = 30  # 秒
    WS_PING_TIMEOUT: int = 10  # 秒

    # 后台任务配置
    NUM_WORKERS: int = 3  # 后台任务线程数
    TASK_TIMEOUT: int = 600  # 任务超时时间（秒）

    # CORS 配置
    @property
    def CORS_ORIGINS(self) -> list[str]:
        """CORS 白名单 - 内网简化版"""
        if self.ENVIRONMENT == "production":
            # 生产环境从环境变量读取
            origins_str = os.getenv("CORS_ORIGINS", "")
            return [o.strip() for o in origins_str.split(",") if o.strip()]
        else:
            # 开发环境允许所有来源
            return ["*"]

    CORS_ALLOW_CREDENTIALS: bool = True

    # 默认管理员
    DEFAULT_ADMIN_USERNAME: str = "admin"
    DEFAULT_ADMIN_PASSWORD: Optional[str] = None  # 必须通过环境变量设置

    # 速率限制配置
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_LOGIN: str = "5/minute"  # 登录限制
    RATE_LIMIT_API: str = "100/minute"  # API 限制

    @property
    def LOG_LEVEL(self) -> str:
        """日志级别 - 根据环境自动调整"""
        if self.ENVIRONMENT == "production":
            return "INFO"  # 生产环境仅记录关键日志
        else:
            return "DEBUG"  # 开发环境记录详细日志

    @field_validator('DEFAULT_ADMIN_PASSWORD', mode='before')
    @classmethod
    def validate_admin_password(cls, v):
        if v is None:
            # 生成随机密码
            return secrets.token_urlsafe(16)
        return v

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 生产环境安全检查
        if self.ENVIRONMENT == "production":
            # 检查 SECRET_KEY 是否设置
            try:
                secret_key = self.SECRET_KEY
                if not secret_key or len(secret_key) < 32:
                    warnings.warn(
                        "生产环境 SECRET_KEY 长度不足 32 字符，建议使用强随机密钥！",
                        UserWarning
                    )
            except ValueError as e:
                # SECRET_KEY 未设置会抛出异常
                warnings.warn(str(e), UserWarning)

            # 检查管理员密码
            if len(self.DEFAULT_ADMIN_PASSWORD) == 22 and '-' in self.DEFAULT_ADMIN_PASSWORD:
                print(f"ℹ️  管理员密码：{self.DEFAULT_ADMIN_PASSWORD} (请保存此密码)")

            # 检查 CORS 配置
            cors_origins = self.CORS_ORIGINS
            if "*" in cors_origins:
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
