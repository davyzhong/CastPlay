"""
认证 API 测试
"""
import pytest
from httpx import AsyncClient


class TestAuthAPI:
    """认证 API 测试类"""

    def test_register_user(self, client):
        """测试用户注册"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "password": "password123",
                "email": "newuser@example.com",
                "full_name": "New User"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "id" in data
        assert "password" not in data  # 确保密码不返回

    def test_register_duplicate_username(self, client, test_user):
        """测试重复用户名注册"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": test_user.username,
                "password": "password123",
                "email": "another@example.com"
            }
        )
        assert response.status_code == 400

    def test_register_duplicate_email(self, client, test_user):
        """测试重复邮箱注册"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "anotheruser",
                "password": "password123",
                "email": test_user.email
            }
        )
        assert response.status_code == 400

    def test_register_invalid_email(self, client):
        """测试无效邮箱格式"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "password": "password123",
                "email": "invalid-email"
            }
        )
        assert response.status_code == 422

    def test_register_weak_password(self, client):
        """测试弱密码"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "password": "123",  # 太短
                "email": "test@example.com"
            }
        )
        assert response.status_code == 422

    def test_login_success(self, client, test_user):
        """测试成功登录"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": test_user.username,
                "password": "testpass123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "user" in data

    def test_login_wrong_password(self, client, test_user):
        """测试错误密码登录"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": test_user.username,
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        """测试不存在的用户登录"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "nonexistent",
                "password": "password123"
            }
        )
        assert response.status_code == 401

    def test_login_missing_fields(self, client):
        """测试缺少字段的登录请求"""
        response = client.post(
            "/api/auth/login",
            json={"username": "testuser"}  # 缺少密码
        )
        assert response.status_code == 422

    def test_get_current_user(self, client, auth_headers, test_user):
        """测试获取当前用户信息"""
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email
        assert "id" in data

    def test_get_current_user_without_token(self, client):
        """测试未认证获取用户信息"""
        response = client.get("/api/auth/me")
        # 返回 403 (Forbidden) 而不是 401，因为依赖项处理方式不同
        assert response.status_code == 403

    def test_get_current_user_invalid_token(self, client):
        """测试无效 Token"""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401

    def test_get_users_as_admin(self, client, admin_headers, test_user):
        """测试管理员获取用户列表"""
        response = client.get("/api/auth/users", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_users_as_regular_user(self, client, auth_headers):
        """测试普通用户获取用户列表（应该失败）"""
        response = client.get("/api/auth/users", headers=auth_headers)
        assert response.status_code == 403

    def test_get_users_without_auth(self, client):
        """测试未认证获取用户列表"""
        response = client.get("/api/auth/users")
        assert response.status_code == 403


class TestAuthSecurity:
    """认证安全测试"""

    def test_password_hashing(self):
        """测试密码哈希"""
        from app.utils.security import get_password_hash, verify_password

        password = "test_password_123"
        hashed = get_password_hash(password)

        assert hashed != password  # 哈希后的密码与原密码不同
        assert verify_password(password, hashed)  # 可以验证
        assert not verify_password("wrong_password", hashed)  # 错误密码验证失败

    def test_token_creation_and_validation(self):
        """测试 JWT Token 创建和验证"""
        from app.utils.security import create_access_token, decode_access_token

        data = {"sub": "testuser", "user_id": 1}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 50  # JWT Token 通常比较长

        decoded = decode_access_token(token)
        assert decoded is not None
        assert decoded["sub"] == "testuser"
        assert decoded["user_id"] == 1

    def test_invalid_token_validation(self):
        """测试无效 Token 验证"""
        from app.utils.security import decode_access_token

        result = decode_access_token("invalid_token_string")
        assert result is None


class TestAuthRateLimiting:
    """认证速率限制测试（可选）"""

    def test_multiple_failed_logins(self, client, test_user):
        """测试多次失败登录"""
        # 模拟多次失败登录
        for _ in range(5):
            response = client.post(
                "/api/auth/login",
                json={
                    "username": test_user.username,
                    "password": "wrongpassword"
                }
            )
            assert response.status_code == 401
        # 第6次应该仍然返回 401（如果实现了速率限制可能返回 429）
        response = client.post(
            "/api/auth/login",
            json={
                "username": test_user.username,
                "password": "wrongpassword"
            }
        )
        # 实际实现中可能需要调整
        assert response.status_code in [401, 429]
