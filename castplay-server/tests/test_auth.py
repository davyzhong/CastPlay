"""
Auth API Tests (Flask 版本)

测试认证相关的 API 端点
注意：系统使用内存存储的 admin 用户，不是数据库 User 模型
"""
import pytest


class TestAuthLogin:
    """测试登录 API"""

    def test_login_success(self, client):
        """测试登录成功 - 使用内置 admin 账户"""
        response = client.post(
            '/api/v1/auth/login',
            json={
                'username': 'admin',
                'password': 'castplay2024'
            }
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert data['token_type'] == 'Bearer'

    def test_login_invalid_credentials(self, client):
        """测试登录失败 - 错误密码"""
        response = client.post(
            '/api/v1/auth/login',
            json={
                'username': 'admin',
                'password': 'wrong_password'
            }
        )

        assert response.status_code == 401

    def test_login_user_not_found(self, client):
        """测试登录失败 - 用户不存在"""
        response = client.post(
            '/api/v1/auth/login',
            json={
                'username': 'nonexistent',
                'password': 'anypassword'
            }
        )

        assert response.status_code == 401

    def test_login_missing_username(self, client):
        """测试登录失败 - 缺少用户名"""
        response = client.post(
            '/api/v1/auth/login',
            json={
                'password': 'anypassword'
            }
        )

        assert response.status_code == 400

    def test_login_missing_password(self, client):
        """测试登录失败 - 缺少密码"""
        response = client.post(
            '/api/v1/auth/login',
            json={
                'username': 'admin'
            }
        )

        assert response.status_code == 400


class TestAuthToken:
    """测试 Token 相关 API"""

    def test_refresh_token(self, client):
        """测试刷新 Token"""
        # 先登录获取 token
        login_response = client.post(
            '/api/v1/auth/login',
            json={
                'username': 'admin',
                'password': 'castplay2024'
            }
        )

        if login_response.status_code != 200:
            pytest.skip('Login failed, skipping refresh test')

        refresh_token = login_response.get_json().get('refresh_token')
        if not refresh_token:
            pytest.skip('No refresh token returned')

        # 刷新 token
        response = client.post(
            '/api/v1/auth/refresh',
            json={'refresh_token': refresh_token}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'access_token' in data

    def test_refresh_token_invalid(self, client):
        """测试使用无效的 refresh token"""
        response = client.post(
            '/api/v1/auth/refresh',
            json={'refresh_token': 'invalid_token'}
        )

        assert response.status_code == 401
