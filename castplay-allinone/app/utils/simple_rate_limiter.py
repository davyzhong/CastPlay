"""
简单速率限制器 - 替代 SlowAPI
适用于内网小规模场景
"""
from fastapi import Depends, HTTPException, status, Request
from collections import defaultdict
import time


class SimpleRateLimiter:
    """
    简单速率限制器

    基于内存的滑动窗口实现，适用于内网小规模场景
    """

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """
        初始化速率限制器

        Args:
            max_requests: 时间窗口内最大请求数
            window_seconds: 时间窗口大小（秒）
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, list[float]] = defaultdict(list)

    async def __call__(self, request: Request):
        """
        FastAPI 依赖调用

        Args:
            request: FastAPI 请求对象

        Raises:
            HTTPException: 当请求超过限制时抛出 429 异常
        """
        client_ip = request.client.host
        now = time.time()

        # 清理过期记录
        self.requests[client_ip] = [
            t for t in self.requests[client_ip]
            if now - t < self.window_seconds
        ]

        # 检查是否超过限制
        if len(self.requests[client_ip]) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"请求过于频繁，请稍后再试（限制：{self.max_requests}次/{self.window_seconds}秒）"
            )

        self.requests[client_ip].append(now)


# 全局实例
rate_limiter = SimpleRateLimiter(max_requests=100, window_seconds=60)
