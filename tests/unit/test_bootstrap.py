"""
Bootstrap 模块单元测试
覆盖 ApplicationBootstrap 的所有公开方法
"""
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from app.bootstrap.application import ApplicationBootstrap
from fastapi import FastAPI


class TestApplicationBootstrap:
    """ApplicationBootstrap 类测试"""

    @pytest.fixture
    def bootstrap(self):
        """创建 Bootstrap 实例"""
        return ApplicationBootstrap()

    @pytest.fixture
    def mock_env(self, monkeypatch):
        """Mock 环境变量为测试模式"""
        monkeypatch.setenv("TESTING", "true")
        monkeypatch.setenv("ENVIRONMENT", "development")
        # Mock settings 对象
        from unittest.mock import MagicMock
        mock_settings = MagicMock()
        mock_settings.UPLOADS_DIR = Path("/tmp/test_uploads")
        mock_settings.CONVERTED_DIR = Path("/tmp/test_converted")
        mock_settings.THUMBNAILS_DIR = Path("/tmp/test_thumbnails")
        mock_settings.BACKUPS_DIR = Path("/tmp/test_backups")
        
        with patch('app.bootstrap.application.settings', mock_settings):
            yield mock_settings

    def test_bootstrap_initialization(self, bootstrap):
        """测试 Bootstrap 初始化"""
        assert bootstrap.app is not None
        assert isinstance(bootstrap.app, FastAPI)
        assert bootstrap.app.title == "CastPlay All-in-One"
        assert bootstrap.app.version == "2.0.0"

    def test_get_app_returns_instance(self, bootstrap):
        """测试 get_app 方法返回正确的实例"""
        app = bootstrap.get_app()
        assert app is not None
        assert isinstance(app, FastAPI)
        assert app is bootstrap.app

    @pytest.mark.asyncio
    async def test_startup_creates_directories(self, bootstrap, mock_env):
        """测试启动时创建必要的目录"""
        # 创建临时目录
        import tempfile
        import shutil
        
        temp_base = Path(tempfile.mkdtemp())
        try:
            mock_env.UPLOADS_DIR = temp_base / "uploads"
            mock_env.CONVERTED_DIR = temp_base / "converted"
            mock_env.THUMBNAILS_DIR = temp_base / "thumbnails"
            mock_env.BACKUPS_DIR = temp_base / "backups"

            await bootstrap.startup()

            # 验证目录被创建
            assert mock_env.UPLOADS_DIR.exists()
            assert mock_env.CONVERTED_DIR.exists()
            assert mock_env.THUMBNAILS_DIR.exists()
            assert mock_env.BACKUPS_DIR.exists()
        finally:
            shutil.rmtree(temp_base)

    @pytest.mark.asyncio
    async def test_startup_registers_routes(self, bootstrap, mock_env):
        """测试启动时注册 API 路由"""
        with patch('app.bootstrap.application.init_database'):
            with patch.object(bootstrap, '_register_routes', wraps=bootstrap._register_routes) as mock_register:
                await bootstrap.startup()
                mock_register.assert_called_once()

        # 验证路由已注册
        app = bootstrap.get_app()
        routes = [route.path for route in app.routes]

        # 检查核心路由
        assert any('/api/auth' in r for r in routes)
        assert any('/api/devices' in r for r in routes)
        assert any('/api/media' in r for r in routes)
        assert any('/api/playlists' in r for r in routes)
        assert any('/api/player' in r for r in routes)

    @pytest.mark.asyncio
    async def test_startup_sets_up_middleware(self, bootstrap, mock_env):
        """测试启动时配置中间件"""
        with patch('app.bootstrap.application.init_database'):
            with patch.object(bootstrap, '_setup_middleware', wraps=bootstrap._setup_middleware) as mock_setup:
                await bootstrap.startup()
                mock_setup.assert_called_once()

    @pytest.mark.asyncio
    async def test_startup_starts_scheduler(self, bootstrap, mock_env):
        """测试启动时启动调度器"""
        with patch('app.bootstrap.application.init_database'):
            with patch('app.bootstrap.application.start_scheduler') as mock_start:
                await bootstrap.startup()
                mock_start.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_stops_scheduler(self, bootstrap, mock_env):
        """测试关闭时停止调度器"""
        with patch('app.bootstrap.application.stop_scheduler') as mock_stop:
            await bootstrap.shutdown()
            mock_stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_startup_logs_welcome_message(self, bootstrap, mock_env, caplog):
        """测试启动时输出欢迎日志"""
        with patch('app.bootstrap.application.init_database'):
            await bootstrap.startup()

            # 验证日志包含关键信息
            assert "CastPlay All-in-One" in caplog.text
            assert "starting..." in caplog.text.lower()

    @pytest.mark.asyncio
    async def test_shutdown_logs_message(self, bootstrap, caplog):
        """测试关闭时输出日志"""
        await bootstrap.shutdown()
        assert "Shutting down" in caplog.text


