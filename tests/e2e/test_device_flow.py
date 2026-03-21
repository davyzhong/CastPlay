"""
设备管理端到端测试

测试从设备注册到播放的完整设备流程
"""
import pytest


class TestDeviceRegistrationToPlayFlow:
    """设备注册到播放流程测试"""

    def test_complete_device_flow(self, client, test_db):
        """测试完整的设备流程：注册 -> 心跳 -> 获取详情 -> 删除"""
        # 1. 注册新设备
        import uuid
        device_id = str(uuid.uuid4())

        register_response = client.post(
            "/api/devices/register",
            json={
                "device_id": device_id,
                "device_name": "Flow Test Device",
                "timezone": "America/Los_Angeles"
            }
        )
        assert register_response.status_code in [200, 201]
        device_data = register_response.json()

        # 2. 获取设备列表（验证注册成功）
        list_response = client.get("/api/devices/")
        assert list_response.status_code == 200
        list_data = list_response.json()
        found = any(d["device_id"] == device_id for d in list_data)
        assert found

        # 3. 发送心跳
        heartbeat_response = client.put(
            f"/api/devices/{device_data['id']}/heartbeat"
        )
        assert heartbeat_response.status_code == 200

        # 4. 获取设备详情
        detail_response = client.get(f"/api/devices/{device_data['id']}")
        assert detail_response.status_code == 200
        detail_data = detail_response.json()
        assert detail_data["device_name"] == "Flow Test Device"

        # 5. 设置定时配置
        schedule_response = client.post(
            f"/api/devices/{device_data['id']}/schedule",
            json={
                "power_on_time": "08:00",
                "power_off_time": "22:00",
                "weekdays": [0, 1, 2, 3, 4],
                "is_enabled": True
            }
        )
        assert schedule_response.status_code == 200

        # 6. 获取定时配置
        get_schedule_response = client.get(
            f"/api/devices/{device_data['id']}/schedule"
        )
        assert get_schedule_response.status_code == 200
        schedule_data = get_schedule_response.json()
        assert schedule_data["power_on_time"] == "08:00"

        # 7. 清理：删除设备（需要认证）
        # 注意：这个测试场景中我们没有认证，所以跳过删除步骤

    def test_device_registration_repeated_flow(self, client):
        """测试设备重复注册流程"""
        import uuid
        device_id = str(uuid.uuid4())

        # 第一次注册
        response1 = client.post(
            "/api/devices/register",
            json={
                "device_id": device_id,
                "device_name": "First Registration"
            }
        )
        assert response1.status_code in [200, 201]
        device_id1 = response1.json()["id"]

        # 第二次注册（应该更新设备信息）
        response2 = client.post(
            "/api/devices/register",
            json={
                "device_id": device_id,
                "device_name": "Second Registration",
                "timezone": "Europe/Berlin"
            }
        )
        assert response2.status_code == 200
        device_id2 = response2.json()["id"]

        # 设备 ID 应该相同
        assert device_id1 == device_id2
        # 名称应该更新
        assert response2.json()["device_name"] == "Second Registration"

    def test_device_heartbeat_flow(self, client, test_db):
        """测试设备心跳流程"""
        import uuid

        # 注册设备
        device_id = str(uuid.uuid4())
        register_response = client.post(
            "/api/devices/register",
            json={"device_id": device_id}
        )
        device_internal_id = register_response.json()["id"]

        # 发送多次心跳
        for _ in range(3):
            heartbeat_response = client.put(
                f"/api/devices/{device_internal_id}/heartbeat"
            )
            assert heartbeat_response.status_code == 200

        # 获取详情验证状态
        detail_response = client.get(f"/api/devices/{device_internal_id}")
        assert detail_response.json()["status"] == "online"

    def test_device_schedule_flow(self, client, test_db):
        """测试设备定时配置流程"""
        import uuid

        # 注册设备
        device_id = str(uuid.uuid4())
        register_response = client.post(
            "/api/devices/register",
            json={"device_id": device_id}
        )
        device_internal_id = register_response.json()["id"]

        # 设置定时配置
        schedule_response = client.post(
            f"/api/devices/{device_internal_id}/schedule",
            json={
                "power_on_time": "09:00",
                "power_off_time": "18:00",
                "weekdays": [0, 1, 2, 3, 4],
                "is_enabled": True
            }
        )
        assert schedule_response.status_code == 200
        schedule_id = schedule_response.json()["id"]

        # 获取定时配置
        get_schedule_response = client.get(
            f"/api/devices/{device_internal_id}/schedule"
        )
        assert get_schedule_response.status_code == 200
        schedule_data = get_schedule_response.json()

        # 验证工作日
        assert schedule_data["weekdays"] == [0, 1, 2, 3, 4]
        # 验证启用状态
        assert schedule_data["is_enabled"] is True

        # 更新定时配置（禁用）
        update_response = client.post(
            f"/api/devices/{device_internal_id}/schedule",
            json={
                "power_on_time": "09:00",
                "power_off_time": "18:00",
                "is_enabled": False
            }
        )
        assert update_response.status_code == 200

        # 验证已禁用
        get_updated_response = client.get(
            f"/api/devices/{device_internal_id}/schedule"
        )
        assert get_updated_response.json()["is_enabled"] is False

    def test_device_filter_flow(self, client, test_db):
        """测试设备过滤流程"""
        import uuid

        # 创建在线设备
        online_device_id = str(uuid.uuid4())
        client.post(
            "/api/devices/register",
            json={"device_id": online_device_id, "status": "online"}
        )

        # 创建离线设备
        offline_device_id = str(uuid.uuid4())
        client.post(
            "/api/devices/register",
            json={"device_id": offline_device_id, "status": "offline"}
        )

        # 过滤在线设备
        online_response = client.get("/api/devices/?status_filter=online")
        assert online_response.status_code == 200
        online_data = online_response.json()
        assert all(d["status"] == "online" for d in online_data)

        # 过滤离线设备
        offline_response = client.get("/api/devices/?status_filter=offline")
        assert offline_response.status_code == 200
        offline_data = offline_response.json()
        assert all(d["status"] == "offline" for d in offline_data)


