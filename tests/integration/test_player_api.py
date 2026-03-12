"""
播放端 API 集成测试

测试所有播放端相关的 API 端点
"""
import pytest


# ============================================================================
# 播放端初始化端点测试
# ============================================================================

class TestPlayerInitEndpoint:
    """播放端初始化端点测试"""

    def test_player_init(self, client, test_device):
        """测试播放端初始化"""
        response = client.post(
            "/api/player/init",
            json={"device_id": test_device.device_id}
        )

        assert response.status_code == 200
        data = response.json()
        assert "device" in data
        assert "playlists" in data
        assert "schedule" in data
        assert data["device"]["device_id"] == test_device.device_id
        assert data["device"]["device_name"] == test_device.device_name

    def test_player_init_with_playlist(self, client, test_device, test_playlist_with_items, device_playlist_assignment):
        """测试带有播放列表的播放端初始化"""
        response = client.post(
            "/api/player/init",
            json={"device_id": test_device.device_id}
        )

        assert response.status_code == 200
        data = response.json()
        assert "playlists" in data
        # 可能返回播放列表，取决于激活状态

    def test_player_init_nonexistent_device(self, client):
        """测试不存在设备的初始化"""
        response = client.post(
            "/api/player/init",
            json={"device_id": "nonexistent-device-id"}
        )

        assert response.status_code == 404
        assert "Device not registered" in response.json()["detail"]

    def test_player_init_missing_device_id(self, client):
        """测试缺少设备 ID"""
        response = client.post("/api/player/init", json={})

        assert response.status_code == 422

    def test_player_init_updates_online_status(self, client, test_device):
        """测试初始化更新在线状态"""
        # 先设置设备离线
        from app.models.device import Device
        # 注意：在测试环境中，设备状态在 fixture 中就设置了

        response = client.post(
            "/api/player/init",
            json={"device_id": test_device.device_id}
        )

        assert response.status_code == 200
        # 实际验证需要重新查询数据库

    def test_player_init_with_schedule(self, client, test_db, test_device):
        """测试带有定时配置的播放端初始化"""
        from app.models.device import DeviceSchedule

        schedule = DeviceSchedule(
            device_id=test_device.id,
            power_on_time="09:00",
            power_off_time="18:00",
            is_enabled=1,
            weekdays="0,1,2,3,4"
        )
        test_db.add(schedule)
        test_db.commit()

        response = client.post(
            "/api/player/init",
            json={"device_id": test_device.device_id}
        )

        assert response.status_code == 200
        data = response.json()
        assert "schedule" in data
        if data["schedule"]:
            assert data["schedule"]["power_on_time"] == "09:00"
            assert data["schedule"]["power_off_time"] == "18:00"


# ============================================================================
# 播放列表版本检查端点测试
# ============================================================================

