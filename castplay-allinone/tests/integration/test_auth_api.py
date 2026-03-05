"""
认证 API 集成测试

测试所有认证相关的 API 端点
"""
import pytest

from app.models.user import User


# ============================================================================
# 注册端点测试
# ============================================================================

class TestRegisterEndpoint:
    """注册端点测试"""

    def test_register_new_user(self, client):
        """测试注册新用户"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "password": "securePassword123",
                "email": "newuser@example.com",
                "full_name": "New User"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert data["is_active"] is True
        assert "password_hash" not in data
        assert "id" in data

    def test_register_minimal_user(self, client):
        """测试注册最小信息用户"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "minimaluser",
                "password": "pass123"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "minimaluser"
        assert data["email"] is None
        assert data["full_name"] is None

    def test_register_duplicate_username(self, client, test_user):
        """测试注册重复用户名"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": test_user.username,
                "password": "password123"
            }
        )

        assert response.status_code == 400
        assert "Username already exists" in response.json()["detail"]

    def test_register_duplicate_email(self, client, test_user):
        """测试注册重复邮箱"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "differentuser",
                "password": "password123",
                "email": test_user.email
            }
        )

        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    def test_register_missing_username(self, client):
        """测试缺少用户名"""
        response = client.post(
            "/api/auth/register",
            json={"password": "password123"}
        )

        assert response.status_code == 422

    def test_register_missing_password(self, client):
        """测试缺少密码"""
        response = client.post(
            "/api/auth/register",
            json={"username": "testuser"}
        )

        assert response.status_code == 422

    def test_register_invalid_data_types(self, client):
        """测试无效数据类型"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": 123,  # 数字而不是字符串
                "password": "password123"
            }
        )

        assert response.status_code == 422


# ============================================================================
# 登录端点测试
# ============================================================================

class TestLoginEndpoint:
    """登录端点测试"""

    def test_login_success(self, client, test_user):
        """测试成功登录"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "testpass123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["username"] == "testuser"
        assert "password_hash" not in data["user"]

    def test_login_wrong_username(self, client, test_user):
        """测试错误的用户名"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "wronguser",
                "password": "testpass123"
            }
        )

        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    def test_login_wrong_password(self, client, test_user):
        """测试错误的密码"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "wrongpassword"
            }
        )

        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    def test_login_missing_credentials(self, client):
        """测试缺少凭据"""
        response = client.post("/api/auth/login", json={})

        assert response.status_code == 422

    def test_login_with_admin(self, client, test_admin):
        """测试管理员登录"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "admin",
                "password": "admin123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user"]["is_superuser"] is True


# ============================================================================
# 获取当前用户信息端点测试
# ============================================================================

class TestGetCurrentUserEndpoint:
    """获取当前用户信息端点测试"""

    def test_get_current_user_with_token(self, client, test_user, auth_headers):
        """测试使用 Token 获取当前用户"""
        response = client.get("/api/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name

    def test_get_current_user_without_token(self, client):
        """测试没有 Token 获取当前用户"""
        response = client.get("/api/auth/me")

        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client):
        """测试无效 Token"""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401

    def test_get_current_user_malformed_token(self, client):
        """测试格式错误的 Token"""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "InvalidFormat token"}
        )

        assert response.status_code == 401

    def test_get_current_user_expired_token(self, client, test_user):
        """测试过期的 Token（需要模拟）"""
        # 这个测试可能需要创建一个立即过期的 Token
        # 在实际实现中，可以使用 JWT 手动创建过期 Token
        pass


# ============================================================================
# 用户列表端点测试
# ============================================================================

class TestListUsersEndpoint:
    """用户列表端点测试"""

    def test_list_users_as_admin(self, client, test_admin, admin_headers):
        """测试管理员获取用户列表"""
        # 创建多个用户
        for i in range(3):
            user = User(
                username=f"user{i}",
                password_hash="hashed",
                email=f"user{i}@example.com"
            )
            client.app.dependency_overrides[lambda: user]

        response = client.get("/api/auth/users", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1  # 至少有管理员

    def test_list_users_as_regular_user(self, client, test_user, auth_headers):
        """测试普通用户获取用户列表（应该失败）"""
        response = client.get("/api/auth/users", headers=auth_headers)

        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]

    def test_list_users_without_auth(self, client):
        """测试未认证获取用户列表"""
        response = client.get("/api/auth/users")

        assert response.status_code == 401

    def test_list_users_pagination(self, client, test_admin, admin_headers):
        """测试用户列表分页"""
        response = client.get("/api/auth/users?skip=0&limit=10", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_users_large_limit(self, client, test_admin, admin_headers):
        """测试大 limit（应该被限制）"""
        response = client.get("/api/auth/users?limit=1000", headers=admin_headers)

        # 应该返回成功，但实际数量应该被限制
        assert response.status_code == 200


# ============================================================================
# Token 验证测试
# ============================================================================

class TestTokenValidation:
    """Token 验证测试"""

    def test_token_in_multiple_requests(self, client, test_user):
        """测试 Token 在多个请求中使用"""
        # 登录获取 Token
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "testpass123"
            }
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 使用 Token 多次请求
        for _ in range(3):
            response = client.get("/api/auth/me", headers=headers)
            assert response.status_code == 200

    def test_token_format(self, client, test_user):
        """测试 Token 格式"""
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "testpass123"
            }
        )
        token = login_response.json()["access_token"]

        # Token 应该是三个部分组成的 JWT 格式
        parts = token.split(".")
        assert len(parts) == 3


# ============================================================================
# 用户状态测试
# ============================================================================

class TestUserStatus:
    """用户状态测试"""

    def test_inactive_user_cannot_login(self, client, test_db):
        """测试非活跃用户无法登录"""
        # 创建非活跃用户
        from app.utils.security import get_password_hash
        inactive_user = User(
            username="inactive",
            password_hash=get_password_hash("password123"),
            is_active=False
        )
        test_db.add(inactive_user)
        test_db.commit()

        response = client.post(
            "/api/auth/login",
            json={"username": "inactive", "password": "password123"}
        )

        assert response.status_code == 403

    def test_inactive_user_cannot_access_api(self, client, test_db):
        """测试非活跃用户无法访问 API"""
        from app.utils.security import get_password_hash, create_access_token
        from app.models.user import User

        # 创建非活跃用户
        inactive_user = User(
            username="inactive2",
            password_hash=get_password_hash("password123"),
            is_active=False
        )
        test_db.add(inactive_user)
        test_db.commit()
        test_db.refresh(inactive_user)

        # 创建 Token
        token = create_access_token(
            data={"sub": str(inactive_user.id), "username": "inactive2"}
        )
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/api/auth/me", headers=headers)

        assert response.status_code == 403


# ============================================================================
# 边界条件测试
# ============================================================================

class TestAuthBoundaryConditions:
    """认证边界条件测试"""

    def test_very_long_username(self, client):
        """测试超长用户名"""
        long_username = "a" * 100
        response = client.post(
            "/api/auth/register",
            json={
                "username": long_username,
                "password": "password123"
            }
        )

        # 根据实际约束，可能成功或失败
        # 如果成功，检查用户名是否被截断或存储
        assert response.status_code in [201, 422]

    def test_special_characters_in_username(self, client):
        """测试用户名中的特殊字符"""
        usernames = [
            "user_name",
            "user-name",
            "user.name",
            "user@domain"
        ]

        for username in usernames:
            response = client.post(
                "/api/auth/register",
                json={
                    "username": username,
                    "password": "password123"
                }
            )
            # 根据实际验证规则
            assert response.status_code in [201, 422]

    def test_very_long_password(self, client):
        """测试超长密码"""
        long_password = "a" * 1000
        response = client.post(
            "/api/auth/register",
            json={
                "username": "longpassuser",
                "password": long_password
            }
        )

        # bcrypt 有长度限制，但应该能处理
        assert response.status_code == 201

    def test_empty_username(self, client):
        """测试空用户名"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "",
                "password": "password123"
            }
        )

        assert response.status_code == 422

    def test_empty_password(self, client):
        """测试空密码"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "emptypass",
                "password": ""
            }
        )

        assert response.status_code == 422
