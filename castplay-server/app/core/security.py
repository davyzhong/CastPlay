"""
Security Module - JWT Authentication & Authorization

提供 JWT Token 生成、验证和用户认证功能
"""
from datetime import datetime, timedelta
from typing import Optional, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core import settings


# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer 认证
bearer_scheme = HTTPBearer(auto_error=False)


class TokenData(BaseModel):
    """Token 数据模型"""
    user_id: Optional[int] = None
    username: Optional[str] = None
    token_type: str = "access"


class TokenPair(BaseModel):
    """Token 对模型"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)


def create_token(
    data: dict,
    token_type: str = "access",
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    创建 JWT Token

    Args:
        data: Token 载荷数据
        token_type: Token 类型 (access/refresh)
        expires_delta: 过期时间增量

    Returns:
        JWT Token 字符串
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    elif token_type == "refresh":
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": token_type
    })

    return jwt.encode(
        to_encode,
        settings.jwt_secret,
        algorithm=settings.JWT_ALGORITHM
    )


def create_access_token(user_id: int, username: str) -> str:
    """创建访问 Token"""
    return create_token(
        data={"sub": str(user_id), "username": username},
        token_type="access"
    )


def create_refresh_token(user_id: int, username: str) -> str:
    """创建刷新 Token"""
    return create_token(
        data={"sub": str(user_id), "username": username},
        token_type="refresh"
    )


def create_token_pair(user_id: int, username: str) -> TokenPair:
    """创建 Token 对（访问 + 刷新）"""
    return TokenPair(
        access_token=create_access_token(user_id, username),
        refresh_token=create_refresh_token(user_id, username)
    )


def verify_token(token: str, expected_type: str = "access") -> Optional[TokenData]:
    """
    验证 JWT Token

    Args:
        token: JWT Token 字符串
        expected_type: 期望的 Token 类型

    Returns:
        TokenData 或 None
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.JWT_ALGORITHM]
        )

        # 验证 Token 类型
        token_type = payload.get("type", "access")
        if token_type != expected_type:
            return None

        user_id = payload.get("sub")
        username = payload.get("username")

        if user_id is None:
            return None

        return TokenData(
            user_id=int(user_id),
            username=username,
            token_type=token_type
        )
    except JWTError:
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        bearer_scheme)
) -> TokenData:
    """
    获取当前用户（依赖注入）

    Usage:
        @router.get("/me")
        async def get_me(current_user: TokenData = Depends(get_current_user)):
            ...
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_exception

    token_data = verify_token(credentials.credentials, "access")
    if token_data is None:
        raise credentials_exception

    return token_data


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        bearer_scheme)
) -> Optional[TokenData]:
    """
    获取当前用户（可选，不强制登录）
    """
    if credentials is None:
        return None

    return verify_token(credentials.credentials, "access")


# === API Key 认证（用于设备端） ===

async def verify_api_key(api_key: str) -> bool:
    """验证 API Key"""
    # 这里可以从数据库查询设备的 API Key
    # 简化实现：直接返回 True
    return bool(api_key)
