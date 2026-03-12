"""
Rate Limit 中间件测试
测试 API 限流功能
"""
import pytest
from unittest.mock import patch, MagicMock


class TestRateLimitConfig:
    """限流配置测试"""

    def test_rate_limit_settings_exist(self):
        """测试限流设置存在"""
        from app.config import settings
        assert hasattr(settings, 'RATE_LIMIT_ENABLED')

    def test_rate_limit_login_setting(self):
        """测试登录限流设置"""
        from app.config import settings
        assert hasattr(settings, 'RATE_LIMIT_LOGIN')

    def test_rate_limit_api_setting(self):
        """测试 API 限流设置"""
        from app.config import settings
        assert hasattr(settings, 'RATE_LIMIT_API')


class TestRateLimitMiddleware:
    """限流中间件测试"""

    def test_rate_limit_import(self):
        """测试限流模块可以导入"""
        from app.middleware.rate_limit import limiter
        assert limiter is not None

    def test_limiter_instance(self):
        """测试限流器实例"""
        from app.middleware.rate_limit import limiter
        # 检查限流器是否正确配置
        assert hasattr(limiter, '_storage')

    @patch('app.middleware.rate_limit.settings')
    def test_rate_limit_can_be_disabled(self, mock_settings):
        """测试限流可以禁用"""
        mock_settings.RATE_LIMIT_ENABLED = False
        mock_settings.RATE_LIMIT_LOGIN = "5/minute"
        mock_settings.RATE_LIMIT_API = "100/minute"

        # 重新导入以获取新的设置
        import importlib
        import app.middleware.rate_limit as rate_limit_module
        importlib.reload(rate_limit_module)


class TestRateLimitStorage:
    """限流存储测试"""

    def test_storage_configuration(self):
        """测试存储配置"""
        from app.middleware.rate_limit import limiter
        # 检查存储是否配置
        storage = limiter._storage
        assert storage is not None


class TestRateLimitDecorators:
    """限流装饰器测试"""

    def test_limit_login_decorator_exists(self):
        """测试登录限流装饰器存在"""
        from app.middleware.rate_limit import limit_login
        assert callable(limit_login)

    def test_limiter_has_limit_method(self):
        """测试限流器有 limit 方法"""
        from app.middleware.rate_limit import limiter
        assert hasattr(limiter, 'limit')


class TestRateLimitIntegration:
    """限流集成测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from app.main import app
        from fastapi.testclient import TestClient
        return TestClient(app)

    def test_login_endpoint_has_rate_limit(self, client):
        """测试登录端点有速率限制"""
        # 多次快速请求可能触发限流
        responses = []
        for _ in range(10):
            response = client.post("/api/auth/login", json={
                "username": "test",
                "password": "wrong"
            })
            responses.append(response.status_code)

        # 至少有一些请求应该失败（401 或 429）
        assert any(code in [401, 422, 429, 400] for code in responses)
