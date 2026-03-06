"""
播放端增强功能集成测试
测试新增的 API 接口和功能
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models.device_enhancement import DeviceNotificationLog, PlaylistDownloadTask

client = TestClient(app)


@pytest.fixture
def test_db(mocker):
    """测试数据库夹具"""
    mock_db = mocker.MagicMock(spec=Session)
    return mock_db


class TestDeviceNotifications:
    """设备通知 API 测试"""

    def test_receive_download_success_notification(self, mocker):
        """测试接收下载成功通知"""
        mock_db = mocker.MagicMock()
        mocker.patch("app.api.player.get_db", return_value=mock_db)

        response = client.post("/api/player/devices/notifications", json={
            "device_id": "test-device-001",
            "type": "download_success",
            "playlist_id": 123
        })

        assert response.status_code == 200
        data = response.json()
        assert data["acknowledged"] is True

        # 验证数据库调用
        assert mock_db.add.called
        assert mock_db.commit.called

    def test_receive_download_failed_notification(self, mocker):
        """测试接收下载失败通知"""
        mock_db = mocker.MagicMock()
        mocker.patch("app.api.player.get_db", return_value=mock_db)

        response = client.post("/api/player/devices/notifications", json={
            "device_id": "test-device-002",
            "type": "download_failed",
            "playlist_id": 456,
            "error_message": "MD5 mismatch after 3 retries"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["acknowledged"] is True

        # 验证记录了错误日志
        assert mock_db.add.called
        call_args = mock_db.add.call_args[0][0]
        assert isinstance(call_args, DeviceNotificationLog)
        assert call_args.notification_type == "download_failed"
        assert "MD5 mismatch" in call_args.message

    def test_receive_insufficient_storage_notification(self, mocker):
        """测试接收存储空间不足通知"""
        mock_db = mocker.MagicMock()
        mocker.patch("app.api.player.get_db", return_value=mock_db)

        response = client.post("/api/player/devices/notifications", json={
            "device_id": "test-device-003",
            "type": "insufficient_storage",
            "playlist_id": 789,
            "error_message": "Required: 500MB, Available: 100MB"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["acknowledged"] is True

    def test_receive_switch_failed_notification(self, mocker):
        """测试接收切换失败通知"""
        mock_db = mocker.MagicMock()
        mocker.patch("app.api.player.get_db", return_value=mock_db)

        response = client.post("/api/player/devices/notifications", json={
            "device_id": "test-device-004",
            "type": "switch_failed",
            "playlist_id": 999,
            "error_message": "Failed to switch after playlist ended"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["acknowledged"] is True


class TestAvailablePlaylists:
    """可用播放列表 API 测试"""

    def test_get_available_playlists(self, mocker):
        """测试获取可用播放列表"""
        mock_db = mocker.MagicMock()

        # Mock 播放列表查询
        mock_playlist = mocker.MagicMock()
        mock_playlist.id = 1
        mock_playlist.name = "企业宣传片"
        mock_playlist.is_system = True

        mock_db.query().filter().all.return_value = [mock_playlist]

        # Mock 播放列表项查询
        mock_item = mocker.MagicMock()
        mock_item.media_file.file_size = 1024 * 1024 * 100  # 100MB
        mock_db.query().join().filter().all.return_value = [mock_item]

        mocker.patch("app.api.player.get_db", return_value=mock_db)

        response = client.get("/api/player/playlists/available")

        assert response.status_code == 200
        data = response.json()
        assert "playlists" in data
        assert len(data["playlists"]) > 0
        assert data["playlists"][0]["id"] == 1
        assert data["playlists"][0]["name"] == "企业宣传片"
        assert data["playlists"][0]["media_count"] == 1
        assert data["playlists"][0]["total_size_mb"] > 0


class TestHeartbeatWithPush:
    """心跳推送机制测试"""

    def test_heartbeat_returns_playlist_update(self, mocker):
        """测试心跳时返回播放列表更新信息"""
        mock_db = mocker.MagicMock()

        # Mock 已完成的下载任务
        mock_task = mocker.MagicMock()
        mock_task.device_id = "test-device-005"
        mock_task.status = "completed"
        mock_task.playlist_id = 123

        mock_db.query().filter().first.return_value = mock_task

        # Mock 播放列表
        mock_playlist = mocker.MagicMock()
        mock_playlist.id = 123
        mock_playlist.name = "新产品介绍"
        mock_playlist.updated_at = None

        mocker.patch("app.api.player.get_db", return_value=mock_db)

        response = client.post("/api/player/heartbeat", json={
            "device_id": "test-device-005",
            "current_playlist_id": 1,
            "status": "playing"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["acknowledged"] is True
        assert "playlist_update" in data
        assert data["playlist_update"] is not None
        assert data["playlist_update"]["has_update"] is True
        assert data["playlist_update"]["playlist_id"] == 123

    def test_heartbeat_no_update(self, mocker):
        """测试心跳时无更新"""
        mock_db = mocker.MagicMock()
        mock_db.query().filter().first.return_value = None  # 无下载任务

        mocker.patch("app.api.player.get_db", return_value=mock_db)

        response = client.post("/api/player/heartbeat", json={
            "device_id": "test-device-006",
            "current_playlist_id": 1,
            "status": "playing"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["acknowledged"] is True
        assert data["playlist_update"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