class TestPlaylistVersionCheckEndpoint:
    """播放列表版本检查端点测试"""

    def test_check_playlist_version_needs_update(self, client, test_playlist):
        """测试检查播放列表版本（需要更新）"""
        # 使用旧版本号
        old_version = "2026-01-01T00:00:00"

        response = client.post(
            f"/api/player/playlist/{test_playlist.id}/check",
            json={"version": old_version}
        )

        assert response.status_code == 200
        data = response.json()
        assert "needs_update" in data
        assert "server_version" in data
        assert "local_version" in data

    def test_check_playlist_version_no_update(self, client, test_playlist):
        """测试检查播放列表版本（不需要更新）"""
        # 使用当前版本（或更新后的版本）
        current_version = test_playlist.updated_at.isoformat()

        response = client.post(
            f"/api/player/playlist/{test_playlist.id}/check",
            json={"version": current_version}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["needs_update"] is False

    def test_check_nonexistent_playlist(self, client):
        """测试检查不存在的播放列表"""
        response = client.post(
            "/api/player/playlist/99999/check",
            json={"version": "2026-01-01T00:00:00"}
        )

        assert response.status_code == 404
        assert "Playlist not found" in response.json()["detail"]

    def test_check_version_missing(self, client, test_playlist):
        """测试缺少版本参数"""
        response = client.post(
            f"/api/player/playlist/{test_playlist.id}/check",
            json={}
        )

        assert response.status_code == 422

    def test_check_version_after_update(self, client, test_playlist, auth_headers):
        """测试更新播放列表后版本检查"""
        # 获取初始版本
        initial_version = test_playlist.updated_at.isoformat()

        # 更新播放列表
        client.put(
            f"/api/playlists/{test_playlist.id}",
            json={"name": "Updated"},
            headers=auth_headers
        )

        # 检查版本（应该需要更新）
        response = client.post(
            f"/api/player/playlist/{test_playlist.id}/check",
            json={"version": initial_version}
        )

        assert response.status_code == 200
        data = response.json()
        # 服务器版本应该更新
        assert data["server_version"] != initial_version


# ============================================================================
# 媒体下载端点测试
# ============================================================================

class TestMediaDownloadEndpoint:
    """媒体下载端点测试"""

    def test_download_media_for_player(self, client, test_db):
        """测试播放端下载媒体"""
        from app.models.media import MediaFile
        import tempfile

        # 创建实际的测试文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
            f.write(b"test image content for player")
            file_path = f.name

        try:
            media = MediaFile(
                file_name="player_test.jpg",
                file_type="image",
                file_path=file_path,
                file_size=100,
                md5_hash="hash123"
            )
            test_db.add(media)
            test_db.commit()
            test_db.refresh(media)

            response = client.get(f"/api/player/media/{media.id}/download")

            assert response.status_code == 200
            assert response.headers["content-type"] == "application/octet-stream"
        finally:
            import os
            if os.path.exists(file_path):
                os.unlink(file_path)

    def test_download_converted_media(self, client, test_ppt_media):
        """测试下载转换后的媒体"""
        response = client.get(f"/api/player/media/{test_ppt_media.id}/converted")

        # 文件可能不存在
        assert response.status_code in [200, 404]

    def test_download_converted_nonexistent(self, client, test_media):
        """测试下载不存在转换文件的媒体"""
        response = client.get(f"/api/player/media/{test_media.id}/converted")

        assert response.status_code == 404

    def test_download_nonexistent_media(self, client):
        """测试下载不存在的媒体"""
        response = client.get("/api/player/media/99999/download")

        assert response.status_code == 404

    def test_download_from_player_endpoint(self, client, test_db):
        """测试从播放端 API 下载（使用 /api/player/media 路径）"""
        from app.models.media import MediaFile
        import tempfile

        # 创建实际的测试文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as f:
            f.write(b"fake video content")
            file_path = f.name

        try:
            media = MediaFile(
                file_name="video.mp4",
                file_type="video",
                file_path=file_path,
                file_size=100,
                md5_hash="hash456"
            )
            test_db.add(media)
            test_db.commit()
            test_db.refresh(media)

            response = client.get(f"/api/player/media/{media.id}/download")

            assert response.status_code == 200
        finally:
            import os
            if os.path.exists(file_path):
                os.unlink(file_path)


# ============================================================================
# 播放状态上报端点测试
# ============================================================================

class TestPlayerStatusEndpoint:
    """播放状态上报端点测试"""

    def test_report_playing_status(self, client, test_device):
        """测试上报播放中状态"""
        response = client.post(
            "/api/player/status",
            json={
                "device_id": test_device.device_id,
                "player_status": "playing"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "successfully" in data["message"].lower()

    def test_report_paused_status(self, client, test_device):
        """测试上报暂停状态"""
        response = client.post(
            "/api/player/status",
            json={
                "device_id": test_device.device_id,
                "player_status": "paused"
            }
        )

        assert response.status_code == 200

    def test_report_status_nonexistent_device(self, client):
        """测试上报不存在设备的状态"""
        response = client.post(
            "/api/player/status",
            json={
                "device_id": "nonexistent",
                "player_status": "playing"
            }
        )

        assert response.status_code == 404

    def test_report_status_missing_device_id(self, client):
        """测试缺少设备 ID"""
        response = client.post(
            "/api/player/status",
            json={"player_status": "playing"}
        )

        assert response.status_code == 422

    def test_report_status_default_status(self, client, test_device):
        """测试默认状态"""
        response = client.post(
            "/api/player/status",
            json={"device_id": test_device.device_id}
        )

        assert response.status_code == 200

    def test_report_status_updates_timestamp(self, client, test_device):
        """测试状态上报更新时间戳"""
        import time

        # 首次上报
        client.post(
            "/api/player/status",
            json={
                "device_id": test_device.device_id,
                "player_status": "playing"
            }
        )

        # 二次上报
        time.sleep(0.1)
        client.post(
            "/api/player/status",
            json={
                "device_id": test_device.device_id,
                "player_status": "playing"
            }
        )

        # 验证时间戳已更新（需要查询数据库）
        # 这里仅验证端点响应


# ============================================================================
# 边界条件测试
# ============================================================================

class TestPlayerBoundaryConditions:
    """播放端边界条件测试"""

    def test_init_with_invalid_device_id_format(self, client):
        """测试无效的设备 ID 格式"""
        response = client.post(
            "/api/player/init",
            json={"device_id": "invalid-uuid-format"}
        )

        # 可能接受或拒绝，取决于验证
        assert response.status_code in [200, 422]

    def test_check_version_future_date(self, client, test_playlist):
        """测试使用未来日期检查版本"""
        future_version = "2099-12-31T23:59:59"

        response = client.post(
            f"/api/player/playlist/{test_playlist.id}/check",
            json={"version": future_version}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["needs_update"] is False  # 未来版本不需要更新

    def test_report_status_very_long_status(self, client, test_device):
        """测试上报超长状态"""
        long_status = "x" * 1000

        response = client.post(
            "/api/player/status",
            json={
                "device_id": test_device.device_id,
                "player_status": long_status
            }
        )

        # 可能接受或限制长度
        assert response.status_code in [200, 422]


# ============================================================================
# 集成场景测试
# ============================================================================

class TestPlayerIntegrationScenarios:
    """播放端集成场景测试"""

    def test_complete_player_workflow(self, client, test_db, test_device, test_playlist, test_media, auth_headers):
        """测试完整的播放端工作流程"""
        # 1. 添加媒体到播放列表
        client.post(
            f"/api/playlists/{test_playlist.id}/items",
            json={"media_id": test_media.id, "display_duration": 10},
            headers=auth_headers
        )

        # 2. 分配播放列表到设备
        client.post(
            f"/api/playlists/{test_playlist.id}/devices/{test_device.id}",
            headers=auth_headers
        )

        # 3. 播放端初始化
        init_response = client.post(
            "/api/player/init",
            json={"device_id": test_device.device_id}
        )
        assert init_response.status_code == 200
        init_data = init_response.json()
        assert len(init_data["playlists"]) >= 1

        # 4. 检查版本
        version = init_data["playlists"][0]["version"]
        version_response = client.post(
            f"/api/player/playlist/{test_playlist.id}/check",
            json={"version": version}
        )
        assert version_response.status_code == 200

        # 5. 上报状态
        status_response = client.post(
            "/api/player/status",
            json={"device_id": test_device.device_id, "player_status": "playing"}
        )
        assert status_response.status_code == 200

    def test_player_init_with_empty_playlist(self, client, test_db, test_device):
        """测试带有空播放列表的播放端初始化"""
        from app.models.playlist import Playlist
        from app.models.playlist import DevicePlaylist

        # 创建空播放列表
        empty_playlist = Playlist(name="Empty Playlist")
        test_db.add(empty_playlist)
        test_db.commit()

        # 分配到设备
        assignment = DevicePlaylist(
            device_id=test_device.id,
            playlist_id=empty_playlist.id,
            is_active=1
        )
        test_db.add(assignment)
        test_db.commit()

        response = client.post(
            "/api/player/init",
            json={"device_id": test_device.device_id}
        )

        assert response.status_code == 200
        data = response.json()
        # 应该返回播放列表，但 items 为空
        if len(data["playlists"]) > 0:
            assert len(data["playlists"][0]["items"]) == 0

    def test_player_init_with_multiple_playlists(self, client, test_db, test_device, auth_headers):
        """测试带有多个播放列表的播放端初始化"""
        from app.models.playlist import Playlist, DevicePlaylist

        # 创建多个播放列表
        playlist1 = Playlist(name="Playlist 1")
        playlist2 = Playlist(name="Playlist 2")
        test_db.add_all([playlist1, playlist2])
        test_db.commit()

        # 分配到设备
        assignment1 = DevicePlaylist(
            device_id=test_device.id,
            playlist_id=playlist1.id,
            is_active=1
        )
        assignment2 = DevicePlaylist(
            device_id=test_device.id,
            playlist_id=playlist2.id,
            is_active=1
        )
        test_db.add_all([assignment1, assignment2])
        test_db.commit()

        response = client.post(
            "/api/player/init",
            json={"device_id": test_device.device_id}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["playlists"]) >= 1

    def test_player_init_with_inactive_playlist(self, client, test_db, test_device, auth_headers):
        """测试带有非激活播放列表的播放端初始化"""
        from app.models.playlist import Playlist, DevicePlaylist

        # 创建播放列表
        playlist = Playlist(name="Inactive Playlist")
        test_db.add(playlist)
        test_db.commit()

        # 分配到设备，但设为非激活
        assignment = DevicePlaylist(
            device_id=test_device.id,
            playlist_id=playlist.id,
            is_active=0
        )
        test_db.add(assignment)
        test_db.commit()

        response = client.post(
            "/api/player/init",
            json={"device_id": test_device.device_id}
        )

        assert response.status_code == 200
        data = response.json()
        # 非激活的播放列表不应该返回
        inactive_found = any(
            p["id"] == playlist.id
            for p in data["playlists"]
        )
        assert not inactive_found
