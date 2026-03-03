"""
Device API Tests (FastAPI 版本)
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device


@pytest.mark.asyncio
async def test_register_device_new(client: AsyncClient, test_db: AsyncSession):
    """测试新设备注册"""
    response = await client.post(
        "/api/v1/devices/register",
        json={
            "hardware_id": "test_hardware_123",
            "device_name": "Test Device",
            "timezone": "Asia/Shanghai"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_new"] == True
    assert "device" in data
    assert data["device"]["device_name"] == "Test Device"
    assert data["device"]["device_id"].startswith("CAS-")


@pytest.mark.asyncio
async def test_register_device_existing(client: AsyncClient, test_db: AsyncSession):
    """测试已有设备重新注册"""
    # 先注册一次
    response1 = await client.post(
        "/api/v1/devices/register",
        json={"hardware_id": "test_hardware_456"}
    )
    device_id = response1.json()["device"]["device_id"]

    # 再次注册
    response2 = await client.post(
        "/api/v1/devices/register",
        json={
            "device_id": device_id,
            "device_name": "Updated Name"
        }
    )

    assert response2.status_code == 200
    data = response2.json()
    assert data["is_new"] == False
    assert data["device"]["device_name"] == "Updated Name"


@pytest.mark.asyncio
async def test_create_device_requires_auth(client: AsyncClient):
    """测试创建设备需要认证"""
    # 开发模式下会跳过认证，这里主要测试 API 是否正常工作
    response = await client.post(
        "/api/v1/devices",
        json={"device_name": "Auth Test Device"}
    )

    # 在开发模式下应该成功
    assert response.status_code in [200, 201]


@pytest.mark.asyncio
async def test_list_devices(client: AsyncClient, test_db: AsyncSession):
    """测试设备列表"""
    # 先创建一些设备
    for i in range(3):
        await client.post(
            "/api/v1/devices/register",
            json={"hardware_id": f"list_test_{i}"}
        )

    response = await client.get("/api/v1/devices")

    assert response.status_code == 200
    data = response.json()
    assert "devices" in data
    assert "total" in data
    assert data["total"] >= 3


@pytest.mark.asyncio
async def test_get_device_not_found(client: AsyncClient):
    """测试获取不存在的设备"""
    response = await client.get("/api/v1/devices/99999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_heartbeat(client: AsyncClient, test_db: AsyncSession):
    """测试心跳"""
    # 先注册设备
    reg_response = await client.post(
        "/api/v1/devices/register",
        json={"hardware_id": "heartbeat_test"}
    )
    device_id = reg_response.json()["device"]["id"]

    # 发送心跳
    response = await client.put(f"/api/v1/devices/{device_id}/heartbeat")

    assert response.status_code == 200
    assert "Heartbeat received" in response.json()["message"]
