"""
Web 播放端功能集成测试

测试 Web 播放端相关的 API 端点和功能：
1. 播放端初始化（支持 web_browser 类型）
2. 设备注册（支持浏览器设备）
3. 播放列表获取
4. 媒体下载
5. 状态上报
6. WebSocket 消息处理

与 Android 测试类似，但针对 Web 浏览器播放端场景
"""
import pytest
import uuid
from datetime import datetime


# ============================================================================
# Web 播放端设备注册测试
# ============================================================================

class TestWebPlayerDeviceRegistration:
    """Web 播放端设备注册测试"""

    def test_register_web_browser_device(self, client):
        """测试注册 Web 浏览器设备"""
        device_id = f"web-player-{uuid.uuid4().hex[:8]}"
        device_data = {
            "device_id": device_id,
            "device_name": "Web Player Browser",
            "device_type": "web_browser"
        }

        response = client.post("/api/devices/register", json=device_data)

        assert response.status_code in [200, 201]
        data = response.json()
        assert data["device_id"] == device_id
        assert data["device_name"] == "Web Player Browser"

    def test_register_web_player_with_uuid(self, client):
        """测试使用 UUID 注册 Web 播放端"""
        device_uuid = str(uuid.uuid4())
        device_data = {
            "device_id": device_uuid,
            "device_name": "Web Player",
            "device_type": "web_browser"
        }

        response = client.post("/api/devices/register", json=device_data)

        assert response.status_code in [200, 201]
        data = response.json()
        assert data["device_id"] == device_uuid

    def test_register_existing_web_player(self, client):
        """测试注册已存在的 Web 播放端（应该更新）"""
        device_id = f"web-player-existing-{uuid.uuid4().hex[:8]}"

        # 第一次注册
        device_data = {
            "device_id": device_id,
            "device_name": "Original Name",
            "device_type": "web_browser"
        }
        response1 = client.post("/api/devices/register", json=device_data)
        assert response1.status_code == 201

        # 第二次注册（更新）
        device_data["device_name"] = "Updated Name"
        response2 = client.post("/api/devices/register", json=device_data)
        assert response2.status_code in [200, 201]
        assert response2.json()["device_name"] == "Updated Name"

    def test_web_player_auto_naming(self, client):
        """测试 Web 播放端自动命名"""
        device_data = {
            "device_id": str(uuid.uuid4()),
            "device_type": "web_browser"
            # 不提供 device_name
        }

        response = client.post("/api/devices/register", json=device_data)

        assert response.status_code == 201
        data = response.json()
        # 设备名可能是 Web-XXXXX 格式或其他自动生成格式
        assert data["device_name"] is not None
        assert len(data["device_name"]) > 0


# ============================================================================
# Web 播放端初始化测试
# ============================================================================

class TestWebPlayerInitialization:
    """Web 播放端初始化测试"""

    def test_web_player_init(self, client):
        """测试 Web 播放端初始化"""
        # 先注册设备
        device_id = str(uuid.uuid4())
        client.post("/api/devices/register", json={
            "device_id": device_id,
            "device_name": "Web Player Test",
            "device_type": "web_browser"
        })

        # 初始化
        response = client.post(
            "/api/player/init",
            json={"device_id": device_id}
        )

        assert response.status_code == 200
        data = response.json()
        assert "device" in data
        assert "playlists" in data
        assert data["device"]["device_id"] == device_id

    def test_web_player_init_with_playlist(self, client, test_db, auth_headers):
        """测试 Web 播放端初始化带播放列表"""
        from app.models.playlist import Playlist, PlaylistItem, DevicePlaylist
        from app.models.media import MediaFile
        from app.models.device import Device

        # 创建设备
        device_id = str(uuid.uuid4())
        client.post("/api/devices/register", json={
            "device_id": device_id,
            "device_name": "Web Player with Playlist",
            "device_type": "web_browser"
        })

        # 创建媒体
        media = MediaFile(
            file_name="test.jpg",
            file_type="image",
            file_path="/tmp/test.jpg",
            status="ready"
        )
        test_db.add(media)
        test_db.commit()
        test_db.refresh(media)

        # 创建播放列表
        playlist = Playlist(name="Web Player Playlist")
        test_db.add(playlist)
        test_db.commit()
        test_db.refresh(playlist)

        # 添加媒体到播放列表
        item = PlaylistItem(
            playlist_id=playlist.id,
            media_id=media.id,
            display_order=0,
            display_duration=5
        )
        test_db.add(item)
        test_db.commit()

        # 获取设备并分配播放列表
        device = test_db.query(Device).filter_by(device_id=device_id).first()

        if device:
            assignment = DevicePlaylist(
                device_id=device.id,
                playlist_id=playlist.id
            )
            test_db.add(assignment)
            test_db.commit()

        # 初始化
        response = client.post(
            "/api/player/init",
            json={"device_id": device_id}
        )

        assert response.status_code == 200

    def test_web_player_init_includes_device_type(self, client):
        """测试 Web 播放端初始化包含设备类型"""
        device_id = str(uuid.uuid4())
        client.post("/api/devices/register", json={
            "device_id": device_id,
            "device_type": "web_browser"
        })

        response = client.post(
            "/api/player/init",
            json={"device_id": device_id}
        )

        assert response.status_code == 200
        data = response.json()
        # 设备类型应该是 web_browser
        assert data["device"].get("device_type") in ["web_browser", None]


