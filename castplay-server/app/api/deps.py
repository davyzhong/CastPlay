"""CastPlay Server - API Dependencies"""
from typing import Optional
from datetime import datetime

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt, JWTError

from app.database import get_db
from app.core.config import settings
from app.models.device import Device

# HTTP Bearer 认证
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> str:
    """获取当前认证用户

    通过 JWT Token 验证用户身份
    """
    # 开发环境跳过认证
    if settings.DEBUG and not credentials:
        return "dev_user"

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        # 检查 token 类型
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )

        # 检查过期时间
        exp = payload.get("exp")
        if exp and datetime.utcnow().timestamp() > exp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )

        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )

        return user_id

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_device_by_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db)
) -> Optional[Device]:
    """通过 API Key 获取设备

    用于播放端设备认证
    """
    if not x_api_key:
        return None

    result = await db.execute(
        select(Device).where(Device.api_key == x_api_key)
    )
    device = result.scalar_one_or_none()

    if device:
        # 更新最后在线时间
        device.last_online = datetime.utcnow()
        device.status = "online"
        await db.commit()

    return device


async def require_device_auth(
    device: Optional[Device] = Depends(get_device_by_api_key)
) -> Device:
    """要求设备认证"""
    if not device:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "X-API-Key"},
        )
    return device


def require_auth():
    """认证装饰器工厂 - 返回依赖函数"""
    return Depends(get_current_user)
