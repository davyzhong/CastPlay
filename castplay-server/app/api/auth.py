"""
Auth API Routes - 认证相关接口
"""
import logging
from flask import Blueprint, request, jsonify
from app import db
from app.auth import (
    generate_token,
    generate_refresh_token,
    verify_token,
    hash_password,
    verify_password,
    jwt_required
)
from app.models import Device

logger = logging.getLogger(__name__)

bp = Blueprint('auth', __name__)

# ============= 简化用户存储（生产环境应使用数据库） =============
# 默认管理员账户（首次使用时应修改密码）
ADMIN_USERS = {
    'admin': {
        'password_hash': hash_password('castplay2024'),  # 默认密码
        'role': 'admin'
    }
}


@bp.route('/login', methods=['POST'])
def login():
    """
    用户登录

    Request Body:
        {
            "username": "admin",
            "password": "password"
        }

    Response:
        {
            "access_token": "...",
            "refresh_token": "...",
            "token_type": "Bearer",
            "expires_in": 86400
        }
    """
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Missing request body'}), 400

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    # 验证用户
    user = ADMIN_USERS.get(username)
    if not user or not verify_password(password, user['password_hash']):
        logger.warning(f"Failed login attempt for user: {username}")
        return jsonify({'error': 'Invalid credentials'}), 401

    # 生成 Token
    access_token = generate_token(username, expires_hours=24)
    refresh_token = generate_refresh_token(username, expires_days=7)

    logger.info(f"User {username} logged in successfully")

    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer',
        'expires_in': 86400,  # 24 hours
        'user': {
            'username': username,
            'role': user['role']
        }
    }), 200


@bp.route('/refresh', methods=['POST'])
def refresh_token():
    """
    刷新 Token

    Request Body:
        {
            "refresh_token": "..."
        }

    Response:
        {
            "access_token": "...",
            "token_type": "Bearer",
            "expires_in": 86400
        }
    """
    data = request.get_json()

    if not data or not data.get('refresh_token'):
        return jsonify({'error': 'Refresh token required'}), 400

    payload = verify_token(data['refresh_token'], 'refresh')
    if not payload:
        return jsonify({'error': 'Invalid or expired refresh token'}), 401

    user_id = payload.get('user_id')
    if user_id not in ADMIN_USERS:
        return jsonify({'error': 'User not found'}), 401

    # 生成新的 access token
    new_access_token = generate_token(user_id, expires_hours=24)

    return jsonify({
        'access_token': new_access_token,
        'token_type': 'Bearer',
        'expires_in': 86400
    }), 200


@bp.route('/me', methods=['GET'])
@jwt_required
def get_current_user():
    """
    获取当前用户信息
    """
    from flask import g
    username = g.current_user
    user = ADMIN_USERS.get(username)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'username': username,
        'role': user['role']
    }), 200


@bp.route('/change-password', methods=['POST'])
@jwt_required
def change_password():
    """
    修改密码

    Request Body:
        {
            "old_password": "...",
            "new_password": "..."
        }
    """
    from flask import g
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Missing request body'}), 400

    old_password = data.get('old_password')
    new_password = data.get('new_password')

    if not old_password or not new_password:
        return jsonify({'error': 'Old and new password required'}), 400

    if len(new_password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400

    username = g.current_user
    user = ADMIN_USERS.get(username)

    if not user or not verify_password(old_password, user['password_hash']):
        return jsonify({'error': 'Invalid old password'}), 401

    # 更新密码
    ADMIN_USERS[username]['password_hash'] = hash_password(new_password)
    logger.info(f"User {username} changed password")

    return jsonify({'message': 'Password changed successfully'}), 200


# ============= 设备 API Key 管理 =============

@bp.route('/device/<int:device_id>/api-key', methods=['POST'])
@jwt_required
def generate_device_api_key(device_id):
    """
    为设备生成 API Key

    Response:
        {
            "device_id": 1,
            "api_key": "..."
        }
    """
    device = Device.query.get_or_404(device_id)

    api_key = device.generate_api_key()
    db.session.commit()

    logger.info(f"Generated API key for device {device.device_id}")

    return jsonify({
        'device_id': device.id,
        'device_name': device.device_name,
        'api_key': api_key
    }), 200


@bp.route('/device/<int:device_id>/api-key', methods=['DELETE'])
@jwt_required
def revoke_device_api_key(device_id):
    """
    撤销设备 API Key
    """
    device = Device.query.get_or_404(device_id)

    device.api_key = None
    db.session.commit()

    logger.info(f"Revoked API key for device {device.device_id}")

    return jsonify({'message': 'API key revoked'}), 200
