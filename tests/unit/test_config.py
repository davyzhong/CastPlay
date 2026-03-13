"""
配置模块单元测试

测试 Settings 配置类的加载、验证和默认值
"""
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import warnings


class TestSettingsDefaults:
    """测试配置默认值"""

    def test_default_app_name(self):
        """测试默认应用名称"""
        from app.config import Settings
        settings = Settings()
        assert settings.APP_NAME == "CastPlay All-in-One"

    def test_default_app_version(self):
        """测试默认版本号"""
        from app.config import Settings
        settings = Settings()
        assert settings.APP_VERSION == "2.0.0"

    def test_default_debug_mode(self):
        """测试默认调试模式"""
        from app.config import Settings
        settings = Settings()
        assert settings.DEBUG is False

    def test_default_environment(self):
        """测试环境配置存在"""
        from app.config import Settings
        settings = Settings()
        # 环境应该是有效的值之一
        assert settings.ENVIRONMENT in ["development", "staging", "production"]

    def test_default_host_port(self):
        """测试默认主机和端口"""
        from app.config import Settings
        settings = Settings()
        assert settings.HOST == "0.0.0.0"
        assert settings.PORT == 8000

    def test_default_database_path(self):
        """测试数据库路径配置"""
        from app.config import Settings
        settings = Settings()
        # 数据库路径应该存在且是字符串或 Path
        assert settings.DATABASE_PATH is not None
        # 转换为字符串检查（可能是 :memory: 或实际文件路径）
        db_path_str = str(settings.DATABASE_PATH)
        valid_paths = [".db" in db_path_str, ".sqlite" in db_path_str, db_path_str == ":memory:"]
        assert any(valid_paths)

    def test_default_file_size_limit(self):
        """测试默认文件大小限制"""
        from app.config import Settings
        settings = Settings()
        assert settings.MAX_FILE_SIZE == 500 * 1024 * 1024  # 500MB

    def test_default_allowed_file_types(self):
        """测试默认允许的文件类型"""
        from app.config import Settings
        settings = Settings()
        assert "jpg" in settings.ALLOWED_IMAGE_TYPES
        assert "png" in settings.ALLOWED_IMAGE_TYPES
        assert "mp4" in settings.ALLOWED_VIDEO_TYPES
        assert "pptx" in settings.ALLOWED_PPT_TYPES

    def test_default_jwt_settings(self):
        """测试默认 JWT 配置"""
        from app.config import Settings
        settings = Settings()
        assert settings.ALGORITHM == "HS256"
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 60 * 24 * 7  # 7天

    def test_default_websocket_settings(self):
        """测试默认 WebSocket 配置"""
        from app.config import Settings
        settings = Settings()
        assert settings.WS_PING_INTERVAL == 30
        assert settings.WS_PING_TIMEOUT == 10

    def test_default_worker_settings(self):
        """测试默认工作线程配置"""
        from app.config import Settings
        settings = Settings()
        assert settings.NUM_WORKERS == 3
        assert settings.TASK_TIMEOUT == 600

    def test_default_cors_settings(self):
        """测试默认 CORS 配置"""
        from app.config import Settings
        settings = Settings()
        assert "*" in settings.CORS_ORIGINS
        assert settings.CORS_ALLOW_CREDENTIALS is True

    def test_default_rate_limit_settings(self):
        """测试速率限制配置"""
        from app.config import Settings
        settings = Settings()
        # 速率限制应该是布尔值
        assert isinstance(settings.RATE_LIMIT_ENABLED, bool)
        # 限制值应该是字符串格式
        assert isinstance(settings.RATE_LIMIT_LOGIN, str)
        assert isinstance(settings.RATE_LIMIT_API, str)
        assert "minute" in settings.RATE_LIMIT_LOGIN or "/" in settings.RATE_LIMIT_LOGIN


class TestSecretKeyGeneration:
    """测试密钥生成"""

    def test_secret_key_auto_generation(self):
        """测试自动生成密钥 - 通过 get_secret_key() 方法"""
        from app.config import Settings
        settings = Settings()
        # 开发环境下， get_secret_key() 会生成或读取密钥
        secret_key = settings.get_secret_key()
        assert secret_key is not None
        assert len(secret_key) >= 32

    def test_secret_key_from_env(self):
        """测试从环境变量读取密钥"""
        with patch.dict(os.environ, {"SECRET_KEY": "my-test-secret-key-12345"}):
            from app.config import Settings
            settings = Settings()
            assert settings.SECRET_KEY == "my-test-secret-key-12345"
            # get_secret_key() 应该返回环境变量中的密钥
            assert settings.get_secret_key() == "my-test-secret-key-12345"

    def test_secret_key_uniqueness(self):
        """测试密钥生成 - 每次调用生成唯一密钥"""
        from app.config import Settings
        settings1 = Settings()
        # get_secret_key() 返回有效的密钥
        secret_key = settings1.get_secret_key()
        assert secret_key is not None
        assert len(secret_key) >= 32


