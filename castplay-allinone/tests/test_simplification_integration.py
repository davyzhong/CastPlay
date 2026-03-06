"""
集成测试 - 验证简化优化功能
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.utils.simple_rate_limiter import SimpleRateLimiter

client = TestClient(app)


class TestSimplificationFeatures:
    """测试简化优化功能"""

    def test_health_endpoint(self):
        """测试健康检查端点"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_rate_limiter_basic(self):
        """测试简单限流器基本功能"""
        from unittest.mock import Mock
        limiter = SimpleRateLimiter(max_requests=5, window_seconds=1)

        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"

        # 前 5 次应该成功
        for i in range(5):
            import asyncio
            asyncio.run(limiter(mock_request))

        # 第 6 次应该被限制
        with pytest.raises(Exception) as exc_info:
            import asyncio
            asyncio.run(limiter(mock_request))

        assert exc_info.value.status_code == 429

    def test_scheduler_import(self):
        """测试 APScheduler 导入成功"""
        from app.scheduler import scheduler, submit_ppt_conversion
        assert scheduler is not None
        assert callable(submit_ppt_conversion)

    def test_config_simplified_settings(self):
        """测试简化后的配置"""
        from app.config import settings

        # 测试 JWT 密钥 property
        assert hasattr(settings, 'SECRET_KEY')
        assert isinstance(settings.SECRET_KEY, str)

        # 测试 CORS property
        assert hasattr(settings, 'CORS_ORIGINS')
        assert isinstance(settings.CORS_ORIGINS, list)

        # 测试日志级别 property
        assert hasattr(settings, 'LOG_LEVEL')
        assert settings.LOG_LEVEL in ['DEBUG', 'INFO', 'WARNING', 'ERROR']
