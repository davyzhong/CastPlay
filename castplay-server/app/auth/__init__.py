"""
认证模块 - JWT + API Key 双模式

功能：
- JWT Token: 管理后台用户认证
- API Key: 播放端设备认证
- 可选：开发模式跳过认证
"""
import functools
import logging
from datetime import datetime, timedelta
from typing import Optional, Callable

import jwt
from flask import request, jsonify, current_app, g
from werkzeug.security import generate_password_hash, check_password_hash

logger = logging.getLogger(__name__)


# ============= JWT 认证 (管理后台) =============

def generate_token(user_id: str, expires_hours: int = 24) -> str:
    """
    生成 JWT Token

    Args:
        user_id: 用户标识
        expires_hours: 过期时间（小时）

    Returns:
        JWT Token 字符串
    """
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=expires_hours),
        'iat': datetime.utcnow(),
        'type': 'access'
    }
    return jwt.encode(
        payload,
        current_app.config['JWT_SECRET_KEY'],
        algorithm='HS256'
    )


def generate_refresh_token(user_id: str, expires_days: int = 7) -> str:
    """生成刷新 Token"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=expires_days),
        'iat': datetime.utcnow(),
        'type': 'refresh'
    }
    return jwt.encode(
        payload,
        current_app.config['JWT_SECRET_KEY'],
        algorithm='HS256'
    )


def verify_token(token: str, token_type: str = 'access') -> Optional[dict]:
    """
    验证 JWT Token

    Args:
        token: JWT Token 字符串
        token_type: Token 类型 ('access' 或 'refresh')

    Returns:
        Token payload 或 None（验证失败）
    """
    try:
        payload = jwt.decode(
            token,
            current_app.config['JWT_SECRET_KEY'],
            algorithms=['HS256']
        )
        if payload.get('type') != token_type:
            logger.warning(
                f"Token type mismatch: expected {token_type}, got {payload.get('type')}")
            return None
        return payload
    except jwt.ExpiredSignatureError:
        logger.debug("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None


def jwt_required(f: Callable) -> Callable:
    """
    JWT 认证装饰器 - 用于管理后台 API

    使用方式：
        @bp.route('/api/resource')
        @jwt_required
        def get_resource():
            user_id = g.current_user
            ...
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        # 开发模式跳过认证
        if _should_skip_auth():
            g.current_user = 'dev_user'
            return f(*args, **kwargs)

        token = _extract_token_from_header()

        if not token:
            return jsonify({'error': 'Missing authorization token'}), 401

        payload = verify_token(token, 'access')
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401

        g.current_user = payload.get('user_id')
        return f(*args, **kwargs)

    return decorated


def jwt_optional(f: Callable) -> Callable:
    """
    可选 JWT 认证装饰器 - 有 Token 则验证，无 Token 也允许访问
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_token_from_header()

        if token:
            payload = verify_token(token, 'access')
            if payload:
                g.current_user = payload.get('user_id')
            else:
                g.current_user = None
        else:
            g.current_user = None

        return f(*args, **kwargs)

    return decorated


# ============= API Key 认证 (播放端) =============

def verify_device_api_key(api_key: str):
    """
    验证设备 API Key

    Args:
        api_key: 设备 API Key

    Returns:
        Device 对象或 None
    """
    if not api_key:
        return None

    # 延迟导入避免循环依赖
    from app.models import Device
    return Device.query.filter_by(api_key=api_key).first()


def device_auth_required(f: Callable) -> Callable:
    """
    设备认证装饰器 - 用于播放端 API

    使用方式：
        @bp.route('/player/init')
        @device_auth_required
        def player_init():
            device = g.current_device
            ...
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        # 开发模式跳过认证
        if _should_skip_auth():
            g.current_device = None
            return f(*args, **kwargs)

        api_key = request.headers.get('X-API-Key')

        if not api_key:
            return jsonify({'error': 'Missing API key'}), 401

        device = verify_device_api_key(api_key)
        if not device:
            return jsonify({'error': 'Invalid API key'}), 401

        g.current_device = device
        return f(*args, **kwargs)

    return decorated


def device_auth_optional(f: Callable) -> Callable:
    """
    可选设备认证装饰器 - 有 API Key 则验证，无则允许访问
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')

        if api_key:
            device = verify_device_api_key(api_key)
            g.current_device = device
        else:
            g.current_device = None

        return f(*args, **kwargs)

    return decorated


# ============= 密码工具 =============

def hash_password(password: str) -> str:
    """生成密码哈希"""
    return generate_password_hash(password, method='pbkdf2:sha256')


def verify_password(password: str, password_hash: str) -> bool:
    """验证密码"""
    return check_password_hash(password_hash, password)


# ============= 辅助函数 =============

def _extract_token_from_header() -> Optional[str]:
    """从请求头提取 Token"""
    auth_header = request.headers.get('Authorization')

    if auth_header and auth_header.startswith('Bearer '):
        return auth_header.split(' ', 1)[1]

    return None


def _should_skip_auth() -> bool:
    """检查是否应该跳过认证（开发模式）"""
    return (
        current_app.config.get('DEBUG', False) and
        current_app.config.get('SKIP_AUTH', False)
    )


# ============= 导出 =============

__all__ = [
    'generate_token',
    'generate_refresh_token',
    'verify_token',
    'jwt_required',
    'jwt_optional',
    'verify_device_api_key',
    'device_auth_required',
    'device_auth_optional',
    'hash_password',
    'verify_password',
]