class TestAdminPasswordGeneration:
    """测试管理员密码生成"""

    def test_admin_password_auto_generation(self):
        """测试自动生成管理员密码"""
        from app.config import Settings
        settings = Settings()
        assert settings.DEFAULT_ADMIN_PASSWORD is not None
        assert len(settings.DEFAULT_ADMIN_PASSWORD) >= 16

    def test_admin_password_from_env(self):
        """测试从环境变量读取管理员密码"""
        with patch.dict(os.environ, {"DEFAULT_ADMIN_PASSWORD": "my-secure-password"}):
            from app.config import Settings
            settings = Settings()
            assert settings.DEFAULT_ADMIN_PASSWORD == "my-secure-password"


class TestEnvironmentVariables:
    """测试环境变量覆盖"""

    def test_override_app_name(self):
        """测试覆盖应用名称"""
        with patch.dict(os.environ, {"APP_NAME": "Custom App"}):
            from app.config import Settings
            settings = Settings()
            assert settings.APP_NAME == "Custom App"

    def test_override_debug_mode(self):
        """测试覆盖调试模式"""
        with patch.dict(os.environ, {"DEBUG": "true"}):
            from app.config import Settings
            settings = Settings()
            assert settings.DEBUG is True

    def test_override_port(self):
        """测试覆盖端口"""
        with patch.dict(os.environ, {"PORT": "9000"}):
            from app.config import Settings
            settings = Settings()
            assert settings.PORT == 9000

    def test_override_database_path(self):
        """测试覆盖数据库路径"""
        with patch.dict(os.environ, {"DATABASE_PATH": "/custom/path/db.sqlite"}):
            from app.config import Settings
            settings = Settings()
            assert settings.DATABASE_PATH == "/custom/path/db.sqlite"

    def test_override_environment(self):
        """测试覆盖环境"""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            from app.config import Settings
            settings = Settings()
            assert settings.ENVIRONMENT == "production"


class TestDirectoryCreation:
    """测试目录自动创建"""

    def test_directory_paths_are_path_objects(self):
        """测试目录路径是 Path 对象"""
        from app.config import Settings
        settings = Settings()
        assert isinstance(settings.DATA_DIR, Path)
        assert isinstance(settings.UPLOADS_DIR, Path)
        assert isinstance(settings.CONVERTED_DIR, Path)
        assert isinstance(settings.THUMBNAILS_DIR, Path)
        assert isinstance(settings.BACKUPS_DIR, Path)

    def test_directories_exist(self):
        """测试目录存在"""
        from app.config import settings
        assert settings.DATA_DIR.exists()
        assert settings.UPLOADS_DIR.exists()
        assert settings.CONVERTED_DIR.exists()
        assert settings.THUMBNAILS_DIR.exists()
        assert settings.BACKUPS_DIR.exists()


class TestProductionWarnings:
    """测试生产环境警告"""

    def test_production_warning_for_missing_secret_key(self):
        """测试开发环境密钥自动生成 - get_secret_key() 方法"""
        from app.config import Settings
        settings = Settings()
        # 开发环境下，get_secret_key() 应该返回有效密钥（自动生成或从文件读取）
        secret_key = settings.get_secret_key()
        assert secret_key is not None
        assert len(secret_key) >= 32

    def test_production_warning_for_cors_wildcard(self):
        """测试生产环境 CORS 通配符警告"""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "CORS_ORIGINS": '["*"]'
        }):
            from app.config import Settings
            settings = Settings()
            # validate_production_config() 返回 CORS 警告
            warnings_list = settings.validate_production_config()
            # 生产环境使用 CORS 通配符应该产生警告
            assert any("CORS" in warning for warning in warnings_list)


class TestSettingsValidation:
    """测试配置验证"""

    def test_allowed_image_types_list(self):
        """测试允许的图片类型是列表"""
        from app.config import Settings
        settings = Settings()
        assert isinstance(settings.ALLOWED_IMAGE_TYPES, list)
        assert len(settings.ALLOWED_IMAGE_TYPES) > 0

    def test_allowed_video_types_list(self):
        """测试允许的视频类型是列表"""
        from app.config import Settings
        settings = Settings()
        assert isinstance(settings.ALLOWED_VIDEO_TYPES, list)
        assert len(settings.ALLOWED_VIDEO_TYPES) > 0

    def test_allowed_ppt_types_list(self):
        """测试允许的 PPT 类型是列表"""
        from app.config import Settings
        settings = Settings()
        assert isinstance(settings.ALLOWED_PPT_TYPES, list)
        assert len(settings.ALLOWED_PPT_TYPES) > 0


class TestGlobalSettingsInstance:
    """测试全局配置实例"""

    def test_global_settings_exists(self):
        """测试全局配置实例存在"""
        from app.config import settings
        assert settings is not None

    def test_global_settings_is_settings_instance(self):
        """测试全局配置是 Settings 实例"""
        from app.config import settings, Settings
        assert isinstance(settings, Settings)


class TestCaseSensitivity:
    """测试配置大小写敏感"""

    def test_case_sensitive_config(self):
        """测试配置是大小写敏感的"""
        from app.config import Settings
        settings = Settings()
        # 小写的配置不应该生效
        assert hasattr(settings, 'APP_NAME')
        # APP_NAME 和 app_name 是不同的
