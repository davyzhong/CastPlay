"""
设备管理 API 测试
"""
import pytest
from httpx import AsyncClient
import uuid


class TestDeviceAPI:
    """设备 API 测试类"""

    def test_register_device(self, client):
        """测试设备注册"""
        device_id = str(uuid.uuid4())
        response = client.post(
            "/api/devices/register",
            json={
                "device_id": device_id,
                "device_name": "Test Device",
                "timezone": "Asia/Shanghai"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["device_id"] == device_id
        assert data["device_name"] == "Test Device"
        assert data["status"] == "online"

    def test_register_device_update_existing(self, client, test_device):
        """测试更新已存在的设备"""
        response = client.post(
            "/api/devices/register",
            json={
                "device_id": test_device.device_id,
                "device_name": "Updated Device Name",
                "timezone": "America/New_York"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["device_name"] == "Updated Device Name"
        assert data["timezone"] == "America/New_York"

    def test_device_heartbeat(self, client, test_device):
        """测试设备心跳"""
        response = client.put(f"/api/devices/{test_device.id}/heartbeat")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Heartbeat received"

    def test_get_device_list(self, client, multiple_test_devices):
        """测试获取设备列表"""
        response = client.get("/api/devices/")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) == len(multiple_test_devices)

    def test_get_device_list_with_pagination(self, client, multiple_test_devices):
        """测试分页获取设备列表"""
        response = client.get("/api/devices/?skip=0&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 2

    def test_get_device_list_with_status_filter(self, client):
        """测试状态过滤"""
        response = client.get("/api/devices/?status=online")
        assert response.status_code == 200
        data = response.json()
        for device in data["items"]:
            assert device["status"] == "online"

    def test_get_device_by_id(self, client, test_device):
        """测试获取单个设备详情"""
        response = client.get(f"/api/devices/{test_device.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_device.id
        assert data["device_id"] == test_device.device_id

    def test_get_nonexistent_device(self, client):
        """测试获取不存在的设备"""
        response = client.get("/api/devices/99999")
        assert response.status_code == 404

    def test_update_device(self, client, test_device, auth_headers):
        """测试更新设备信息"""
        response = client.put(
            f"/api/devices/{test_device.id}",
            json={
                "device_name": "New Name",
                "timezone": "Europe/London"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["device_name"] == "New Name"
        assert data["timezone"] == "Europe/London"

    def test_update_device_without_auth(self, client, test_device):
        """测试未认证更新设备"""
        response = client.put(
            f"/api/devices/{test_device.id}",
            json={"device_name": "New Name"}
        )
        assert response.status_code == 401

    def test_delete_device(self, client, test_device, auth_headers):
        """测试删除设备"""
        response = client.delete(f"/api/devices/{test_device.id}", headers=auth_headers)
        assert response.status_code == 200

        # 验证设备已被删除
        response = client.get(f"/api/devices/{test_device.id}")
        assert response.status_code == 404

    def test_delete_device_without_auth(self, client, test_device):
        """测试未认证删除设备"""
        response = client.delete(f"/api/devices/{test_device.id}")
        assert response.status_code == 401

    def test_set_device_schedule(self, client, test_device, auth_headers):
        """测试设置设备定时配置"""
        response = client.post(
            f"/api/devices/{test_device.id}/schedule",
            json={
                "power_on_time": "08:00",
                "power_off_time": "22:00",
                "is_enabled": True,
                "weekdays": [1, 2, 3, 4, 5]
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["power_on_time"] == "08:00"
        assert data["power_off_time"] == "22:00"
        assert data["is_enabled"] is True

    def test_get_device_schedule(self, client, test_device):
        """测试获取设备定时配置"""
        response = client.get(f"/api/devices/{test_device.id}/schedule")
        assert response.status_code == 200
        data = response.json()
        assert "power_on_time" in data
        assert "power_off_time" in data
        assert "is_enabled" in data
        assert "weekdays" in data


class TestDeviceValidation:
    """设备数据验证测试"""

    def test_register_missing_device_id(self, client):
        """测试缺少 device_id"""
        response = client.post(
            "/api/devices/register",
            json={"device_name": "Test"}
        )
        assert response.status_code == 422

    def test_invalid_timezone(self, client):
        """测试无效时区"""
        device_id = str(uuid.uuid4())
        response = client.post(
            "/api/devices/register",
            json={
                "device_id": device_id,
                "timezone": "Invalid/Timezone"
            }
        )
        assert response.status_code == 422

    def test_invalid_schedule_time_format(self, client, test_device, auth_headers):
        """测试无效的时间格式"""
        response = client.post(
            f"/api/devices/{test_device.id}/schedule",
            json={
                "power_on_time": "25:00",  # 无效时间
                "power_off_time": "22:00",
                "is_enabled": True,
                "weekdays": [1, 2, 3, 4, 5]
            },
            headers=auth_headers
        )
        assert response.status_code == 422


class TestDevicePermissions:
    """设备权限测试"""

    def test_regular_user_can_get_devices(self, client, auth_headers):
        """测试普通用户可以查看设备列表"""
        response = client.get("/api/devices/", headers=auth_headers)
        assert response.status_code == 200

    def test_regular_user_can_get_device_detail(self, client, auth_headers, test_device):
        """测试普通用户可以查看设备详情"""
        response = client.get(f"/api/devices/{test_device.id}", headers=auth_headers)
        assert response.status_code == 200


class TestDeviceConcurrency:
    """设备并发测试"""

    def test_multiple_device_registrations(self, client):
        """测试同时注册多个设备"""
        device_ids = [str(uuid.uuid4()) for _ in range(10)]

        for device_id in device_ids:
            response = client.post(
                "/api/devices/register",
                json={
                    "device_id": device_id,
                    "device_name": f"Device {device_id}"
                }
            )
            assert response.status_code == 200

        # 验证所有设备都已注册
        response = client.get("/api/devices/")
        data = response.json()
        assert len(data["items"]) >= 10


class TestDeviceState:
    """设备状态测试"""

    def test_device_online_status(self, client, test_device):
        """测试设备在线状态"""
        response = client.get(f"/api/devices/{test_device.id}")
        data = response.json()
        assert data["status"] in ["online", "offline"]

    def test_device_last_online_update(self, client, test_device):
        """测试最后在线时间更新"""
        # 发送心跳
        client.put(f"/api/devices/{test_device.id}/heartbeat")

        # 获取设备信息
        response = client.get(f"/api/devices/{test_device.id}")
        data = response.json()
        assert "last_online" in data
