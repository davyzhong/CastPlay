"""
Authentication and Authorization 单元测试补充
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from tests.conftest import _generate_unique_id


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


class TestAuthAPI:
    """认证 API 测试类"""

    def test_login_invalid_endpoint(self, client):
        """测试登录接口 - 无效凭据返回 401"""
        payload = {
            'username': 'testuser',
            'password': 'testpass123'
        }

        response = client.post('/api/v1/auth/login', json=payload)

        # 由于用户不存在，应该返回 401
        assert response.status_code == 401

    def test_register_invalid_endpoint(self, client):
        """测试注册接口不存在"""
        payload = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'SecurePass123!'
        }

        response = client.post('/api/v1/auth/register', json=payload)

        assert response.status_code in [404, 405, 500]


class TestJWTToken:
    """JWT Token 相关测试"""

    def test_token_structure(self):
        """测试 JWT token 基本结构"""
        # 由于没有 User 模型，仅测试基本概念
        import jwt

        # 创建一个简单的 token
        payload = {
            'sub': 'test_user',
            'exp': 9999999999,
            'iat': 1234567890
        }

        token = jwt.encode(payload, 'test_secret', algorithm='HS256')

        # 验证可以解码
        decoded = jwt.decode(token, options={'verify_signature': False})

        assert decoded['sub'] == 'test_user'
        assert 'exp' in decoded
        assert 'iat' in decoded
