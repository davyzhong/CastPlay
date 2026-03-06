"""
播放端增强功能 - 完整单元测试套件
测试新增的所有功能模块
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.models.device_enhancement import (
    DeviceNotificationLog,
    PlaylistDownloadTask,
    PlaylistCleanupSchedule
)
from app.models.base import Base
from app.database import get_db


# ============== 数据库 Fixture ==============

@pytest.fixture(scope="function")
def test_engine():
    """创建测试数据库引擎"""
    from app.models.device import Device, DeviceSchedule
    from app.models.playlist import Playlist, PlaylistItem, DevicePlaylist
    from app.models.media import MediaFile

    engine = create_engine("sqlite:///:memory:")
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db(test_engine):
    """创建测试数据库会话"""
    SessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine)
    db = SessionLocal()
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

    from app import main
    mocker.patch.object(main, "get_db", side_effect=override_get_db)

    with TestClient(app) as test_client:
        test_client.app.state.db = test_db
        yield test_client


# ============== 数据模型测试 ==============

class TestDeviceEnhancementModels:
    """测试新增数据模型"""

    def test_create_notification_log(self, test_db):
        """测试创建通知日志"""
        log = DeviceNotificationLog(
            device_id="test-device-001",
            notification_type="download_success",
            message="Download completed successfully",
            playlist_id=123
        )

        test_db.add(log)
        test_db.commit()

        assert log.id is not None
        assert log.created_at is not None
        assert log.device_id == "test-device-001"
        assert log.notification_type == "download_success"

    def test_create_download_task(self, test_db):
        """测试创建下载任务"""
        task = PlaylistDownloadTask(
            device_id="test-device-002",
            playlist_id=456,
            status="pending",
            retry_count=0
        )

        test_db.add(task)
        test_db.commit()

        assert task.id is not None
        assert task.status == "pending"
        assert task.retry_count == 0

    def test_create_cleanup_schedule(self, test_db):
        """测试创建清理计划"""
        schedule = PlaylistCleanupSchedule(
            playlist_id=789,
            scheduled_time=datetime.utcnow() + timedelta(hours=24),
            executed=False
        )

        test_db.add(schedule)
        test_db.commit()

        assert schedule.id is not None
        assert schedule.executed is False
        assert schedule.scheduled_time > datetime.utcnow()


# ============== 设备通知 API 测试 ==============

class TestDeviceNotificationsAPI:
    """测试设备通知 API"""

    def test_receive_download_success(self, client, test_db, mocker):
        """测试接收下载成功通知"""
        # 修复：正确 mock commit 方法
        mock_commit = mocker.patch.object(type(test_db), "commit")

        response = client.post("/api/player/devices/notifications", json={
            "device_id": "test-device-001",
            "type": "download_success",
            "playlist_id": 123
        })

        assert response.status_code == 200
        data = response.json()
        assert data["acknowledged"] is True

        # 验证数据库调用
        mock_commit.assert_called_once()

    def test_receive_download_failed_with_alert(self, client, test_db, mocker, caplog):
        """测试接收下载失败通知（应触发告警）"""
        mock_commit = mocker.patch.object(type(test_db), "commit")

        response = client.post("/api/player/devices/notifications", json={
            "device_id": "test-device-002",
            "type": "download_failed",
            "playlist_id": 456,
            "error_message": "MD5 mismatch after 3 retries"
        })

        assert response.status_code == 200

        # 验证日志包含告警
        assert "Device alert received" in caplog.text
        assert "download_failed" in caplog.text

    def test_receive_insufficient_storage(self, client, test_db, mocker):
        """测试接收存储空间不足通知"""
        mock_commit = mocker.patch.object(type(test_db), "commit")

        response = client.post("/api/player/devices/notifications", json={
            "device_id": "test-device-003",
            "type": "insufficient_storage",
            "playlist_id": 789,
            "error_message": "Required: 500MB, Available: 100MB"
        })

        assert response.status_code == 200

    def test_receive_switch_failed(self, client, test_db, mocker):
        """测试接收切换失败通知"""
        mock_commit = mocker.patch.object(type(test_db), "commit")

        response = client.post("/api/player/devices/notifications", json={
            "device_id": "test-device-004",
            "type": "switch_failed",
            "playlist_id": 999,
            "error_message": "Failed to switch after playlist ended"
        })

        assert response.status_code == 200


# ============== 可用播放列表 API 测试 ==============

class TestAvailablePlaylistsAPI:
    """测试可用播放列表 API"""

    def test_get_available_playlists_empty(self, client, test_db, mocker):
        """测试获取空播放列表"""
        mock_query = mocker.MagicMock()
        mock_query.filter.return_value.all.return_value = []
        test_db.query = mocker.MagicMock(return_value=mock_query)

        response = client.get("/api/player/playlists/available")

        assert response.status_code == 200
        data = response.json()
        assert len(data["playlists"]) == 0

    def test_get_available_playlists_with_data(self, client, test_db, mocker):
        """测试获取播放列表（有数据）"""
        # Mock 播放列表
        mock_playlist = mocker.MagicMock()
        mock_playlist.id = 1
        mock_playlist.name = "企业宣传片"
        mock_playlist.is_system = True

        # Mock 播放列表项
        mock_item = mocker.MagicMock()
        mock_item.media_file.file_size = 1024 * 1024 * 100  # 100MB

        test_db.query().filter().all.side_effect = [
            [mock_playlist],  # 播放列表查询
            [mock_item]       # 播放列表项查询
        ]

        response = client.get("/api/player/playlists/available")

        assert response.status_code == 200
        data = response.json()
        assert len(data["playlists"]) > 0
        assert data["playlists"][0]["name"] == "企业宣传片"
        assert data["playlists"][0]["media_count"] == 1
        assert data["playlists"][0]["total_size_mb"] > 0


# ============== 心跳推送机制测试 ==============

class TestHeartbeatWithPush:
    """测试心跳推送机制"""

    def test_heartbeat_with_completed_task(self, client, test_db, mocker):
        """测试心跳时有已完成的下载任务"""
        # Mock 已完成的下载任务
        mock_task = mocker.MagicMock()
        mock_task.device_id = "test-device-005"
        mock_task.status = "completed"
        mock_task.playlist_id = 123

        # Mock 播放列表
        mock_playlist = mocker.MagicMock()
        mock_playlist.id = 123
        mock_playlist.name = "新产品介绍"
        mock_playlist.updated_at = None

        # 正确配置 query 链式调用
        mock_query_obj = mocker.MagicMock()
        mock_query_obj.filter.return_value.first.side_effect = [
            mock_task, mock_playlist]
        mock_query_obj.filter.return_value.all.return_value = []

        test_db.query = mocker.MagicMock(return_value=mock_query_obj)

        response = client.post("/api/player/heartbeat", json={
            "device_id": "test-device-005",
            "current_playlist_id": 1,
            "status": "playing"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["playlist_update"] is not None
        assert data["playlist_update"]["has_update"] is True
        assert data["playlist_update"]["playlist_id"] == 123

    def test_heartbeat_without_update(self, client, test_db, mocker):
        """测试心跳时无更新"""
        # Mock 查询返回 None
        mock_query_obj = mocker.MagicMock()
        mock_query_obj.filter.return_value.first.return_value = None

        test_db.query = mocker.MagicMock(return_value=mock_query_obj)

        response = client.post("/api/player/heartbeat", json={
            "device_id": "test-device-006",
            "current_playlist_id": 1,
            "status": "playing"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["playlist_update"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
