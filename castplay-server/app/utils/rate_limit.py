"""
Rate Limiting Configuration

使用 Flask-Limiter 实现 API 限流保护，防止滥用和 DDoS 攻击。

限流策略：
- 默认: 200 次/分钟, 50 次/秒
- 登录 API: 5 次/分钟 (防止暴力破解)
- 上传 API: 10 次/分钟 (防止存储滥用)
- 播放端 API: 更宽松的限制 (设备同步需要)
"""
import logging
from functools import wraps
from typing import Optional, Callable

from flask import Flask, request, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

logger = logging.getLogger(__name__)

# 创建 Limiter 实例（延迟初始化）
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per minute", "50 per second"],
    storage_uri="memory://",  # 默认内存存储，生产环境可改为 Redis
    strategy="fixed-window",
)


def init_limiter(app: Flask) -> None:
    """
    初始化限流器

    Args:
        app: Flask 应用实例
    """
    # 从配置获取 Redis URL（如果有）
    redis_url = app.config.get('REDIS_URL')
    if redis_url:
        limiter._storage_uri = redis_url
        logger.info(f"Rate limiter using Redis: {redis_url}")
    else:
        logger.info("Rate limiter using in-memory storage")

    limiter.init_app(app)

    # 注册错误处理器
    @app.errorhandler(429)
    def ratelimit_handler(e):
        """处理限流错误"""
        return {
            'error': 'Too Many Requests',
            'message': f'请求过于频繁，请稍后重试。限制: {e.description}',
            'retry_after': e.retry_after
        }, 429


# 预定义的限流装饰器
def limit_login(f: Callable) -> Callable:
    """登录 API 限流: 5 次/分钟"""
    return limiter.limit("5 per minute")(f)


def limit_upload(f: Callable) -> Callable:
    """上传 API 限流: 10 次/分钟"""
    return limiter.limit("10 per minute")(f)


def limit_player(f: Callable) -> Callable:
    """播放端 API 限流: 60 次/分钟 (更宽松)"""
    return limiter.limit("60 per minute")(f)


def limit_register(f: Callable) -> Callable:
    """设备注册限流: 10 次/分钟"""
    return limiter.limit("10 per minute")(f)


# 基于设备 ID 的限流（用于播放端）
def get_device_id() -> str:
    """获取设备 ID 作为限流 key"""
    # 尝试从请求参数获取
    device_id = request.args.get('device_id')
    if device_id:
        return f"device:{device_id}"

    # 尝试从 JSON body 获取
    if request.is_json:
        data = request.get_json(silent=True)
        if data and 'device_id' in data:
            return f"device:{data['device_id']}"

    # 回退到 IP 地址
    return get_remote_address()


def limit_by_device(limit_string: str) -> Callable:
    """
    基于设备 ID 的限流装饰器

    Usage:
        @limit_by_device("60 per minute")
        def my_api():
            ...
    """
    return limiter.limit(limit_string, key_func=get_device_id)
