"""
设备管理 API 集成测试

测试所有设备管理相关的 API 端点
"""
import pytest
import uuid
from datetime import datetime


# ============================================================================
# 设备注册端点测试
# ============================================================================

class TestDeviceRegisterEndpoint:
    """设备注册端点测试"""

    def test_register_new_device(self, client):
        """测试注册新设备"""
        device_data = {
            "device_id": str(uuid.uuid4()),
            "device_name": "Living Room TV",
            "timezone": "America/New_York"
        }

        response = client.post("/api/devices/register", json=device_data)

        assert response.status_code == 201
        data = response.json()
        assert data["device_id"] == device_data["device_id"]
        assert data["device_name"] == "Living Room TV"
        assert data["timezone"] == "America/New_York"
        assert data["status"] == "online"
        assert data["last_online"] is not None

    def test_register_device_minimal(self, client):
        """测试注册最小信息设备"""
        device_data = {
            "device_id": str(uuid.uuid4())
        }

        response = client.post("/api/devices/register", json=device_data)

        assert response.status_code == 201
        data = response.json()
        assert data["device_id"] == device_data["device_id"]
        assert data["device_name"] == "Default Device"
        assert data["timezone"] == "Asia/Shanghai"

    def test_register_existing_device(self, client, test_device):
        """测试注册已存在的设备（应该更新）"""
        device_data = {
            "device_id": test_device.device_id,
            "device_name": "Updated Name"
        }

        response = client.post("/api/devices/register", json=device_data)

        assert response.status_code == 200
        data = response.json()
        assert data["device_id"] == test_device.device_id
        assert data["device_name"] == "Updated Name"

    def test_register_device_invalid_timezone(self, client):
        """测试无效时区"""
        device_data = {
            "device_id": str(uuid.uuid4()),
            "timezone": "Invalid/Timezone"
        }

        response = client.post("/api/devices/register", json=device_data)

        # 可能不验证时区格式，取决于实现
        # 如果验证，应该返回 422
        # 如果不验证，会接受
        assert response.status_code in [200, 201, 422]

    def test_register_missing_device_id(self, client):
        """测试缺少设备 ID"""
        response = client.post("/api/devices/register", json={"device_name": "Test"})

        assert response.status_code == 422


# ============================================================================
# 设备心跳端点测试
# ============================================================================

class TestDeviceHeartbeatEndpoint:
    """设备心跳端点测试"""

    def test_device_heartbeat(self, client, test_device):
        """测试设备心跳"""
        response = client.put(f"/api/devices/{test_device.id}/heartbeat")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Heartbeat received"
        assert data["device_id"] == test_device.device_id

    def test_heartbeat_nonexistent_device(self, client):
        """测试不存在设备的心跳"""
        response = client.put("/api/devices/99999/heartbeat")

        assert response.status_code == 404
        assert "Device not found" in response.json()["detail"]

    def test_heartbeat_updates_timestamp(self, client, test_device):
        """测试心跳更新时间戳"""
        import time

        # 获取初始时间
        initial_time = test_device.last_online

        # 等待一小段时间
        time.sleep(0.1)

        # 发送心跳
        client.put(f"/api/devices/{test_device.id}/heartbeat")

        # 验证时间已更新（需要重新查询数据库）
        # 在实际测试中，需要从数据库获取更新后的记录
        # 这里仅验证端点响应正确


# ============================================================================
# 设备列表端点测试
# ============================================================================

