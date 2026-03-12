"""
测试简单速率限制器
"""
import pytest
from unittest.mock import AsyncMock, Mock
from app.utils.simple_rate_limiter import SimpleRateLimiter


class TestSimpleRateLimiter:
    """测试简单速率限制器"""

    def test_initialization(self):
        """测试初始化"""
        limiter = SimpleRateLimiter(max_requests=10, window_seconds=60)
        assert limiter.max_requests == 10
        assert limiter.window_seconds == 60

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """测试速率限制功能"""
        # 创建限制器：5 次/秒
        limiter = SimpleRateLimiter(max_requests=5, window_seconds=1)

        # Mock 请求对象
        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"

        # 前 5 次请求应该成功
        for i in range(5):
            await limiter(mock_request)

        # 第 6 次请求应该被限制
        with pytest.raises(Exception) as exc_info:
            await limiter(mock_request)

        assert exc_info.value.status_code == 429
        assert "请求过于频繁" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_window_reset(self):
        """测试时间窗口重置"""
        import time

        # 创建限制器：2 次/0.1 秒
        limiter = SimpleRateLimiter(max_requests=2, window_seconds=0.1)

        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"

        # 前 2 次请求成功
        await limiter(mock_request)
        await limiter(mock_request)

        # 等待窗口过期
        time.sleep(0.15)

        # 新请求应该再次成功
        await limiter(mock_request)  # 不应该抛出异常

    @pytest.mark.asyncio
    async def test_multiple_clients(self):
        """测试多个客户端独立计数"""
        limiter = SimpleRateLimiter(max_requests=2, window_seconds=60)

        # 客户端 1
        request1 = Mock()
        request1.client.host = "192.168.1.1"

        # 客户端 2
        request2 = Mock()
        request2.client.host = "192.168.1.2"

        # 客户端 1 发起 2 次请求
        await limiter(request1)
        await limiter(request1)

        # 客户端 2 的请求不应该受影响
        await limiter(request2)  # 应该成功

        # 客户端 1 的第 3 次请求应该被限制
        with pytest.raises(Exception):
            await limiter(request1)
