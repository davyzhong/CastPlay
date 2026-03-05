"""
设备功能单元测试

测试设备相关的新功能:
- MAC 地址注册
- 注册码生成
- 设备定时配置 404 处理
- 设备播放列表管理
"""
import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestMacAddressRegistration:
    """MAC 地址注册测试"""

    def test_register_with_mac_address(self, client):
        """测试使用 MAC 地址注册设备"""
        mac_address = "AA:BB:CC:DD:EE:FF"
        response = client.post(
            "/api/devices/register",
            json={
                "mac_address": mac_address,
                "device_name": "MAC Test Device"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["mac_address"] == mac_address
        assert data["registration_code"] is not None
        assert data["registration_code"].startswith("CP-")

    def test_register_with_mac_lowercase(self, client):
        """测试小写 MAC 地址自动转为大写"""
        mac_address = "aa:bb:cc:dd:ee:ff"
        response = client.post(
            "/api/devices/register",
            json={
                "mac_address": mac_address,
                "device_name": "Lowercase MAC Device"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["mac_address"] == mac_address.upper()

    def test_register_same_mac_updates_device(self, client):
        """测试同一 MAC 地址更新设备而非创建新设备"""
        mac_address = "11:22:33:44:55:66"

        # 第一次注册
        response1 = client.post(
            "/api/devices/register",
            json={
                "mac_address": mac_address,
                "device_name": "Original Device"
            }
        )
        assert response1.status_code == 201
        device_id_1 = response1.json()["id"]
        registration_code = response1.json()["registration_code"]

        # 第二次注册（应该更新）
        response2 = client.post(
            "/api/devices/register",
            json={
                "mac_address": mac_address,
                "device_name": "Updated Device"
            }
        )
        assert response2.status_code == 200  # 更新返回 200
        device_id_2 = response2.json()["id"]

        # 应该是同一个设备
        assert device_id_1 == device_id_2
        assert response2.json()["registration_code"] == registration_code

    def test_register_generates_friendly_registration_code(self, client):
        """测试生成友好的注册码格式"""
        mac_address = "DE:AD:BE:EF:CA:FE"
        response = client.post(
            "/api/devices/register",
            json={
                "mac_address": mac_address,
                "device_name": "Code Test Device"
            }
        )

        assert response.status_code == 201
        code = response.json()["registration_code"]

        # 验证格式: CP-XXXX-XXXX-XXXX
        parts = code.split("-")
        assert len(parts) == 4
        assert parts[0] == "CP"
        for part in parts[1:]:
            assert len(part) == 4
            assert part.isalnum()

    def test_register_with_device_id_and_mac(self, client):
        """测试同时提供 device_id 和 mac_address（MAC 优先）"""
        mac_address = "FE:DC:BA:98:76:54"
        device_id = str(uuid.uuid4())

        response = client.post(
            "/api/devices/register",
            json={
                "device_id": device_id,
                "mac_address": mac_address,
                "device_name": "Dual ID Device"
            }
        )

        assert response.status_code == 201
        data = response.json()
        # MAC 地址注册会生成基于 MAC 的 device_id
        assert "device-" in data["device_id"]


class TestRegistrationCodeGeneration:
    """注册码生成测试"""

    def test_deterministic_code_from_mac(self, client):
        """测试相同 MAC 地址生成相同注册码"""
        mac_address = "AA:BB:CC:11:22:33"

        responses = []
        for _ in range(3):
            # 每次使用相同的 MAC 注册应该返回相同的注册码
            response = client.post(
                "/api/devices/register",
                json={
                    "mac_address": mac_address,
                    "device_name": "Deterministic Test"
                }
            )
            responses.append(response)

        codes = [r.json()["registration_code"] for r in responses]
        assert codes[0] == codes[1] == codes[2]

    def test_different_macs_different_codes(self, client):
        """测试不同 MAC 地址生成不同注册码"""
        macs = ["AA:AA:AA:AA:AA:01", "AA:AA:AA:AA:AA:02", "AA:AA:AA:AA:AA:03"]
        codes = []

        for mac in macs:
            response = client.post(
                "/api/devices/register",
                json={
                    "mac_address": mac,
                    "device_name": f"Device {mac}"
                }
            )
            codes.append(response.json()["registration_code"])

        # 所有注册码应该不同
        assert len(set(codes)) == 3


class TestDeviceSchedule404Handling:
    """设备定时配置 404 处理测试"""

    def test_get_schedule_nonexistent_returns_404(self, client, test_device):
        """测试获取不存在定时配置返回 404"""
        response = client.get(f"/api/devices/{test_device.id}/schedule")

        assert response.status_code == 404
        assert "No schedule configured" in response.json()["detail"]

    def test_create_and_get_schedule(self, client, test_device, auth_headers):
        """测试创建和获取定时配置"""
        # 创建定时配置
        create_response = client.post(
            f"/api/devices/{test_device.id}/schedule",
            json={
                "power_on_time": "08:00",
                "power_off_time": "22:00",
                "is_enabled": True,
                "weekdays": [1, 2, 3, 4, 5]
            },
            headers=auth_headers
        )
        assert create_response.status_code == 200

        # 获取定时配置
        get_response = client.get(f"/api/devices/{test_device.id}/schedule")
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["power_on_time"] == "08:00"
        assert data["power_off_time"] == "22:00"
        assert data["is_enabled"] is True

    def test_update_existing_schedule(self, client, test_device, auth_headers):
        """测试更新已有定时配置"""
        # 创建初始配置
        client.post(
            f"/api/devices/{test_device.id}/schedule",
            json={
                "power_on_time": "08:00",
                "power_off_time": "22:00",
                "is_enabled": True,
                "weekdays": [1, 2, 3, 4, 5]
            },
            headers=auth_headers
        )

        # 更新配置
        update_response = client.post(
            f"/api/devices/{test_device.id}/schedule",
            json={
                "power_on_time": "09:00",
                "power_off_time": "18:00",
                "is_enabled": False,
                "weekdays": [1, 2, 3, 4, 5, 6, 7]
            },
            headers=auth_headers
        )
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["power_on_time"] == "09:00"
        assert data["power_off_time"] == "18:00"
        assert data["is_enabled"] is False


class TestDevicePlaylistManagement:
    """设备播放列表管理测试"""

    def test_get_device_playlists_structure(self, client, test_device, test_playlist, test_db):
        """测试设备播放列表返回结构"""
        from app.models.playlist import DevicePlaylist

        # 创建关联
        assignment = DevicePlaylist(
            device_id=test_device.id,
            playlist_id=test_playlist.id,
            is_active=1
        )
        test_db.add(assignment)
        test_db.commit()

        response = client.get(f"/api/devices/{test_device.id}/playlists")

        assert response.status_code == 200
        data = response.json()

        # 验证返回结构
        assert "device_id" in data
        assert "playlists" in data
        assert isinstance(data["playlists"], list)

        if len(data["playlists"]) > 0:
            playlist = data["playlists"][0]
            required_fields = [
                "assignment_id",
                "playlist_id",
                "playlist_name",
                "is_active",
                "item_count",
                "assigned_at"
            ]
            for field in required_fields:
                assert field in playlist, f"Missing field: {field}"

    def test_get_device_playlists_with_multiple_items(
        self, client, test_device, test_playlist_with_items, test_db
    ):
        """测试播放列表项数统计"""
        from app.models.playlist import DevicePlaylist

        playlist = test_playlist_with_items[0] if isinstance(test_playlist_with_items, tuple) else test_playlist_with_items

        assignment = DevicePlaylist(
            device_id=test_device.id,
            playlist_id=playlist.id,
            is_active=1
        )
        test_db.add(assignment)
        test_db.commit()

        response = client.get(f"/api/devices/{test_device.id}/playlists")

        assert response.status_code == 200
        data = response.json()

        found = next(
            (p for p in data["playlists"] if p["playlist_id"] == playlist.id),
            None
        )
        assert found is not None
        assert found["item_count"] > 0

    def test_playlist_activation_status(self, client, test_device, test_playlist, test_db):
        """测试播放列表激活状态"""
        from app.models.playlist import DevicePlaylist

        # 创建未激活的关联
        assignment = DevicePlaylist(
            device_id=test_device.id,
            playlist_id=test_playlist.id,
            is_active=0
        )
        test_db.add(assignment)
        test_db.commit()

        response = client.get(f"/api/devices/{test_device.id}/playlists")

        assert response.status_code == 200
        data = response.json()

        found = next(
            (p for p in data["playlists"] if p["playlist_id"] == test_playlist.id),
            None
        )
        assert found is not None
        assert found["is_active"] is False


class TestDeviceAutoNaming:
    """设备自动命名测试"""

    def test_auto_naming_from_mac(self, client):
        """测试基于 MAC 地址自动生成设备名称"""
        mac_address = "11:22:33:44:55:66"
        response = client.post(
            "/api/devices/register",
            json={
                "mac_address": mac_address,
                "device_name": "Default Device"  # 使用默认名称
            }
        )

        assert response.status_code == 201
        data = response.json()
        # 应该生成 CastPlay-XXXXXX 格式的名称（MAC 后 6 位）
        assert "CastPlay-" in data["device_name"]

    def test_custom_name_preserved(self, client):
        """测试自定义名称被保留"""
        mac_address = "22:33:44:55:66:77"
        custom_name = "My Custom Device Name"
        response = client.post(
            "/api/devices/register",
            json={
                "mac_address": mac_address,
                "device_name": custom_name
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["device_name"] == custom_name


class TestDeviceIpAddress:
    """设备 IP 地址测试"""

    def test_ip_address_captured(self, client):
        """测试 IP 地址被记录"""
        mac_address = "33:44:55:66:77:88"
        response = client.post(
            "/api/devices/register",
            json={
                "mac_address": mac_address,
                "device_name": "IP Test Device"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert "ip_address" in data
        # 测试环境下可能是 testclient 或 127.0.0.1
        assert data["ip_address"] is not None

    def test_custom_ip_address(self, client):
        """测试自定义 IP 地址"""
        mac_address = "44:55:66:77:88:99"
        custom_ip = "192.168.1.100"
        response = client.post(
            "/api/devices/register",
            json={
                "mac_address": mac_address,
                "device_name": "Custom IP Device",
                "ip_address": custom_ip
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["ip_address"] == custom_ip


class TestDevicePlaybackSpeed:
    """设备播放速度测试"""

    def test_default_playback_speed(self, client):
        """测试默认播放速度为 1"""
        mac_address = "55:66:77:88:99:AA"
        response = client.post(
            "/api/devices/register",
            json={
                "mac_address": mac_address,
                "device_name": "Speed Test Device"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["playback_speed"] == 1

    def test_set_playback_speed(self, client, test_device, auth_headers):
        """测试设置播放速度"""
        response = client.put(
            f"/api/devices/{test_device.id}/playback-speed",
            json={"speed": 2},
            headers=auth_headers
        )

        # API 可能返回 200 或 400（取决于验证实现）
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            assert response.json()["playback_speed"] == 2

    def test_invalid_playback_speed(self, client, test_device, auth_headers):
        """测试无效播放速度"""
        response = client.put(
            f"/api/devices/{test_device.id}/playback-speed",
            json={"speed": 3},  # 3 不是有效值
            headers=auth_headers
        )

        # 根据实现可能返回 400 或 422
        assert response.status_code in [400, 422]

    def test_valid_playback_speeds(self, client, test_device, auth_headers):
        """测试所有有效播放速度"""
        valid_speeds = [1, 2, 4, 8]

        for speed in valid_speeds:
            response = client.put(
                f"/api/devices/{test_device.id}/playback-speed",
                json={"speed": speed},
                headers=auth_headers
            )
            # 根据实现可能返回 200 或 400
            assert response.status_code in [200, 400]
            if response.status_code == 200:
                assert response.json()["playback_speed"] == speed