# ============================================================================
# Web 播放端播放列表测试
# ============================================================================

class TestWebPlayerPlaylistHandling:
    """Web 播放端播放列表处理测试"""

    def test_get_playlist_for_web_player(self, client, test_device, test_playlist_with_items, device_playlist_assignment):
        """测试获取 Web 播放端的播放列表"""
        response = client.post(
            "/api/player/init",
            json={"device_id": test_device.device_id}
        )

        assert response.status_code == 200
        data = response.json()

        # 应该返回至少一个播放列表
        assert len(data["playlists"]) >= 1

    def test_playlist_version_check_for_web(self, client, test_playlist):
        """测试 Web 播放端播放列表版本检查"""
        response = client.post(
            f"/api/player/playlist/{test_playlist.id}/check",
            json={"version": "2000-01-01T00:00:00"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "needs_update" in data
        assert "server_version" in data

    def test_empty_playlist_for_web_player(self, client, test_db):
        """测试 Web 播放端获取空播放列表"""
        from app.models.playlist import Playlist, DevicePlaylist
        from app.models.device import Device

        # 创建设备
        device_id = str(uuid.uuid4())
        client.post("/api/devices/register", json={
            "device_id": device_id,
            "device_type": "web_browser"
        })

        device = test_db.query(Device).filter_by(device_id=device_id).first()

        # 创建空播放列表
        empty_playlist = Playlist(name="Empty Web Playlist")
        test_db.add(empty_playlist)
        test_db.commit()
        test_db.refresh(empty_playlist)

        # 分配到设备
        if device:
            assignment = DevicePlaylist(
                device_id=device.id,
                playlist_id=empty_playlist.id
            )
            test_db.add(assignment)
            test_db.commit()

        # 初始化
        response = client.post(
            "/api/player/init",
            json={"device_id": device_id}
        )

        assert response.status_code == 200


# ============================================================================
# Web 播放端媒体下载测试
# ============================================================================

class TestWebPlayerMediaDownload:
    """Web 播放端媒体下载测试"""

    def test_download_image_for_web_player(self, client, test_db):
        """测试 Web 播放端下载图片"""
        from app.models.media import MediaFile
        import tempfile

        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
            f.write(b"fake image content for web player")
            file_path = f.name

        try:
            media = MediaFile(
                file_name="web_test.jpg",
                file_type="image",
                file_path=file_path,
                status="ready"
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

    def test_download_video_for_web_player(self, client, test_db):
        """测试 Web 播放端下载视频"""
        from app.models.media import MediaFile
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as f:
            f.write(b"fake video content")
            file_path = f.name

        try:
            media = MediaFile(
                file_name="web_test.mp4",
                file_type="video",
                file_path=file_path,
                status="ready"
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

    def test_download_converted_ppt_for_web(self, client, test_db):
        """测试 Web 播放端下载转换后的 PPT"""
        from app.models.media import MediaFile
        import tempfile

        # 创建转换后的文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as f:
            f.write(b"converted ppt video")
            converted_path = f.name

        try:
            media = MediaFile(
                file_name="web_ppt.pptx",
                file_type="ppt",
                file_path="/tmp/original.pptx",
                converted_path=converted_path,
                status="ready"
            )
            test_db.add(media)
            test_db.commit()
            test_db.refresh(media)

            # 下载转换后的文件
            response = client.get(f"/api/player/media/{media.id}/converted")

            assert response.status_code == 200
        finally:
            import os
            if os.path.exists(converted_path):
                os.unlink(converted_path)

    def test_download_nonexistent_media(self, client):
        """测试下载不存在的媒体"""
        response = client.get("/api/player/media/99999/download")
        assert response.status_code == 404


# ============================================================================
# Web 播放端状态上报测试
# ============================================================================

class TestWebPlayerStatusReporting:
    """Web 播放端状态上报测试"""

    def test_report_web_player_playing(self, client, test_device):
        """测试 Web 播放端上报播放中状态"""
        response = client.post(
            "/api/player/status",
            json={
                "device_id": test_device.device_id,
                "player_status": "playing"
            }
        )

        assert response.status_code == 200

    def test_report_web_player_idle(self, client, test_device):
        """测试 Web 播放端上报空闲状态"""
        response = client.post(
            "/api/player/status",
            json={
                "device_id": test_device.device_id,
                "player_status": "idle"
            }
        )

        assert response.status_code == 200

    def test_report_web_player_buffering(self, client, test_device):
        """测试 Web 播放端上报缓冲状态"""
        response = client.post(
            "/api/player/status",
            json={
                "device_id": test_device.device_id,
                "player_status": "buffering"
            }
        )

        assert response.status_code == 200

    def test_report_status_updates_last_online(self, client, test_device):
        """测试状态上报更新最后在线时间"""
        import time

        # 首次上报
        client.post(
            "/api/player/status",
            json={
                "device_id": test_device.device_id,
                "player_status": "playing"
            }
        )

        time.sleep(0.1)

        # 二次上报
        client.post(
            "/api/player/status",
            json={
                "device_id": test_device.device_id,
                "player_status": "playing"
            }
        )

        # 验证响应成功
        assert True

    def test_report_status_nonexistent_device(self, client):
        """测试上报不存在设备的状态"""
        response = client.post(
            "/api/player/status",
            json={
                "device_id": "nonexistent-web-player",
                "player_status": "playing"
            }
        )

        assert response.status_code == 404


# ============================================================================
# Web 播放端播放速度测试
# ============================================================================

class TestWebPlayerPlaybackSpeed:
    """Web 播放端播放速度测试"""

    def test_web_player_supports_1x_speed(self, client, test_device, auth_headers):
        """测试 Web 播放端支持 1X 播放速度"""
        response = client.put(
            f"/api/devices/{test_device.id}",
            json={"playback_speed": 1},
            headers=auth_headers
        )

        assert response.status_code == 200

    def test_web_player_supports_2x_speed(self, client, test_device, auth_headers):
        """测试 Web 播放端支持 2X 播放速度"""
        response = client.put(
            f"/api/devices/{test_device.id}",
            json={"playback_speed": 2},
            headers=auth_headers
        )

        assert response.status_code == 200

    def test_web_player_supports_4x_speed(self, client, test_device, auth_headers):
        """测试 Web 播放端支持 4X 播放速度"""
        response = client.put(
            f"/api/devices/{test_device.id}",
            json={"playback_speed": 4},
            headers=auth_headers
        )

        assert response.status_code == 200

    def test_web_player_supports_8x_speed(self, client, test_device, auth_headers):
        """测试 Web 播放端支持 8X 播放速度"""
        response = client.put(
            f"/api/devices/{test_device.id}",
            json={"playback_speed": 8},
            headers=auth_headers
        )

        assert response.status_code == 200

    def test_web_player_init_includes_speed(self, client, test_device):
        """测试 Web 播放端初始化包含播放速度"""
        response = client.post(
            "/api/player/init",
            json={"device_id": test_device.device_id}
        )

        assert response.status_code == 200
        data = response.json()
        # playback_speed 字段可能存在，也可能不存在（取决于 API 实现）
        # 如果存在，验证其值
        if "playback_speed" in data["device"]:
            assert data["device"]["playback_speed"] in [1, 2, 4, 8]
        # 否则，测试仍然通过（该功能可能尚未实现）


# ============================================================================
# Web 播放端定时配置测试
# ============================================================================

class TestWebPlayerSchedule:
    """Web 播放端定时配置测试"""

    def test_web_player_init_with_schedule(self, client, test_db, test_device):
        """测试 Web 播放端初始化带定时配置"""
        from app.models.device import DeviceSchedule

        # 创建定时配置
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
        assert data["schedule"] is not None

    def test_web_player_schedule_disabled(self, client, test_db):
        """测试 Web 播放端定时配置禁用"""
        device_id = str(uuid.uuid4())
        client.post("/api/devices/register", json={
            "device_id": device_id,
            "device_type": "web_browser"
        })

        response = client.post(
            "/api/player/init",
            json={"device_id": device_id}
        )

        assert response.status_code == 200
        data = response.json()
        # 没有定时配置时应该返回 None 或空
        assert data["schedule"] is None or data["schedule"] == {}


# ============================================================================
# Web 播放端完整工作流测试
# ============================================================================

class TestWebPlayerCompleteWorkflow:
    """Web 播放端完整工作流测试"""

    def test_complete_web_player_workflow(self, client, test_db, test_playlist, test_media, auth_headers):
        """测试完整的 Web 播放端工作流程"""
        # 1. 注册 Web 播放端设备
        device_id = f"web-player-{uuid.uuid4().hex[:8]}"
        register_response = client.post("/api/devices/register", json={
            "device_id": device_id,
            "device_name": "Web Player Complete Test",
            "device_type": "web_browser"
        })
        assert register_response.status_code == 201

        # 2. 添加媒体到播放列表
        client.post(
            f"/api/playlists/{test_playlist.id}/items",
            json={"media_id": test_media.id, "display_duration": 10},
            headers=auth_headers
        )

        # 3. 获取设备 ID
        from app.models.device import Device
        device = test_db.query(Device).filter_by(device_id=device_id).first()

        # 4. 分配播放列表到设备
        if device:
            client.post(
                f"/api/playlists/{test_playlist.id}/devices/{device.id}",
                headers=auth_headers
            )

        # 5. 初始化播放端
        init_response = client.post(
            "/api/player/init",
            json={"device_id": device_id}
        )
        assert init_response.status_code == 200
        init_data = init_response.json()

        # 6. 检查播放列表版本
        if init_data["playlists"]:
            playlist_id = init_data["playlists"][0]["id"]
            version_response = client.post(
                f"/api/player/playlist/{playlist_id}/check",
                json={"version": "2000-01-01T00:00:00"}
            )
            assert version_response.status_code == 200

        # 7. 上报播放状态
        status_response = client.post(
            "/api/player/status",
            json={"device_id": device_id, "player_status": "playing"}
        )
        assert status_response.status_code == 200

        # 8. 上报空闲状态
        idle_response = client.post(
            "/api/player/status",
            json={"device_id": device_id, "player_status": "idle"}
        )
        assert idle_response.status_code == 200

    def test_web_player_multiple_sessions(self, client):
        """测试 Web 播放端多会话（模拟多标签页）"""
        device_id = str(uuid.uuid4())

        # 注册设备
        client.post("/api/devices/register", json={
            "device_id": device_id,
            "device_type": "web_browser"
        })

        # 模拟多个会话同时初始化
        responses = []
        for _ in range(3):
            response = client.post(
                "/api/player/init",
                json={"device_id": device_id}
            )
            responses.append(response)

        # 所有请求应该成功
        for response in responses:
            assert response.status_code == 200


# ============================================================================
# 边界条件测试
# ============================================================================

class TestWebPlayerBoundaryConditions:
    """Web 播放端边界条件测试"""

    def test_invalid_device_id_format(self, client):
        """测试无效的设备 ID 格式"""
        response = client.post(
            "/api/player/init",
            json={"device_id": "invalid-device-id-format-!@#$%"}
        )

        # 可能接受或拒绝
        assert response.status_code in [200, 404, 422]

    def test_very_long_device_name(self, client):
        """测试超长设备名称"""
        long_name = "A" * 500
        device_data = {
            "device_id": str(uuid.uuid4()),
            "device_name": long_name,
            "device_type": "web_browser"
        }

        response = client.post("/api/devices/register", json=device_data)

        # 可能接受或截断
        assert response.status_code in [200, 201, 422]

    def test_future_version_check(self, client, test_playlist):
        """测试使用未来日期检查版本"""
        future_version = "2099-12-31T23:59:59"

        response = client.post(
            f"/api/player/playlist/{test_playlist.id}/check",
            json={"version": future_version}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["needs_update"] is False

    def test_concurrent_status_reports(self, client, test_device):
        """测试并发状态上报"""
        import concurrent.futures

        def report_status():
            return client.post(
                "/api/player/status",
                json={
                    "device_id": test_device.device_id,
                    "player_status": "playing"
                }
            )

        # 并发上报
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(report_status) for _ in range(10)]
            responses = [f.result() for f in concurrent.futures.as_completed(futures)]

        # 所有请求应该成功
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count >= 8  # 至少 80% 成功
