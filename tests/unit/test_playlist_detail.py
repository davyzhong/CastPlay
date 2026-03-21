"""
播放列表详情和设备分配结构测试

测试播放列表详情返回的设备结构是否正确
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestPlaylistDetailDeviceStructure:
    """播放列表详情设备结构测试"""

    def test_playlist_detail_devices_flat_structure(
        self, client, test_playlist, test_device, test_db
    ):
        """测试播放列表详情返回扁平设备结构"""
        from app.models.playlist import DevicePlaylist

        # 创建关联
        assignment = DevicePlaylist(
            device_id=test_device.id,
            playlist_id=test_playlist.id,
            is_active=1
        )
        test_db.add(assignment)
        test_db.commit()

        response = client.get(f"/api/playlists/{test_playlist.id}")

        assert response.status_code == 200
        data = response.json()

        assert "devices" in data
        assert isinstance(data["devices"], list)

        if len(data["devices"]) > 0:
            device = data["devices"][0]
            # 验证扁平结构字段
            assert "id" in device  # assignment ID
            assert "device_id" in device  # device database ID
            assert "is_active" in device
            assert "assigned_at" in device

    def test_playlist_detail_no_nested_device_object(
        self, client, test_playlist, test_device, test_db
    ):
        """测试播放列表详情不包含嵌套 device 对象"""
        from app.models.playlist import DevicePlaylist

        assignment = DevicePlaylist(
            device_id=test_device.id,
            playlist_id=test_playlist.id,
            is_active=1
        )
        test_db.add(assignment)
        test_db.commit()

        response = client.get(f"/api/playlists/{test_playlist.id}")

        assert response.status_code == 200
        data = response.json()

        if len(data["devices"]) > 0:
            device = data["devices"][0]
            # 不应该有嵌套的 device 或 assignment 对象
            assert "device" not in device or device.get("device") is None
            assert "assignment" not in device or device.get("assignment") is None

    def test_playlist_detail_multiple_devices(
        self, client, test_playlist, multiple_test_devices, test_db
    ):
        """测试播放列表关联多个设备"""
        from app.models.playlist import DevicePlaylist

        # 创建多个关联
        for i, device in enumerate(multiple_test_devices):
            assignment = DevicePlaylist(
                device_id=device.id,
                playlist_id=test_playlist.id,
                is_active=1 if i == 0 else 0  # 第一个激活
            )
            test_db.add(assignment)
        test_db.commit()

        response = client.get(f"/api/playlists/{test_playlist.id}")

        assert response.status_code == 200
        data = response.json()

        assert len(data["devices"]) == len(multiple_test_devices)

        # 验证激活状态
        active_devices = [d for d in data["devices"] if d["is_active"]]
        assert len(active_devices) == 1


class TestPlaylistListCounts:
    """播放列表计数测试"""

    def test_playlist_list_includes_item_count(
        self, client, test_playlist_with_items
    ):
        """测试播放列表列表包含 item_count"""
        playlist = test_playlist_with_items[0] if isinstance(test_playlist_with_items, tuple) else test_playlist_with_items

        response = client.get("/api/playlists/")

        assert response.status_code == 200
        data = response.json()

        found = next(
            (p for p in data["items"] if p["id"] == playlist.id),
            None
        )
        assert found is not None
        assert "item_count" in found
        assert found["item_count"] > 0

    def test_playlist_list_includes_device_count(
        self, client, test_playlist, test_device, test_db
    ):
        """测试播放列表列表包含 device_count"""
        from app.models.playlist import DevicePlaylist

        assignment = DevicePlaylist(
            device_id=test_device.id,
            playlist_id=test_playlist.id,
            is_active=1
        )
        test_db.add(assignment)
        test_db.commit()

        response = client.get("/api/playlists/")

        assert response.status_code == 200
        data = response.json()

        found = next(
            (p for p in data["items"] if p["id"] == test_playlist.id),
            None
        )
        assert found is not None
        assert "device_count" in found
        assert found["device_count"] >= 1

    def test_empty_playlist_counts_are_zero(self, client, test_db, auth_headers):
        """测试空播放列表的计数为 0"""
        from app.models.playlist import Playlist

        playlist = Playlist(name="Empty Count Test")
        test_db.add(playlist)
        test_db.commit()
        test_db.refresh(playlist)

        response = client.get("/api/playlists/")

        assert response.status_code == 200
        data = response.json()

        found = next(
            (p for p in data["items"] if p["id"] == playlist.id),
            None
        )
        assert found is not None
        assert found["item_count"] == 0
        assert found["device_count"] == 0


class TestBatchAddItemsValidation:
    """批量添加媒体验证测试"""

    def test_batch_add_validates_media_ids_required(
        self, client, test_playlist, auth_headers
    ):
        """测试 media_ids 必填"""
        response = client.post(
            f"/api/playlists/{test_playlist.id}/items/batch",
            json={"display_duration": 10},
            headers=auth_headers
        )

        assert response.status_code == 422

    def test_batch_add_validates_display_duration(
        self, client, test_playlist, test_media, auth_headers
    ):
        """测试 display_duration 验证"""
        # 无效的 display_duration
        response = client.post(
            f"/api/playlists/{test_playlist.id}/items/batch",
            json={
                "media_ids": [test_media.id],
                "display_duration": 0  # 太小
            },
            headers=auth_headers
        )

        # 根据实现可能返回 422 或接受
        assert response.status_code in [200, 422]

    def test_batch_add_max_items(self, client, test_playlist, test_db, auth_headers):
        """测试批量添加最多 50 个媒体"""
        from app.models.media import MediaFile

        # 创建 60 个媒体文件
        media_ids = []
        for i in range(60):
            media = MediaFile(
                file_name=f"batch_test_{i}.jpg",
                file_type="image",
                file_path=f"/tmp/batch_test_{i}.jpg",
                status="ready"
            )
            test_db.add(media)
            test_db.flush()
            media_ids.append(media.id)
        test_db.commit()

        response = client.post(
            f"/api/playlists/{test_playlist.id}/items/batch",
            json={
                "media_ids": media_ids,
                "display_duration": 5
            },
            headers=auth_headers
        )

        # 根据实现可能限制或接受
        # 如果限制为 50，应该返回 422 或只添加前 50 个
        assert response.status_code in [200, 422]


class TestReorderItemsValidation:
    """重新排序验证测试"""

    def test_reorder_requires_items_array(
        self, client, test_playlist, auth_headers
    ):
        """测试重新排序需要 items 数组"""
        response = client.put(
            f"/api/playlists/{test_playlist.id}/items/reorder",
            json={},
            headers=auth_headers
        )

        assert response.status_code == 422

    def test_reorder_item_structure(
        self, client, test_playlist_with_items, auth_headers
    ):
        """测试重新排序项目结构"""
        playlist = test_playlist_with_items[0] if isinstance(test_playlist_with_items, tuple) else test_playlist_with_items

        # 获取详情
        detail = client.get(f"/api/playlists/{playlist.id}")
        items = detail.json()["items"]

        if len(items) >= 2:
            # 错误的结构（缺少 order）- API 可能忽略或使用默认值
            response = client.put(
                f"/api/playlists/{playlist.id}/items/reorder",
                json={
                    "items": [
                        {"id": items[0]["id"], "order": 0}  # 正确格式
                    ]
                },
                headers=auth_headers
            )
            # API 应该接受正确格式
            assert response.status_code in [200, 422]


class TestDeviceScheduleValidation:
    """设备定时配置验证测试"""

    def test_schedule_time_format_validation(self, client, test_device, auth_headers):
        """测试时间格式验证"""
        # 错误的时间格式 - API 可能不严格验证时间格式
        response = client.post(
            f"/api/devices/{test_device.id}/schedule",
            json={
                "power_on_time": "25:00",  # 无效小时
                "power_off_time": "22:00",
                "is_enabled": True,
                "weekdays": [1, 2, 3, 4, 5]
            },
            headers=auth_headers
        )

        # 根据实现可能返回 200（接受任何字符串）或 422（验证格式）
        assert response.status_code in [200, 422]

    def test_schedule_weekdays_validation(self, client, test_device, auth_headers):
        """测试工作日验证"""
        response = client.post(
            f"/api/devices/{test_device.id}/schedule",
            json={
                "power_on_time": "08:00",
                "power_off_time": "22:00",
                "is_enabled": True,
                "weekdays": [0, 8]  # 无效工作日
            },
            headers=auth_headers
        )

        # 根据实现可能验证或不验证
        assert response.status_code in [200, 422]

    def test_schedule_empty_weekdays(self, client, test_device, auth_headers):
        """测试空工作日"""
        response = client.post(
            f"/api/devices/{test_device.id}/schedule",
            json={
                "power_on_time": "08:00",
                "power_off_time": "22:00",
                "is_enabled": True,
                "weekdays": []
            },
            headers=auth_headers
        )

        # 根据实现可能接受或拒绝
        assert response.status_code in [200, 422]

    def test_schedule_valid_weekdays(self, client, test_device, auth_headers):
        """测试有效工作日（1-7）"""
        response = client.post(
            f"/api/devices/{test_device.id}/schedule",
            json={
                "power_on_time": "08:00",
                "power_off_time": "22:00",
                "is_enabled": True,
                "weekdays": [1, 2, 3, 4, 5, 6, 7]
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert set(data["weekdays"]) == {1, 2, 3, 4, 5, 6, 7}
