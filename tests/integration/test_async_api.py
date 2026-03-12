"""
异步 API 测试

测试异步代码路径和 WebSocket 端点
"""
import pytest
from httpx import AsyncClient, ASGITransport


# ============================================================================
# 异步客户端 fixture
# ============================================================================

@pytest.fixture
async def async_app():
    """创建异步测试应用"""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    # 设置测试环境
    import os
    os.environ["TESTING"] = "true"
    os.environ["DATABASE_PATH"] = ":memory:"

    app = FastAPI(title="Test App")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 导入数据库和模型
    from app.database import get_db
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.models import Base

    # 创建测试数据库
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    Base.metadata.create_all(bind=test_engine)
    TestSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine
    )

    def override_get_db():
        try:
            db = TestSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # 注册路由
    from app.api import auth, devices, media, playlists, player
    app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
    app.include_router(devices.router, prefix="/api/devices", tags=["设备"])
    app.include_router(media.router, prefix="/api/media", tags=["媒体"])
    app.include_router(playlists.router, prefix="/api/playlists", tags=["播放列表"])
    app.include_router(player.router, prefix="/api/player", tags=["播放端"])

    @app.get("/health")
    def health():
        return {"status": "ok"}

    yield app

    app.dependency_overrides.clear()


@pytest.fixture
async def async_client(async_app):
    """异步测试客户端"""
    async with AsyncClient(
        transport=ASGITransport(app=async_app),
        base_url="http://test"
    ) as client:
        yield client


# ============================================================================
# 异步认证测试
# ============================================================================

class TestAsyncAuth:
    """异步认证测试"""

    @pytest.mark.asyncio
    async def test_async_register(self, async_client):
        """异步注册测试"""
        response = await async_client.post(
            "/api/auth/register",
            json={
                "username": "asyncuser",
                "password": "password123",
                "email": "async@example.com"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "asyncuser"

    @pytest.mark.asyncio
    async def test_async_login(self, async_client):
        """异步登录测试"""
        # 先注册
        await async_client.post(
            "/api/auth/register",
            json={
                "username": "asynclogin",
                "password": "password123"
            }
        )

        # 然后登录
        response = await async_client.post(
            "/api/auth/login",
            json={
                "username": "asynclogin",
                "password": "password123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    @pytest.mark.asyncio
    async def test_async_get_current_user(self, async_client):
        """异步获取当前用户测试"""
        # 注册
        await async_client.post(
            "/api/auth/register",
            json={
                "username": "asynccurrent",
                "password": "password123"
            }
        )

        # 登录获取 token
        login_response = await async_client.post(
            "/api/auth/login",
            json={
                "username": "asynccurrent",
                "password": "password123"
            }
        )
        token = login_response.json()["access_token"]

        # 获取当前用户
        response = await async_client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "asynccurrent"


# ============================================================================
# 异步设备测试
# ============================================================================

class TestAsyncDevices:
    """异步设备测试"""

    @pytest.mark.asyncio
    async def test_async_device_registration(self, async_client):
        """异步设备注册测试"""
        import uuid
        response = await async_client.post(
            "/api/devices/register",
            json={
                "device_id": str(uuid.uuid4()),
                "device_name": "Async Device"
            }
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert data["device_name"] == "Async Device"

    @pytest.mark.asyncio
    async def test_async_device_list(self, async_client):
        """异步设备列表测试"""
        # 注册几个设备
        import uuid
        for i in range(3):
            await async_client.post(
                "/api/devices/register",
                json={
                    "device_id": str(uuid.uuid4()),
                    "device_name": f"Device {i}"
                }
            )

        # 获取列表
        response = await async_client.get("/api/devices/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data.get("items", data), list)

    @pytest.mark.asyncio
    async def test_async_device_heartbeat(self, async_client):
        """异步设备心跳测试"""
        import uuid

        # 注册设备
        reg_response = await async_client.post(
            "/api/devices/register",
            json={"device_id": str(uuid.uuid4())}
        )
        device_id = reg_response.json()["id"]

        # 发送心跳
        response = await async_client.put(f"/api/devices/{device_id}/heartbeat")

        assert response.status_code == 200


# ============================================================================
# 并发请求测试
# ============================================================================

class TestConcurrentRequests:
    """并发请求测试"""

    @pytest.mark.asyncio
    async def test_concurrent_health_checks(self, async_client):
        """并发健康检查"""
        import asyncio

        async def health_check():
            return await async_client.get("/health")

        # 并发发送 10 个请求
        tasks = [health_check() for _ in range(10)]
        responses = await asyncio.gather(*tasks)

        # 所有请求应该成功
        for response in responses:
            assert response.status_code == 200
            assert response.json()["status"] == "ok"

    @pytest.mark.asyncio
    async def test_concurrent_device_registrations(self, async_client):
        """并发设备注册"""
        import asyncio
        import uuid

        async def register_device(index):
            return await async_client.post(
                "/api/devices/register",
                json={
                    "device_id": str(uuid.uuid4()),
                    "device_name": f"Concurrent Device {index}"
                }
            )

        # 并发发送 5 个注册请求
        tasks = [register_device(i) for i in range(5)]
        responses = await asyncio.gather(*tasks)

        # 所有请求应该成功
        success_count = sum(1 for r in responses if r.status_code in [200, 201])
        assert success_count == 5

    @pytest.mark.asyncio
    async def test_concurrent_mixed_operations(self, async_client):
        """并发混合操作"""
        import asyncio
        import uuid

        results = []

        async def register():
            response = await async_client.post(
                "/api/devices/register",
                json={"device_id": str(uuid.uuid4())}
            )
            results.append(("register", response.status_code))

        async def list_devices():
            response = await async_client.get("/api/devices/")
            results.append(("list", response.status_code))

        async def health():
            response = await async_client.get("/health")
            results.append(("health", response.status_code))

        # 混合操作
        tasks = []
        for _ in range(5):
            tasks.extend([register(), list_devices(), health()])

        await asyncio.gather(*tasks)

        # 统计成功率
        success_count = sum(1 for _, status in results if status in [200, 201])
        success_rate = success_count / len(results)

        assert success_rate >= 0.9  # 至少 90% 成功率
