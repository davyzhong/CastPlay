"""
安全工具模块
包含密码哈希、JWT Token 生成等安全相关功能
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码

    Args:
        plain_password: 明文密码
        hashed_password: 哈希后的密码

    Returns:
        密码是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    获取密码哈希值

    Args:
        password: 明文密码

    Returns:
        哈希后的密码
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建 JWT 访问令牌

    Args:
        data: 要编码的数据
        expires_delta: 过期时间增量

    Returns:
        JWT Token 字符串
    """
    to_encode = data.copy()

    # 添加签发时间 (iat) - JWT 标准声明，用于 token 唯一性和追踪
    now = datetime.utcnow()
    to_encode.update({"iat": now})

    # 添加过期时间 (exp)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.get_secret_key(), algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    解码 JWT 访问令牌

    Args:
        token: JWT Token 字符串

    Returns:
        解码后的数据，失败返回 None
    """
    if not token or not isinstance(token, str):
        return None

    try:
        payload = jwt.decode(token, settings.get_secret_key(), algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


# 别名，用于测试兼容
def decode_token(token: str) -> dict:
    """
    解码 JWT Token（测试用）

    Args:
        token: JWT Token 字符串

    Returns:
        解码后的数据

    Raises:
        Exception: Token 无效时抛出异常
    """
    payload = decode_access_token(token)
    if payload is None:
        raise Exception("Invalid token")
    return payload
