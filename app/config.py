"""
应用配置模块
使用 Pydantic Settings 进行配置管理
"""
import os
import secrets
import json
import warnings
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from loguru import logger


# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 密钥文件路径（用于存储自动生成的开发环境密钥）
DEV_SECRET_KEY_FILE = PROJECT_ROOT / "data" / ".dev_secret_key"


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
    # SECRET_KEY 从 .env 文件加载，如果没有则使用默认值（仅开发环境）
    SECRET_KEY: Optional[str] = None
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
            origins_str = os.getenv(
                "CORS_ORIGINS", '["http://localhost:3000"]')
            # 如果是字符串（JSON 格式），需要解析
            if isinstance(origins_str, str):
                try:
                    return json.loads(origins_str)
                except json.JSONDecodeError:
                    # 如果是逗号分隔的字符串
                    return [o.strip() for o in origins_str.split(",") if o.strip()]
            return origins_str
        else:
            # 开发环境允许所有来源（包括 null origin 用于本地文件和 Android WebView）
            return ["*", "null"]

    CORS_ALLOW_CREDENTIALS: bool = True

    # 默认管理员
    DEFAULT_ADMIN_USERNAME: str = "admin"
    DEFAULT_ADMIN_PASSWORD: Optional[str] = None  # 必须通过环境变量设置

    # 标记是否已显示过密码（避免重复打印）
    _password_displayed: bool = False

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
        self._password_displayed = False

    def display_admin_password_once(self) -> Optional[str]:
        """
        仅在首次调用时返回管理员密码，之后返回 None

        用于在启动时显示一次密码，避免重复打印到日志

        Returns:
            首次调用返回密码，之后返回 None
        """
        if self._password_displayed:
            return None

        self._password_displayed = True

        # 只有自动生成的密码（token_urlsafe 格式）才需要显示
        if self.DEFAULT_ADMIN_PASSWORD and len(self.DEFAULT_ADMIN_PASSWORD) == 22 and '-' in self.DEFAULT_ADMIN_PASSWORD:
            return self.DEFAULT_ADMIN_PASSWORD

        return None

    def validate_production_config(self) -> List[str]:
        """
        验证生产环境配置

        Returns:
            警告消息列表
        """
        warnings_list = []

        if self.ENVIRONMENT != "production":
            return warnings_list

        # 检查 SECRET_KEY
        if not self.SECRET_KEY:
            warnings_list.append("生产环境必须设置 SECRET_KEY！")
        elif len(self.SECRET_KEY) < 32:
            warnings_list.append("SECRET_KEY 长度不足 32 字符，建议使用强随机密钥！")

        # 检查 CORS 配置
        if "*" in self.CORS_ORIGINS:
            warnings_list.append("不建议使用 CORS_ORIGINS=['*']，请配置具体域名！")

        return warnings_list

    def get_secret_key(self) -> str:
        """
        获取有效的 SECRET_KEY

        - 生产环境：必须通过环境变量配置
        - 开发环境：自动生成并持久化到文件，避免重启后 token 失效
        """
        if self.SECRET_KEY:
            return self.SECRET_KEY

        if self.ENVIRONMENT == "production":
            raise ValueError(
                "生产环境必须设置 SECRET_KEY 环境变量！"
                "请在 .env 文件中配置 SECRET_KEY=<your-secret-key>"
            )

        # 开发环境：尝试从文件读取或生成新密钥
        try:
            # 确保目录存在
            DEV_SECRET_KEY_FILE.parent.mkdir(parents=True, exist_ok=True)

            if DEV_SECRET_KEY_FILE.exists():
                key = DEV_SECRET_KEY_FILE.read_text().strip()
                if key and len(key) >= 32:
                    logger.debug(f"Loaded dev secret key from {DEV_SECRET_KEY_FILE}")
                    return key

            # 生成新密钥并保存
            new_key = secrets.token_urlsafe(32)
            DEV_SECRET_KEY_FILE.write_text(new_key)
            DEV_SECRET_KEY_FILE.chmod(0o600)  # 仅所有者可读写
            logger.info(f"Generated new dev secret key saved to {DEV_SECRET_KEY_FILE}")
            return new_key

        except Exception as e:
            # 如果文件操作失败，使用内存中的随机密钥（重启后 token 会失效）
            warnings.warn(
                f"无法保存开发环境密钥到文件: {e}。重启后 token 将失效。",
                UserWarning
            )
            return secrets.token_urlsafe(32)


# 创建全局配置实例
settings = Settings()

# 确保目录存在
settings.DATA_DIR.mkdir(exist_ok=True)
settings.UPLOADS_DIR.mkdir(exist_ok=True)
settings.CONVERTED_DIR.mkdir(exist_ok=True)
settings.THUMBNAILS_DIR.mkdir(exist_ok=True)
settings.BACKUPS_DIR.mkdir(exist_ok=True)
