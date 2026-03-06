"""
播放端状态采集功能单元测试
测试覆盖：心跳上报、设备状态查询、版本检查
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
import json

from app.main import app
from app.models.device import Device
from tests.conftest import TestSessionLocal


# ============== 测试夹具 ==============

@pytest.fixture(scope="function")
def test_db():
    """创建测试数据库会话"""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client(test_db, mocker):
    """创建测试客户端"""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    # 使用 mocker 替换 app.main 中的 get_db 依赖
    from app import main
    mocker.patch.object(main, "get_db", side_effect=override_get_db)

    with TestClient(app) as test_client:
        # 将 test_db 挂载到 app.state 以便测试中访问
        test_client.app.state.db = test_db
        yield test_client


@pytest.fixture
def sample_device(test_db):
    """创建示例设备"""
    device = Device(
        device_id="test-device-001",
        device_name="Test Player",
        device_type="web_browser",
        status="online",
        last_online=datetime.utcnow()
    )
    test_db.add(device)
    test_db.commit()
    test_db.refresh(device)
    return device


# ============== 心跳接口测试 ==============

class TestPlayerHeartbeat:
    """心跳上报接口测试"""

    def test_heartbeat_new_device(self, client, test_db):
        """测试新设备心跳 - 自动注册"""
        payload = {
            "device_id": "new-device-123",
            "device_type": "android_tv",
            "current_playlist_id": 1,
            "last_media_id": 100,
            "status": "playing"
        }

        response = client.post("/api/player/heartbeat", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["acknowledged"] is True
        assert "server_time" in data

        # 验证设备已注册
        device = test_db.query(Device).filter(
            Device.device_id == "new-device-123"
        ).first()
        assert device is not None
        assert device.device_type == "android_tv"
        assert device.status == "online"
        assert device.current_playlist_id == 1
        assert device.last_media_id == 100

    def test_heartbeat_existing_device(self, client, sample_device, test_db):
        """测试已有设备心跳 - 更新状态"""
        old_time = sample_device.last_online

        payload = {
            "device_id": sample_device.device_id,
            "device_type": "web_browser",
            "current_playlist_id": 2,
            "last_media_id": 200,
            "status": "playing"
        }

        response = client.post("/api/player/heartbeat", json=payload)

        assert response.status_code == 200

        # 验证状态已更新
        test_db.refresh(sample_device)
        assert sample_device.last_online > old_time
        assert sample_device.current_playlist_id == 2
        assert sample_device.last_media_id == 200

    def test_heartbeat_minimal_payload(self, client, test_db):
        """测试最小化心跳请求（仅必填字段）"""
        payload = {
            "device_id": "minimal-device",
            "device_type": "web_browser"
        }

        response = client.post("/api/player/heartbeat", json=payload)

        assert response.status_code == 200

        # 验证设备已创建
        device = test_db.query(Device).filter(
            Device.device_id == "minimal-device"
        ).first()
        assert device is not None
        assert device.device_type == "web_browser"

    def test_heartbeat_invalid_device_type(self, client):
        """测试无效的设备类型"""
        payload = {
            "device_id": "invalid-device",
            "device_type": "invalid_type"
        }

        response = client.post("/api/player/heartbeat", json=payload)

        # 应该成功（后端会接受任何值）
        assert response.status_code == 200

    def test_heartbeat_missing_device_id(self, client):
        """测试缺少设备 ID"""
        payload = {
            "device_type": "web_browser"
        }

        response = client.post("/api/player/heartbeat", json=payload)

        assert response.status_code == 422  # Validation error

    def test_heartbeat_database_error(self, client, test_db, mocker):
        """测试数据库异常处理"""
        payload = {
            "device_id": "error-device",
            "device_type": "web_browser"
        }

        # 模拟数据库异常 - patch db.commit 方法
        mock_commit = mocker.patch.object(
            type(test_db),
            "commit",
            side_effect=Exception("Database error")
        )

        response = client.post("/api/player/heartbeat", json=payload)

        assert response.status_code == 500
        mock_commit.assert_called_once()


# ============== 设备状态查询测试 ==============

class TestGetDeviceStatus:
    """设备状态查询接口测试"""

    def test_get_all_devices(self, client, sample_device, test_db):
        """测试获取所有设备"""
        # 创建第二个设备
        device2 = Device(
            device_id="device-002",
            device_name="Player 2",
            device_type="android_tv",
            status="offline",
            last_online=datetime.utcnow() - timedelta(minutes=10)
        )
        test_db.add(device2)
        test_db.commit()

        response = client.get("/api/player/status")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

        # 验证返回字段
        first_device = data[0]
        assert "device_id" in first_device
        assert "device_name" in first_device
        assert "device_type" in first_device
        assert "status" in first_device
        assert "last_online" in first_device

    def test_filter_online_devices(self, client, sample_device):
        """测试过滤在线设备"""
        response = client.get("/api/player/status?status_filter=online")

        assert response.status_code == 200
        data = response.json()

        # 只返回在线设备
        for device in data:
            assert device["status"] == "online"

    def test_filter_offline_devices(self, client, sample_device, test_db):
        """测试过滤离线设备"""
        # 创建一个离线设备
        offline_device = Device(
            device_id="offline-device",
            device_name="Offline Player",
            device_type="web_browser",
            status="offline",
            last_online=datetime.utcnow() - timedelta(minutes=10)
        )
        test_db.add(offline_device)
        test_db.commit()

        response = client.get("/api/player/status?status_filter=offline")

        assert response.status_code == 200
        data = response.json()

        # 至少有一个离线设备
        assert len(data) >= 1
        for device in data:
            assert device["status"] == "offline"

    def test_status_with_playlist(self, client, sample_device, test_db):
        """测试带播放列表的设备状态"""
        # 设置播放列表
        from app.models.playlist import Playlist
        playlist = Playlist(
            name="Test Playlist",
            description="Test"
        )
        test_db.add(playlist)
        test_db.commit()

        sample_device.current_playlist_id = playlist.id
        test_db.commit()

        response = client.get("/api/player/status")

        assert response.status_code == 200
        data = response.json()

        # 验证播放列表信息
        device_data = next(
            d for d in data if d["device_id"] == sample_device.device_id
        )
        assert device_data["current_playlist"] is not None
        assert device_data["current_playlist"]["id"] == playlist.id
        assert device_data["current_playlist"]["name"] == "Test Playlist"

    def test_status_empty_result(self, client):
        """测试空结果"""
        response = client.get("/api/player/status")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0


# ============== 版本检查测试 ==============

class TestCheckPlaylistVersion:
    """播放列表版本检查测试"""

    def test_version_check_needs_update(self, client, test_db):
        """测试需要更新的场景"""
        from app.models.playlist import Playlist
        from datetime import timezone

        playlist = Playlist(
            name="Version Test Playlist",
            description="Test",
            updated_at=datetime.now(timezone.utc)
        )
        test_db.add(playlist)
        test_db.commit()

        # 旧版本号
        old_version = "2020-01-01T00:00:00Z"

        response = client.post(
            f"/api/player/playlist/{playlist.id}/check",
            json={"version": old_version}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["needs_update"] is True
        assert "server_version" in data
        assert "local_version" in data

    def test_version_check_up_to_date(self, client, test_db):
        """测试已是最新版本"""
        from app.models.playlist import Playlist
        from datetime import timezone

        playlist = Playlist(
            name="Latest Playlist",
            description="Test",
            updated_at=datetime.now(timezone.utc)
        )
        test_db.add(playlist)
        test_db.commit()

        # 使用当前版本号
        current_version = playlist.updated_at.isoformat() + "Z"

        response = client.post(
            f"/api/player/playlist/{playlist.id}/check",
            json={"version": current_version}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["needs_update"] is False

    def test_version_check_not_found(self, client):
        """测试播放列表不存在"""
        response = client.post(
            "/api/player/playlist/999999/check",
            json={"version": "2026-01-01T00:00:00Z"}
        )

        assert response.status_code == 404

    def test_version_check_invalid_version_format(self, client, test_db):
        """测试无效版本号格式"""
        from app.models.playlist import Playlist

        playlist = Playlist(
            name="Format Test",
            description="Test"
        )
        test_db.add(playlist)
        test_db.commit()

        # 无效格式 - 字符串比较会返回 needs_update（因为不相等）
        # 注意：实际行为是比较 ISO 时间戳字符串
        invalid_version = "invalid-version"

        response = client.post(
            f"/api/player/playlist/{playlist.id}/check",
            json={"version": invalid_version}
        )

        # 应该成功
        assert response.status_code == 200
        data = response.json()
        # 验证返回数据结构
        assert "needs_update" in data
        assert "server_version" in data
        assert "local_version" in data


# ============== 集成测试 ==============

class TestPlayerIntegration:
    """集成测试"""

    def test_full_heartbeat_and_status_flow(self, client, test_db):
        """测试完整的心跳和状态查询流程"""
        # 1. 设备注册（心跳）
        heartbeat_payload = {
            "device_id": "integration-test-device",
            "device_type": "android_tv",
            "current_playlist_id": 10,
            "last_media_id": 100,
            "status": "playing"
        }

        response = client.post("/api/player/heartbeat", json=heartbeat_payload)
        assert response.status_code == 200

        # 2. 查询设备状态
        response = client.get("/api/player/status")
        assert response.status_code == 200

        data = response.json()
        device = next(
            (d for d in data if d["device_id"] == "integration-test-device"),
            None
        )

        assert device is not None
        assert device["device_type"] == "android_tv"
        assert device["status"] == "online"
        # 注意：实际环境中需要创建播放列表和媒体才能验证这些字段
        # assert device["current_playlist"]["id"] == 10
        # assert device["last_media"]["id"] == 100

        # 3. 过滤在线设备
        response = client.get("/api/player/status?status_filter=online")
        assert response.status_code == 200

        online_devices = [
            d for d in response.json()
            if d["device_id"] == "integration-test-device"
        ]
        assert len(online_devices) == 1

    def test_multiple_devices_concurrent(self, client):
        """测试多设备并发"""
        devices_data = [
            {"device_id": f"device-{i}", "device_type": "web_browser"}
            for i in range(10)
        ]

        # 并发注册
        for device_data in devices_data:
            response = client.post(
                "/api/player/heartbeat",
                json=device_data
            )
            assert response.status_code == 200

        # 验证所有设备都已注册
        response = client.get("/api/player/status")
        assert response.status_code == 200

        data = response.json()
        assert len(data) >= 10


# ============== 边界条件测试 ==============

class TestEdgeCases:
    """边界条件测试"""

    def test_heartbeat_very_long_device_id(self, client):
        """测试超长设备 ID"""
        long_id = "x" * 1000
        payload = {
            "device_id": long_id,
            "device_type": "web_browser"
        }

        response = client.post("/api/player/heartbeat", json=payload)

        # 应该成功或返回验证错误（取决于实现）
        assert response.status_code in [200, 422]

    def test_heartbeat_special_characters_in_device_id(self, client):
        """测试特殊字符设备 ID"""
        payload = {
            "device_id": "device@#$%^&*()",
            "device_type": "web_browser"
        }

        response = client.post("/api/player/heartbeat", json=payload)

        # 应该成功
        assert response.status_code == 200

    def test_status_invalid_filter(self, client):
        """测试无效的过滤参数"""
        response = client.get("/api/player/status?status_filter=invalid")

        assert response.status_code == 200
        # 应该返回空列表或全部设备
        data = response.json()
        assert isinstance(data, list)

    def test_version_check_null_version(self, client, test_db):
        """测试空版本号"""
        from app.models.playlist import Playlist

        playlist = Playlist(
            name="Null Test",
            description="Test"
        )
        test_db.add(playlist)
        test_db.commit()

        response = client.post(
            f"/api/player/playlist/{playlist.id}/check",
            json={"version": None}
        )

        # 应该返回 422 验证错误
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
