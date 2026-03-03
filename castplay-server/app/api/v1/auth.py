"""
Auth API Routes - 认证相关接口 (FastAPI 版本)
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.database import get_db
from app.core.config import settings
from app.api.deps import get_current_user
from app.models.device import Device

logger = logging.getLogger(__name__)
router = APIRouter()

# 密码加密上下文 - 使用 pbkdf2_sha256 避免 bcrypt 版本兼容问题
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


# ============= Pydantic 模型 =============

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 86400
    user: Optional[dict] = None


class RefreshRequest(BaseModel):
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str


class ApiKeyResponse(BaseModel):
    device_id: int
    device_name: str
    api_key: str


# ============= 简化用户存储（生产环境应使用数据库） =============

def _get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def _verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# 默认管理员账户
ADMIN_USERS = {
    'admin': {
        'password_hash': _get_password_hash('castplay2024'),
        'role': 'admin'
    }
}


def _create_token(user_id: str, token_type: str, expires_delta: timedelta) -> str:
    """创建 JWT Token"""
    expire = datetime.utcnow() + expires_delta
    payload = {
        "user_id": user_id,
        "type": token_type,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


# ============= API 端点 =============

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """用户登录"""
    user = ADMIN_USERS.get(request.username)

    if not user or not _verify_password(request.password, user['password_hash']):
        logger.warning(f"Failed login attempt for user: {request.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # 生成 Token
    access_token = _create_token(
        request.username,
        "access",
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)  # 24 hours
    )
    refresh_token = _create_token(
        request.username,
        "refresh",
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )

    logger.info(f"User {request.username} logged in successfully")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            'username': request.username,
            'role': user['role']
        }
    )


@router.post("/refresh")
async def refresh_token(request: RefreshRequest):
    """刷新 Token"""
    try:
        payload = jwt.decode(
            request.refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )

        user_id = payload.get("user_id")
        if user_id not in ADMIN_USERS:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        # 生成新的 access token
        new_access_token = _create_token(
            user_id,
            "access",
            timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
        )

        return {
            "access_token": new_access_token,
            "token_type": "Bearer",
            "expires_in": 86400
        }

    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )


@router.get("/me")
async def get_me(current_user: str = Depends(get_current_user)):
    """获取当前用户信息"""
    user = ADMIN_USERS.get(current_user)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {
        "username": current_user,
        "role": user['role']
    }


@router.post("/change-password")
async def change_password(
    request: PasswordChangeRequest,
    current_user: str = Depends(get_current_user)
):
    """修改密码"""
    if len(request.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters"
        )

    user = ADMIN_USERS.get(current_user)

    if not user or not _verify_password(request.old_password, user['password_hash']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid old password"
        )

    # 更新密码
    ADMIN_USERS[current_user]['password_hash'] = _get_password_hash(
        request.new_password)
    logger.info(f"User {current_user} changed password")

    return {"message": "Password changed successfully"}


# ============= 设备 API Key 管理 =============

@router.post("/device/{device_id}/api-key", response_model=ApiKeyResponse)
async def generate_device_api_key(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """为设备生成 API Key"""
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    api_key = device.generate_api_key()
    await db.commit()

    logger.info(f"Generated API key for device {device.device_id}")

    return ApiKeyResponse(
        device_id=device.id,
        device_name=device.device_name,
        api_key=api_key
    )


@router.delete("/device/{device_id}/api-key")
async def revoke_device_api_key(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """撤销设备 API Key"""
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    device.api_key = None
    await db.commit()

    logger.info(f"Revoked API key for device {device.device_id}")

    return {"message": "API key revoked"}