class TestBootstrapDirectoryCreation:
    """测试目录创建逻辑"""

    @pytest.fixture
    def bootstrap(self):
        return ApplicationBootstrap()

    def test_create_directories_creates_all_paths(self, bootstrap, tmp_path):
        """测试创建所有必要目录"""
        with patch('app.bootstrap.application.settings') as mock_settings:
            mock_settings.UPLOADS_DIR = tmp_path / "uploads"
            mock_settings.CONVERTED_DIR = tmp_path / "converted"
            mock_settings.THUMBNAILS_DIR = tmp_path / "thumbnails"
            mock_settings.BACKUPS_DIR = tmp_path / "backups"

            bootstrap._create_directories()

            # 验证所有目录存在
            assert mock_settings.UPLOADS_DIR.exists()
            assert mock_settings.CONVERTED_DIR.exists()
            assert mock_settings.THUMBNAILS_DIR.exists()
            assert mock_settings.BACKUPS_DIR.exists()

    def test_create_directories_handles_existing_dirs(self, bootstrap, tmp_path):
        """测试处理已存在的目录"""
        with patch('app.bootstrap.application.settings') as mock_settings:
            # 预先创建目录
            mock_settings.UPLOADS_DIR = tmp_path / "uploads"
            mock_settings.UPLOADS_DIR.mkdir(parents=True)

            # 不应抛出异常
            bootstrap._create_directories()
            assert mock_settings.UPLOADS_DIR.exists()

    def test_create_directories_creates_parent_dirs(self, bootstrap, tmp_path):
        """测试创建父目录"""
        with patch('app.bootstrap.application.settings') as mock_settings:
            deep_path = tmp_path / "level1" / "level2" / "uploads"
            mock_settings.UPLOADS_DIR = deep_path

            bootstrap._create_directories()

            assert deep_path.exists()
            assert deep_path.parent.exists()


class TestBootstrapMiddlewareSetup:
    """测试中间件配置"""

    @pytest.fixture
    def bootstrap(self):
        return ApplicationBootstrap()

    def test_setup_middleware_adds_cors(self, bootstrap):
        """测试中间件配置添加 CORS"""
        with patch('app.bootstrap.application.setup_cors') as mock_setup:
            bootstrap._setup_middleware()
            mock_setup.assert_called_once_with(bootstrap.app)


class TestBootstrapRouteRegistration:
    """测试路由注册"""

    @pytest.fixture
    def bootstrap(self):
        return ApplicationBootstrap()

    def test_register_routes_includes_all_apis(self, bootstrap):
        """测试注册所有 API 路由"""
        # Mock 导入避免循环依赖
        with patch('app.api.auth.router'):
            with patch('app.api.devices.router'):
                with patch('app.api.media.router'):
                    with patch('app.api.playlists.router'):
                        with patch('app.api.player.router'):
                            # 不应抛出异常
                            bootstrap._register_routes()

    def test_register_routes_mounts_static_files(self, bootstrap, tmp_path):
        """测试挂载静态文件"""
        # 创建假的前端目录
        frontend_dist = tmp_path / "frontend" / "dist"
        frontend_dist.mkdir(parents=True)
        (frontend_dist / "index.html").touch()

        with patch('pathlib.Path.__truediv__', return_value=frontend_dist):
            bootstrap._register_routes()

            # 验证静态文件被挂载
            app = bootstrap.get_app()
            assert any(route.path == "/" for route in app.routes)


class TestBootstrapErrorHandling:
    """测试错误处理"""

    @pytest.fixture
    def bootstrap(self):
        return ApplicationBootstrap()

    @pytest.mark.asyncio
    async def test_startup_handles_database_error(self, bootstrap, mock_env):
        """测试启动时处理数据库错误"""
        with patch('app.bootstrap.application.init_database') as mock_init:
            mock_init.side_effect = Exception("Database error")

            # 应抛出异常
            with pytest.raises(Exception, match="Database error"):
                await bootstrap.startup()

    @pytest.mark.asyncio
    async def test_startup_handles_scheduler_error(self, bootstrap, mock_env):
        """测试启动时处理调度器错误"""
        with patch('app.bootstrap.application.init_database'):
            with patch('app.bootstrap.application.start_scheduler') as mock_start:
                mock_start.side_effect = Exception("Scheduler error")

                # 应抛出异常
                with pytest.raises(Exception, match="Scheduler error"):
                    await bootstrap.startup()

    @pytest.mark.asyncio
    async def test_shutdown_handles_scheduler_stop_error(self, bootstrap):
        """测试关闭时处理调度器停止错误"""
        with patch('app.bootstrap.application.stop_scheduler') as mock_stop:
            mock_stop.side_effect = Exception("Stop error")

            # 应抛出异常
            with pytest.raises(Exception, match="Stop error"):
                await bootstrap.shutdown()
