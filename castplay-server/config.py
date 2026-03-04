"""CastPlay Server Configuration

安全配置指南：
- 生产环境必须设置 SECRET_KEY 和 JWT_SECRET_KEY 环境变量
- Redis 密码通过 REDIS_PASSWORD 环境变量配置
- 不要在代码中硬编码任何密钥或密码
"""
import os
import secrets
import logging
import platform
import shutil
from typing import Dict, Set, List, Optional

logger = logging.getLogger(__name__)

# ============= 常量定义 =============
# 文件大小限制
MAX_FILE_SIZE_MB: int = 500
MAX_CONTENT_LENGTH: int = MAX_FILE_SIZE_MB * 1024 * 1024

# 默认时长配置
DEFAULT_PPT_FRAME_DURATION: int = 5  # 每页幻灯片默认时长（秒）
DEFAULT_IMAGE_DISPLAY_DURATION: int = 5  # 图片默认显示时长（秒）

# 心跳间隔
HEARTBEAT_INTERVAL_SECONDS: int = 60

# 分页默认值
DEFAULT_PAGE_SIZE: int = 20
MAX_PAGE_SIZE: int = 100

# 基准目录（castplay-server 所在目录）
BASE_DIR: str = os.path.dirname(__file__)

# 允许的文件扩展名
ALLOWED_IMAGE_EXTENSIONS: Set[str] = {
    'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'}
ALLOWED_VIDEO_EXTENSIONS: Set[str] = {'mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv'}
ALLOWED_PPT_EXTENSIONS: Set[str] = {'ppt', 'pptx'}


def _get_redis_url(default_host: str = 'localhost', default_port: int = 6379, default_db: int = 0) -> str:
    """构建 Redis URL，密码从环境变量获取"""
    host = os.environ.get('REDIS_HOST', default_host)
    port = os.environ.get('REDIS_PORT', str(default_port))
    password = os.environ.get('REDIS_PASSWORD', '')
    db = os.environ.get('REDIS_DB', str(default_db))

    if password:
        return f'redis://:{password}@{host}:{port}/{db}'
    return f'redis://{host}:{port}/{db}'


def _generate_dev_secret() -> str:
    """为开发环境生成随机密钥（每次启动不同）"""
    return secrets.token_hex(32)


def _detect_libreoffice_path() -> str:
    """跨平台检测 LibreOffice 路径"""
    # 优先使用环境变量
    if os.environ.get('LIBREOFFICE_PATH'):
        return os.environ['LIBREOFFICE_PATH']

    system = platform.system()

    # 平台特定的常见路径
    platform_paths = {
        'Darwin': [  # macOS
            '/Applications/LibreOffice.app/Contents/MacOS/soffice',
            '/opt/homebrew/bin/soffice',
            '/usr/local/bin/soffice',
        ],
        'Linux': [
            '/usr/bin/libreoffice',
            '/usr/bin/soffice',
            '/usr/lib/libreoffice/program/soffice',
            '/opt/libreoffice/program/soffice',
        ],
        'Windows': [
            r'C:\Program Files\LibreOffice\program\soffice.exe',
            r'C:\Program Files (x86)\LibreOffice\program\soffice.exe',
        ],
    }

    # 检查平台特定路径
    for path in platform_paths.get(system, []):
        if os.path.exists(path):
            return path

    # 尝试使用 shutil.which 查找 PATH 中的命令
    for cmd in ['soffice', 'libreoffice']:
        found = shutil.which(cmd)
        if found:
            return found

    # 默认值（可能不存在，但避免启动崩溃）
    logger.warning("LibreOffice not found, PPT conversion may fail")
    return 'soffice'


def _detect_ffmpeg_path() -> str:
    """跨平台检测 FFmpeg 路径"""
    # 优先使用环境变量
    if os.environ.get('FFMPEG_PATH'):
        return os.environ['FFMPEG_PATH']

    system = platform.system()

    platform_paths = {
        'Darwin': [
            '/opt/homebrew/bin/ffmpeg',
            '/usr/local/bin/ffmpeg',
        ],
        'Linux': [
            '/usr/bin/ffmpeg',
            '/usr/local/bin/ffmpeg',
        ],
        'Windows': [
            r'C:\ffmpeg\bin\ffmpeg.exe',
            r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',
        ],
    }

    for path in platform_paths.get(system, []):
        if os.path.exists(path):
            return path

    found = shutil.which('ffmpeg')
    if found:
        return found

    logger.warning("FFmpeg not found, video conversion may fail")
    return 'ffmpeg'


