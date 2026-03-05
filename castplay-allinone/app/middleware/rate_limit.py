"""
请求速率限制中间件
使用 slowapi 实现 API 速率限制，防止暴力破解和 DDoS 攻击
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from typing import Callable

from app.config import settings
from app.utils.logger import logger


def get_client_identifier(request: Request) -> str:
    """
    获取客户端标识符（用于速率限制）

    优先使用 X-Forwarded-For 头（反向代理场景），
    其次使用 X-Real-IP，最后使用远程地址

    Args:
        request: FastAPI 请求对象

    Returns:
        客户端标识符字符串
    """
    # 检查 X-Forwarded-For 头（可能包含多个 IP，取第一个）
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    # 检查 X-Real-IP 头
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # 使用认证用户 ID（如果已登录）
    # 注意：这需要在认证后才能使用
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"

    # 最后使用远程地址
    return get_remote_address(request)


# 创建速率限制器
limiter = Limiter(
    key_func=get_client_identifier,
    default_limits=[settings.RATE_LIMIT_API] if settings.RATE_LIMIT_ENABLED else [],
    enabled=settings.RATE_LIMIT_ENABLED,
    storage_uri="memory://",  # 使用内存存储，生产环境建议使用 Redis
)


def setup_rate_limit(app):
    """
    配置速率限制

    Args:
        app: FastAPI 应用实例
    """
    if not settings.RATE_LIMIT_ENABLED:
        logger.info("Rate limiting is disabled")
        return

    # 设置速率限制器状态
    app.state.limiter = limiter

    # 添加速率限制超出处理器
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # 添加 SlowAPI 中间件
    app.add_middleware(SlowAPIMiddleware)

    logger.info(f"Rate limiting enabled: API={settings.RATE_LIMIT_API}, Login={settings.RATE_LIMIT_LOGIN}")


# 常用速率限制装饰器
def limit_login():
    """登录接口速率限制"""
    return limiter.limit(settings.RATE_LIMIT_LOGIN)


def limit_api():
    """普通 API 速率限制"""
    return limiter.limit(settings.RATE_LIMIT_API)


def limit_strict():
    """严格速率限制（用于敏感操作）"""
    return limiter.limit("3/minute")


def limit_loose():
    """宽松速率限制（用于只读操作）"""
    return limiter.limit("200/minute")
