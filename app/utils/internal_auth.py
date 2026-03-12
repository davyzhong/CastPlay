"""
内部 API 认证模块

P0-5 修复：为敏感接口添加身份认证保护
用于保护 /cleanup 和 /heartbeat 等内部接口
"""
import os
from fastapi import Depends, HTTPException, status, Header
from typing import Optional


# 从环境变量获取内部 API 密钥
# 如果未设置，则使用默认值（仅用于开发环境，生产环境必须设置）
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "")


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
        HTTPException: 认证失败时抛出 401 错误
    """
    # 如果未配置内部 API 密钥，跳过认证（仅用于开发环境）
    if not INTERNAL_API_KEY:
        import logging
        logging.getLogger(__name__).warning(
            "INTERNAL_API_KEY not configured, skipping internal API authentication. "
            "This is insecure for production environments!"
        )
        return "no-key-configured"

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

    如果配置了密钥则验证，否则返回 True

    Returns:
        True 如果验证通过或未配置密钥
    """
    if not INTERNAL_API_KEY:
        return True

    return x_internal_key == INTERNAL_API_KEY
