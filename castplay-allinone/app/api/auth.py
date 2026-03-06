"""
认证 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import timedelta

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserLogin, TokenResponse
from app.utils.security import verify_password, get_password_hash, create_access_token
from app.utils.logger import logger
from app.utils.simple_rate_limiter import rate_limiter

router = APIRouter()
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    获取当前用户（依赖注入）

    Args:
        credentials: HTTP 认证凭据
        db: 数据库会话

    Returns:
        当前用户对象

    Raises:
        HTTPException: 认证失败
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 解码 Token
    from app.utils.security import decode_access_token
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise credentials_exception

    # 获取用户 ID（Token 中存储为字符串，需要转换为整数）
    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise credentials_exception

    # 查询用户
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    注册新用户

    - **username**: 用户名（唯一）
    - **password**: 密码
    - **email**: 邮箱（可选）
    - **full_name**: 全名（可选）
    """
    # 检查用户名是否已存在
    existing = db.query(User).filter(
        User.username == user_data.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # 检查邮箱是否已存在
    if user_data.email:
        existing_email = db.query(User).filter(
            User.email == user_data.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

    # 创建新用户
    new_user = User(
        username=user_data.username,
        password_hash=get_password_hash(user_data.password),
        email=user_data.email,
        full_name=user_data.full_name
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(f"New user registered: {user_data.username}")
    return new_user


@router.post("/login", response_model=TokenResponse, dependencies=[Depends(rate_limiter)])
def login(request: Request, credentials: UserLogin, db: Session = Depends(get_db)):
    """
    用户登录

    - **username**: 用户名
    - **password**: 密码

    返回访问令牌

    注意：使用简单速率限制器（100 次/分钟）
    """
    # 查询用户
    user = db.query(User).filter(User.username == credentials.username).first()

    # 验证用户和密码
    if not user or not verify_password(credentials.password, user.password_hash):
        logger.warning(
            f"Failed login attempt for username: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # 创建访问令牌
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username}
    )

    logger.info(f"User logged in: {user.username}")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    获取当前用户信息

    需要认证
    """
    return current_user


@router.get("/users", response_model=list[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户列表

    需要超级管理员权限
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    users = db.query(User).offset(skip).limit(limit).all()
    return users
