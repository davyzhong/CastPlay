"""
简单速率限制器 - 替代 SlowAPI
适用于内网小规模场景

P0-4 修复：添加容量限制和 LRU 淘汰机制
"""
from fastapi import Depends, HTTPException, status, Request
from collections import OrderedDict
import time
import threading


class SimpleRateLimiter:
    """
    简单速率限制器

    基于内存的滑动窗口实现，适用于内网小规模场景
    P0-4 修复：添加最大客户端数量限制和 LRU 淘汰
    """

    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 60,
        max_clients: int = 10000,
        cleanup_interval: int = 300  # 5 分钟清理一次
    ):
        """
        初始化速率限制器

        Args:
            max_requests: 时间窗口内最大请求数
            window_seconds: 时间窗口大小（秒）
            max_clients: 最大客户端数量（P0-4 修复：容量限制）
            cleanup_interval: 定期清理间隔（秒）
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.max_clients = max_clients
        self.cleanup_interval = cleanup_interval
        # P0-4 修复：使用 OrderedDict 实现 LRU
        self._requests: OrderedDict[str, list[float]] = OrderedDict()
        self._lock = threading.Lock()
        self._last_cleanup = time.time()

    def _cleanup_expired(self, now: float) -> None:
        """清理过期的请求记录"""
        window_start = now - self.window_seconds

        # 清理每个 IP 的过期记录
        expired_ips = []
        for ip, timestamps in self._requests.items():
            # 过滤掉过期的记录
            valid_timestamps = [t for t in timestamps if t > window_start]
            if valid_timestamps:
                self._requests[ip] = valid_timestamps
            else:
                expired_ips.append(ip)

        # 删除没有有效记录的 IP
        for ip in expired_ips:
            del self._requests[ip]

    def _evict_lru_if_needed(self) -> None:
        """P0-4 修复：如果超过容量限制，使用 LRU 淘汰最旧的条目"""
        while len(self._requests) > self.max_clients:
            # OrderedDict 的 popitem(last=False) 移除最旧的条目
            self._requests.popitem(last=False)

    async def __call__(self, request: Request):
        """
        FastAPI 依赖调用

        Args:
            request: FastAPI 请求对象

        Raises:
            HTTPException: 当请求超过限制时抛出 429 异常
        """
        client_ip = request.client.host if request.client else "0.0.0.0"
        now = time.time()

        with self._lock:
            # 定期清理过期记录（每 5 分钟）
            if now - self._last_cleanup > self.cleanup_interval:
                self._cleanup_expired(now)
                self._last_cleanup = now

            # 清理当前 IP 的过期记录
            if client_ip in self._requests:
                window_start = now - self.window_seconds
                self._requests[client_ip] = [
                    t for t in self._requests[client_ip]
                    if t > window_start
                ]
                # 移动到末尾（LRU）
                self._requests.move_to_end(client_ip)

            # 检查是否超过限制
            if client_ip in self._requests and len(self._requests[client_ip]) >= self.max_requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"请求过于频繁，请稍后再试（限制：{self.max_requests}次/{self.window_seconds}秒）"
                )

            # 添加新记录
            if client_ip not in self._requests:
                self._requests[client_ip] = []
            self._requests[client_ip].append(now)

            # P0-4 修复：检查容量限制并淘汰
            self._evict_lru_if_needed()

    def get_client_count(self) -> int:
        """获取当前跟踪的客户端数量（用于监控）"""
        with self._lock:
            return len(self._requests)

    def force_cleanup(self) -> int:
        """强制清理所有过期记录，返回清理后的客户端数量"""
        now = time.time()
        with self._lock:
            self._cleanup_expired(now)
            self._last_cleanup = now
            return len(self._requests)


# 全局实例
rate_limiter = SimpleRateLimiter(max_requests=100, window_seconds=60, max_clients=10000)