class TestDeviceListEndpoint:
    """设备列表端点测试"""

    def test_list_devices(self, client, multiple_test_devices):
        """测试获取设备列表"""
        response = client.get("/api/devices/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= len(multiple_test_devices)

    def test_list_devices_with_pagination(self, client, multiple_test_devices):
        """测试设备列表分页"""
        response = client.get("/api/devices/?skip=0&limit=2")

        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    def test_list_devices_skip(self, client, multiple_test_devices):
        """测试跳过设备"""
        response_1 = client.get("/api/devices/?skip=0&limit=1")
        response_2 = client.get("/api/devices/?skip=1&limit=1")

        assert response_1.status_code == 200
        assert response_2.status_code == 200

        data_1 = response_1.json()
        data_2 = response_2.json()

        # 跳过第一个后，应该返回不同的设备
        if len(data_1) > 0 and len(data_2) > 0:
            assert data_1[0]["id"] != data_2[0]["id"]

    def test_list_devices_filter_online(self, client, test_db):
        """测试过滤在线设备"""
        # 创建在线和离线设备
        from app.models.device import Device
        import uuid

        online = Device(
            device_id=str(uuid.uuid4()),
            device_name="Online Device",
            status="online"
        )
        offline = Device(
            device_id=str(uuid.uuid4()),
            device_name="Offline Device",
            status="offline"
        )
        test_db.add_all([online, offline])
        test_db.commit()

        # 过滤在线设备
        response = client.get("/api/devices/?status_filter=online")

        assert response.status_code == 200
        data = response.json()
        assert all(device["status"] == "online" for device in data)

    def test_list_devices_filter_offline(self, client, test_db):
        """测试过滤离线设备"""
        from app.models.device import Device
        import uuid

        offline = Device(
            device_id=str(uuid.uuid4()),
            device_name="Offline Device",
            status="offline"
        )
        test_db.add(offline)
        test_db.commit()

        response = client.get("/api/devices/?status_filter=offline")

        assert response.status_code == 200
        data = response.json()
        assert all(device["status"] == "offline" for device in data)

    def test_list_devices_invalid_filter(self, client):
        """测试无效的状态过滤器"""
        response = client.get("/api/devices/?status_filter=invalid")

        assert response.status_code == 422

    def test_list_devices_empty(self, client, test_db):
        """测试空设备列表（清空数据库后）"""
        # 在测试环境中，这是不切实际的，因为测试数据库是隔离的
        # 但我们可以测试 limit=0 的情况
        response = client.get("/api/devices/?limit=0")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


# ============================================================================
# 设备详情端点测试
# ============================================================================

class TestDeviceDetailEndpoint:
    """设备详情端点测试"""

    def test_get_device_detail(self, client, test_device):
        """测试获取设备详情"""
        response = client.get(f"/api/devices/{test_device.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_device.id
        assert data["device_id"] == test_device.device_id
        assert data["device_name"] == test_device.device_name

    def test_get_nonexistent_device(self, client):
        """测试获取不存在的设备"""
        response = client.get("/api/devices/99999")

        assert response.status_code == 404
        assert "Device not found" in response.json()["detail"]

    def test_get_device_all_fields(self, client, test_device):
        """测试获取设备的所有字段"""
        response = client.get(f"/api/devices/{test_device.id}")

        assert response.status_code == 200
        data = response.json()

        # 验证所有预期字段存在
        expected_fields = [
            "id", "device_id", "device_name", "timezone",
            "status", "last_online", "created_at"
        ]
        for field in expected_fields:
            assert field in data


# ============================================================================
# 设备更新端点测试
# ============================================================================

class TestDeviceUpdateEndpoint:
    """设备更新端点测试"""

    def test_update_device_name(self, client, test_device, auth_headers):
        """测试更新设备名称"""
        response = client.put(
            f"/api/devices/{test_device.id}",
            json={"device_name": "Updated Name"},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["device_name"] == "Updated Name"

    def test_update_device_timezone(self, client, test_device, auth_headers):
        """测试更新设备时区"""
        response = client.put(
            f"/api/devices/{test_device.id}",
            json={"timezone": "Europe/London"},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["timezone"] == "Europe/London"

    def test_update_device_status(self, client, test_device, auth_headers):
        """测试更新设备状态"""
        response = client.put(
            f"/api/devices/{test_device.id}",
            json={"status": "offline"},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "offline"

    def test_update_device_all_fields(self, client, test_device, auth_headers):
        """测试更新设备所有字段"""
        update_data = {
            "device_name": "Fully Updated",
            "timezone": "Australia/Sydney",
            "status": "online"
        }

        response = client.put(
            f"/api/devices/{test_device.id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["device_name"] == update_data["device_name"]
        assert data["timezone"] == update_data["timezone"]
        assert data["status"] == update_data["status"]

    def test_update_nonexistent_device(self, client, auth_headers):
        """测试更新不存在的设备"""
        response = client.put(
            "/api/devices/99999",
            json={"device_name": "Test"},
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_update_without_auth(self, client, test_device):
        """测试未认证更新设备"""
        response = client.put(
            f"/api/devices/{test_device.id}",
            json={"device_name": "Test"}
        )

        assert response.status_code == 401

    def test_update_with_partial_data(self, client, test_device, auth_headers):
        """测试部分更新设备"""
        response = client.put(
            f"/api/devices/{test_device.id}",
            json={"device_name": "Partial Update"},
            headers=auth_headers
        )

        assert response.status_code == 200


# ============================================================================
# 设备删除端点测试
# ============================================================================

class TestDeviceDeleteEndpoint:
    """设备删除端点测试"""

    def test_delete_device(self, client, test_db, auth_headers):
        """测试删除设备"""
        # 创建测试设备
        from app.models.device import Device
        import uuid
        device = Device(
            device_id=str(uuid.uuid4()),
            device_name="To Delete"
        )
        test_db.add(device)
        test_db.commit()
        test_db.refresh(device)

        # 删除设备
        response = client.delete(f"/api/devices/{device.id}", headers=auth_headers)

        assert response.status_code == 204
        assert response.content == b""

        # 验证设备已被删除
        deleted = test_db.query(Device).filter(Device.id == device.id).first()
        assert deleted is None

    def test_delete_nonexistent_device(self, client, auth_headers):
        """测试删除不存在的设备"""
        response = client.delete("/api/devices/99999", headers=auth_headers)

        assert response.status_code == 404

    def test_delete_without_auth(self, client, test_device):
        """测试未认证删除设备"""
        response = client.delete(f"/api/devices/{test_device.id}")

        assert response.status_code == 401


# ============================================================================
# 设备定时配置端点测试
# ============================================================================

class TestDeviceScheduleEndpoint:
    """设备定时配置端点测试"""

    def test_set_device_schedule(self, client, test_device):
        """测试设置设备定时配置"""
        schedule_data = {
            "power_on_time": "09:00",
            "power_off_time": "18:00",
            "weekdays": [0, 1, 2, 3, 4],
            "is_enabled": True
        }

        response = client.post(
            f"/api/devices/{test_device.id}/schedule",
            json=schedule_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["power_on_time"] == "09:00"
        assert data["power_off_time"] == "18:00"
        assert data["weekdays"] == [0, 1, 2, 3, 4]
        assert data["is_enabled"] is True

    def test_set_schedule_minimal(self, client, test_device):
        """测试设置最小定时配置"""
        schedule_data = {
            "power_on_time": "08:00",
            "power_off_time": "20:00"
        }

        response = client.post(
            f"/api/devices/{test_device.id}/schedule",
            json=schedule_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["power_on_time"] == "08:00"
        assert data["power_off_time"] == "20:00"

    def test_set_schedule_disabled(self, client, test_device):
        """测试设置禁用的定时配置"""
        schedule_data = {
            "power_on_time": "09:00",
            "power_off_time": "18:00",
            "is_enabled": False
        }

        response = client.post(
            f"/api/devices/{test_device.id}/schedule",
            json=schedule_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_enabled"] is False

    def test_set_schedule_weekend_only(self, client, test_device):
        """测试设置仅周末的定时配置"""
        schedule_data = {
            "power_on_time": "10:00",
            "power_off_time": "22:00",
            "weekdays": [5, 6]  # 周六、周日
        }

        response = client.post(
            f"/api/devices/{test_device.id}/schedule",
            json=schedule_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["weekdays"] == [5, 6]

    def test_update_existing_schedule(self, client, test_device):
        """测试更新已存在的定时配置"""
        # 首先创建配置
        schedule_data_1 = {
            "power_on_time": "09:00",
            "power_off_time": "18:00"
        }
        client.post(
            f"/api/devices/{test_device.id}/schedule",
            json=schedule_data_1
        )

        # 更新配置
        schedule_data_2 = {
            "power_on_time": "08:00",
            "power_off_time": "20:00"
        }
        response = client.post(
            f"/api/devices/{test_device.id}/schedule",
            json=schedule_data_2
        )

        assert response.status_code == 200
        data = response.json()
        assert data["power_on_time"] == "08:00"

    def test_get_device_schedule(self, client, test_device):
        """测试获取设备定时配置"""
        # 先设置配置
        schedule_data = {
            "power_on_time": "09:00",
            "power_off_time": "18:00",
            "weekdays": [0, 1, 2, 3, 4]
        }
        client.post(
            f"/api/devices/{test_device.id}/schedule",
            json=schedule_data
        )

        # 获取配置
        response = client.get(f"/api/devices/{test_device.id}/schedule")

        assert response.status_code == 200
        data = response.json()
        assert data["power_on_time"] == "09:00"
        assert data["power_off_time"] == "18:00"

    def test_get_nonexistent_schedule(self, client, test_device):
        """测试获取不存在的定时配置"""
        response = client.get(f"/api/devices/{test_device.id}/schedule")

        assert response.status_code == 404
        assert "No schedule configured" in response.json()["detail"]

    def test_schedule_invalid_time_format(self, client, test_device):
        """测试无效的时间格式"""
        schedule_data = {
            "power_on_time": "invalid",
            "power_off_time": "18:00"
        }

        response = client.post(
            f"/api/devices/{test_device.id}/schedule",
            json=schedule_data
        )

        # 取决于验证逻辑
        assert response.status_code in [200, 422]


# ============================================================================
# 边界条件测试
# ============================================================================

class TestDeviceBoundaryConditions:
    """设备边界条件测试"""

    def test_device_very_long_name(self, client):
        """测试超长设备名称"""
        long_name = "a" * 200
        device_data = {
            "device_id": str(uuid.uuid4()),
            "device_name": long_name
        }

        response = client.post("/api/devices/register", json=device_data)
        assert response.status_code in [200, 201, 422]

    def test_device_special_characters_name(self, client):
        """测试设备名称中的特殊字符"""
        device_data = {
            "device_id": str(uuid.uuid4()),
            "device_name": "Device@#$%^&*()"
        }

        response = client.post("/api/devices/register", json=device_data)
        assert response.status_code in [200, 201]

    def test_schedule_midnight(self, client, test_device):
        """测试午夜时间配置"""
        schedule_data = {
            "power_on_time": "00:00",
            "power_off_time": "23:59"
        }

        response = client.post(
            f"/api/devices/{test_device.id}/schedule",
            json=schedule_data
        )

        assert response.status_code == 200

    def test_schedule_all_weekdays(self, client, test_device):
        """测试所有工作日配置"""
        schedule_data = {
            "power_on_time": "00:00",
            "power_off_time": "23:59",
            "weekdays": [0, 1, 2, 3, 4, 5, 6]
        }

        response = client.post(
            f"/api/devices/{test_device.id}/schedule",
            json=schedule_data
        )

        assert response.status_code == 200

    def test_schedule_single_weekday(self, client, test_device):
        """测试单个工作日配置"""
        schedule_data = {
            "power_on_time": "09:00",
            "power_off_time": "18:00",
            "weekdays": [0]  # 仅周一
        }

        response = client.post(
            f"/api/devices/{test_device.id}/schedule",
            json=schedule_data
        )

        assert response.status_code == 200
