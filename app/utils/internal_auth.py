"""
内部 API 认证模块

P0-5 修复：为敏感接口添加身份认证保护
用于保护 /cleanup 和 /heartbeat 等内部接口
"""
import os
import warnings
from fastapi import Depends, HTTPException, status, Header
from typing import Optional
from loguru import logger

from app.config import settings


# 从环境变量获取内部 API 密钥
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "")

# 检查生产环境配置
if settings.ENVIRONMENT == "production" and not INTERNAL_API_KEY:
    warnings.warn(
        "生产环境必须配置 INTERNAL_API_KEY 环境变量！内部 API 将拒绝所有请求。",
        UserWarning
    )


def verify_internal_api_key(
    x_internal_key: Optional[str] = Header(None, alias="X-Internal-Key")
) -> str:
    """
    验证内部 API 密钥

    通过 X-Internal-Key 头传递密钥进行认证

    Args:
        x_internal_key: 请求头中的密钥

    Returns:
        验证通过返回密钥

    Raises:
        HTTPException: 认证失败时抛出 401 或 503 错误
    """
    # 生产环境必须配置密钥
    if settings.ENVIRONMENT == "production":
        if not INTERNAL_API_KEY:
            logger.error("INTERNAL_API_KEY not configured in production environment")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Internal API authentication not configured"
            )

        if not x_internal_key or x_internal_key != INTERNAL_API_KEY:
            logger.warning(f"Invalid internal API key attempt from {x_internal_key}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing internal API key",
                headers={"WWW-Authenticate": "Internal-Key"}
            )

        return x_internal_key

    # 开发环境：未配置密钥时允许访问但记录警告
    if not INTERNAL_API_KEY:
        logger.debug(
            "INTERNAL_API_KEY not configured, allowing access (development mode)"
        )
        return "dev-mode-no-key"

    # 开发环境：配置了密钥则必须验证
    if not x_internal_key or x_internal_key != INTERNAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing internal API key",
            headers={"WWW-Authenticate": "Internal-Key"}
        )

    return x_internal_key


def verify_internal_api_key_optional(
    x_internal_key: Optional[str] = Header(None, alias="X-Internal-Key")
) -> bool:
    """
    可选的内部 API 密钥验证

    如果配置了密钥则验证，开发环境未配置时返回 True

    Returns:
        True 如果验证通过或开发环境未配置密钥
    """
    # 生产环境必须验证
    if settings.ENVIRONMENT == "production":
        if not INTERNAL_API_KEY:
            return False
        return x_internal_key == INTERNAL_API_KEY

    # 开发环境
    if not INTERNAL_API_KEY:
        return True

    return x_internal_key == INTERNAL_API_KEY
