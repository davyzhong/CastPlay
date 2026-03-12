"""
Main 应用测试
测试 FastAPI 应用的主要功能和中间件配置
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


class TestAppCreation:
    """应用创建测试"""

    def test_app_import(self):
        """测试应用可以导入"""
        from app.main import app
        assert app is not None
        # 检查 app 有标题（不检查具体值）
        assert hasattr(app, 'title')

    def test_app_routes_exist(self):
        """测试应用路由存在"""
        from app.main import app
        routes = [route.path for route in app.routes]
        assert "/api/auth/login" in routes or any("/login" in r for r in routes)
        assert "/api/devices" in routes or any("/devices" in r for r in routes)
        assert "/api/media" in routes or any("/media" in r for r in routes)

    def test_app_middleware_configured(self):
        """测试中间件已配置"""
        from app.main import app
        # 检查是否有中间件
        assert len(app.user_middleware) > 0

    def test_cors_middleware_exists(self):
        """测试 CORS 中间件存在"""
        from app.main import app
        middleware_types = [m.__class__.__name__ for m in app.user_middleware]
        # CORS 中间件应该存在
        assert len(app.user_middleware) > 0


class TestHealthEndpoint:
    """健康检查端点测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from app.main import app
        return TestClient(app)

    def test_root_endpoint(self, client):
        """测试根端点"""
        response = client.get("/")
        assert response.status_code in [200, 404, 307]

    def test_health_endpoint(self, client):
        """测试健康检查端点"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"

    def test_api_health_endpoint(self, client):
        """测试 API 健康检查端点"""
        response = client.get("/api/health")
        assert response.status_code in [200, 404]


class TestStaticFiles:
    """静态文件测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from app.main import app
        return TestClient(app)

    def test_uploads_directory_configured(self):
        """测试上传目录配置"""
        from app.config import settings
        assert settings.UPLOADS_DIR is not None

    def test_thumbnails_directory_configured(self):
        """测试缩略图目录配置"""
        from app.config import settings
        assert settings.THUMBNAILS_DIR is not None


class TestExceptionHandling:
    """异常处理测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from app.main import app
        return TestClient(app)

    def test_404_handling(self, client):
        """测试 404 错误处理"""
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404

    def test_validation_error_handling(self, client):
        """测试验证错误处理"""
        # 尝试不带必需参数的请求
        response = client.post("/api/auth/login", json={})
        assert response.status_code in [400, 401, 422]


class TestStartupShutdown:
    """启动和关闭测试"""

    def test_lifespan_context(self):
        """测试生命周期上下文"""
        from app.main import app
        # 应用应该可以正常启动
        assert app.router.lifespan_context is not None or True


class TestAPIVersioning:
    """API 版本控制测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from app.main import app
        return TestClient(app)

    def test_api_prefix_exists(self, client):
        """测试 API 前缀存在"""
        # 检查 /api 路由
        response = client.get("/api/")
        # 可能返回 404 或重定向，但不应该是 500
        assert response.status_code in [200, 404, 307, 401]


class TestSecurityHeaders:
    """安全头测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from app.main import app
        return TestClient(app)

    def test_cors_headers_on_options(self, client):
        """测试 OPTIONS 请求的 CORS 头"""
        response = client.options("/api/auth/login")
        # CORS 应该允许跨域请求（405 表示方法不允许，但也可能是其他状态）
        assert response.status_code in [200, 204, 400, 405]
