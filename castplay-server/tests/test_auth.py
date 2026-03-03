"""
Auth API Tests (FastAPI 版本)
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """测试登录成功"""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "admin",
            "password": "castplay2024"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "Bearer"
    assert data["user"]["username"] == "admin"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    """测试登录失败"""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "admin",
            "password": "wrong_password"
        }
    )

    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient):
    """测试刷新 Token"""
    # 先登录获取 token
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "admin",
            "password": "castplay2024"
        }
    )
    refresh_token = login_response.json()["refresh_token"]

    # 刷新 token
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "Bearer"


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient):
    """测试获取当前用户"""
    # 在开发模式下不需要认证
    response = await client.get("/api/v1/auth/me")

    assert response.status_code == 200
    data = response.json()
    assert "username" in data


@pytest.mark.asyncio
async def test_change_password_too_short(client: AsyncClient):
    """测试密码太短"""
    response = await client.post(
        "/api/v1/auth/change-password",
        json={
            "old_password": "castplay2024",
            "new_password": "short"
        }
    )

    assert response.status_code == 400
    assert "8 characters" in response.json()["detail"]