class Config:
    """Base configuration"""
    # 安全配置 - 开发环境使用随机生成的密钥
    SECRET_KEY: str = os.environ.get('SECRET_KEY') or _generate_dev_secret()
    JWT_SECRET_KEY: str = os.environ.get(
        'JWT_SECRET_KEY') or _generate_dev_secret()

    # Database
    SQLALCHEMY_DATABASE_URI: str = os.environ.get(
        'DATABASE_URL') or 'sqlite:///castplay.db'
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # 数据库连接池配置
    SQLALCHEMY_ENGINE_OPTIONS: Dict = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    # File Storage
    _BASE_DIR = os.path.dirname(__file__)
    UPLOAD_FOLDER: str = os.path.join(_BASE_DIR, 'storage/uploads')
    CONVERTED_FOLDER: str = os.path.join(_BASE_DIR, 'storage/converted')
    THUMBNAIL_FOLDER: str = os.path.join(_BASE_DIR, 'storage/thumbnails')
    MAX_CONTENT_LENGTH: int = MAX_CONTENT_LENGTH

    ALLOWED_EXTENSIONS: Dict[str, Set[str]] = {
        'image': ALLOWED_IMAGE_EXTENSIONS,
        'video': ALLOWED_VIDEO_EXTENSIONS,
        'ppt': ALLOWED_PPT_EXTENSIONS
    }

    # Celery - 从环境变量获取 Redis 配置
    CELERY_BROKER_URL: Optional[str] = os.environ.get(
        'CELERY_BROKER_URL') or _get_redis_url()
    CELERY_RESULT_BACKEND: Optional[str] = os.environ.get(
        'CELERY_RESULT_BACKEND') or _get_redis_url()

    # Redis URL - 用于 WebSocket 状态存储等
    REDIS_URL: Optional[str] = os.environ.get('REDIS_URL') or _get_redis_url()

    # WebSocket
    SOCKETIO_MESSAGE_QUEUE: Optional[str] = os.environ.get(
        'SOCKETIO_MESSAGE_QUEUE')
    WEBSOCKET_URL: str = os.environ.get(
        'WEBSOCKET_URL') or 'ws://localhost:5001'

    # PPT Conversion - 使用跨平台检测
    LIBREOFFICE_PATH: str = _detect_libreoffice_path()
    FFMPEG_PATH: str = _detect_ffmpeg_path()
    PPT_FRAME_DURATION: int = DEFAULT_PPT_FRAME_DURATION

    # CORS - 支持逗号分隔的多个源
    CORS_ORIGINS: List[str] = os.environ.get(
        'CORS_ORIGINS',
        'http://localhost:3000,http://localhost:5001,http://localhost:5173'
    ).split(',')

    # 日志配置
    LOG_LEVEL: str = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    @classmethod
    def init_app(cls, app) -> None:
        """应用初始化钩子"""
        pass


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG: bool = True
    TESTING: bool = False
    LOG_LEVEL: str = 'DEBUG'

    @classmethod
    def init_app(cls, app) -> None:
        Config.init_app(app)
        logger.info("Running in DEVELOPMENT mode")


class ProductionConfig(Config):
    """Production configuration

    生产环境必须通过环境变量设置以下配置：
    - SECRET_KEY: 应用密钥
    - JWT_SECRET_KEY: JWT 签名密钥
    - DATABASE_URL: PostgreSQL 数据库连接字符串
    """
    DEBUG: bool = False
    TESTING: bool = False
    LOG_LEVEL: str = 'WARNING'

    # 生产环境强制从环境变量获取密钥
    SECRET_KEY: str = os.environ.get('SECRET_KEY', '')
    JWT_SECRET_KEY: str = os.environ.get('JWT_SECRET_KEY', '')

    # 生产环境数据库连接池优化
    SQLALCHEMY_ENGINE_OPTIONS: Dict = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 20,
    }

    @classmethod
    def init_app(cls, app) -> None:
        Config.init_app(app)

        # 检查必需的环境变量
        required_vars = ['SECRET_KEY', 'JWT_SECRET_KEY', 'DATABASE_URL']
        missing_vars = [
            var for var in required_vars if not os.environ.get(var)]

        if missing_vars:
            error_msg = f"生产环境缺少必需的环境变量: {', '.join(missing_vars)}"
            logger.critical(error_msg)
            raise ValueError(error_msg)

        # 检查密钥长度
        if len(cls.SECRET_KEY) < 32:
            logger.warning("SECRET_KEY 长度小于32字符，建议使用更长的密钥")

        # 生产环境强制使用 PostgreSQL
        db_url = os.environ.get('DATABASE_URL', '')
        if not db_url.startswith('postgresql'):
            error_msg = "生产环境必须使用 PostgreSQL 数据库，请设置 DATABASE_URL=postgresql://..."
            logger.critical(error_msg)
            raise ValueError(error_msg)

        logger.info("Running in PRODUCTION mode with PostgreSQL")


class TestingConfig(Config):
    """Testing configuration"""
    TESTING: bool = True
    DEBUG: bool = True
    SKIP_AUTH: bool = True  # 测试模式跳过认证
    SQLALCHEMY_DATABASE_URI: str = 'sqlite:///:memory:'
    SOCKETIO_MESSAGE_QUEUE: Optional[str] = None
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None
    WTF_CSRF_ENABLED: bool = False

    @classmethod
    def init_app(cls, app) -> None:
        Config.init_app(app)
        logger.info("Running in TESTING mode")


config: Dict[str, type] = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