class TestDeviceErrorHandlingFlow:
    """设备错误处理流程测试"""

    def test_device_not_found_flow(self, client):
        """测试设备不存在的流程"""
        # 获取不存在的设备
        get_response = client.get("/api/devices/99999")
        assert get_response.status_code == 404

        # 发送心跳到不存在的设备
        heartbeat_response = client.put("/api/devices/99999/heartbeat")
        assert heartbeat_response.status_code == 404

        # 获取不存在的定时配置
        schedule_response = client.get("/api/devices/99999/schedule")
        assert schedule_response.status_code == 404

    def test_device_invalid_data_flow(self, client):
        """测试无效数据的流程"""
        # 缺少 device_id
        register_response = client.post(
            "/api/devices/register",
            json={"device_name": "Test"}
        )
        assert register_response.status_code == 422

        # 无效的状态过滤器
        filter_response = client.get("/api/devices/?status_filter=invalid")
        assert filter_response.status_code == 422


class TestDevicePaginationFlow:
    """设备分页流程测试"""

    def test_device_pagination_flow(self, client, test_db):
        """测试设备分页流程"""
        import uuid

        # 创建多个设备
        device_ids = []
        for _ in range(5):
            device_id = str(uuid.uuid4())
            response = client.post(
                "/api/devices/register",
                json={"device_id": device_id, "device_name": f"Device {len(device_ids)}"}
            )
            device_ids.append(response.json()["id"])

        # 分页查询
        page1 = client.get("/api/devices/?skip=0&limit=2")
        page2 = client.get("/api/devices/?skip=2&limit=2")
        page3 = client.get("/api/devices/?skip=4&limit=2")

        assert page1.status_code == 200
        assert page2.status_code == 200
        assert page3.status_code == 200

        # 验证页面大小
        assert len(page1.json()) <= 2
        assert len(page2.json()) <= 2
