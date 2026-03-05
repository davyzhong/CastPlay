"""
播放列表管理 API 集成测试

测试所有播放列表管理相关的 API 端点
"""
import pytest


# ============================================================================
# 创建播放列表端点测试
# ============================================================================

class TestCreatePlaylistEndpoint:
    """创建播放列表端点测试"""

    def test_create_playlist(self, client, auth_headers):
        """测试创建播放列表"""
        response = client.post(
            "/api/playlists/",
            json={
                "name": "My Playlist",
                "description": "A test playlist"
            },
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My Playlist"
        assert data["description"] == "A test playlist"

    def test_create_playlist_minimal(self, client, auth_headers):
        """测试创建最小播放列表"""
        response = client.post(
            "/api/playlists/",
            json={"name": "Minimal Playlist"},
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal Playlist"
        assert data["description"] is None

    def test_create_playlist_without_auth(self, client):
        """测试未认证创建播放列表"""
        response = client.post(
            "/api/playlists/",
            json={"name": "Test"}
        )

        assert response.status_code in [401, 403]  # Unauthorized or Forbidden

    def test_create_playlist_missing_name(self, client, auth_headers):
        """测试缺少播放列表名称"""
        response = client.post(
            "/api/playlists/",
            json={"description": "No name"},
            headers=auth_headers
        )

        assert response.status_code == 422


# ============================================================================
# 播放列表列表端点测试
# ============================================================================

class TestPlaylistListEndpoint:
    """播放列表列表端点测试"""

    def test_list_playlists(self, client, test_playlist):
        """测试获取播放列表"""
        response = client.get("/api/playlists/")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert "pages" in data
        assert len(data["items"]) >= 1

    def test_list_playlists_pagination(self, client, test_db, auth_headers):
        """测试播放列表分页"""
        # 创建多个播放列表
        from app.models.playlist import Playlist
        for i in range(5):
            playlist = Playlist(name=f"Playlist {i}")
            test_db.add(playlist)
        test_db.commit()

        response = client.get("/api/playlists/?skip=0&limit=2")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 2
        assert data["page"] == 1
        assert data["per_page"] == 2

    def test_list_playlists_skip(self, client, test_db, auth_headers):
        """测试跳过播放列表"""
        from app.models.playlist import Playlist

        playlist1 = Playlist(name="First")
        playlist2 = Playlist(name="Second")
        test_db.add_all([playlist1, playlist2])
        test_db.commit()

        response_1 = client.get("/api/playlists/?skip=0&limit=1")
        response_2 = client.get("/api/playlists/?skip=1&limit=1")

        assert response_1.status_code == 200
        assert response_2.status_code == 200

        data_1 = response_1.json()["items"]
        data_2 = response_2.json()["items"]

        if len(data_1) > 0 and len(data_2) > 0:
            assert data_1[0]["id"] != data_2[0]["id"]


# ============================================================================
# 播放列表详情端点测试
# ============================================================================

class TestPlaylistDetailEndpoint:
    """播放列表详情端点测试"""

    def test_get_playlist_detail(self, client, test_playlist):
        """测试获取播放列表详情"""
        response = client.get(f"/api/playlists/{test_playlist.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_playlist.id
        assert data["name"] == test_playlist.name
        assert "items" in data
        assert "devices" in data

    def test_get_playlist_detail_with_items(self, client, test_playlist_with_items):
        """测试获取包含媒体的播放列表详情"""
        playlist = test_playlist_with_items[0] if isinstance(test_playlist_with_items, tuple) else test_playlist_with_items
        response = client.get(f"/api/playlists/{playlist.id}")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) > 0
        assert data["items"][0]["file_name"] is not None

    def test_get_playlist_detail_with_devices(self, client, test_playlist, test_device, test_db):
        """测试获取包含设备的播放列表详情"""
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
        assert "devices" in data
        assert len(data["devices"]) > 0

    def test_get_nonexistent_playlist(self, client):
        """测试获取不存在的播放列表"""
        response = client.get("/api/playlists/99999")

        assert response.status_code == 404
        assert "Playlist not found" in response.json()["detail"]


# ============================================================================
# 更新播放列表端点测试
# ============================================================================

class TestUpdatePlaylistEndpoint:
    """更新播放列表端点测试"""

    def test_update_playlist_name(self, client, test_playlist, auth_headers):
        """测试更新播放列表名称"""
        response = client.put(
            f"/api/playlists/{test_playlist.id}",
            json={"name": "Updated Name"},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"

    def test_update_playlist_description(self, client, test_playlist, auth_headers):
        """测试更新播放列表描述"""
        response = client.put(
            f"/api/playlists/{test_playlist.id}",
            json={"description": "Updated description"},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"

    def test_update_playlist_all_fields(self, client, test_playlist, auth_headers):
        """测试更新播放列表所有字段"""
        response = client.put(
            f"/api/playlists/{test_playlist.id}",
            json={
                "name": "Fully Updated",
                "description": "Fully updated description"
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Fully Updated"
        assert data["description"] == "Fully updated description"

    def test_update_nonexistent_playlist(self, client, auth_headers):
        """测试更新不存在的播放列表"""
        response = client.put(
            "/api/playlists/99999",
            json={"name": "Test"},
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_update_without_auth(self, client, test_playlist):
        """测试未认证更新播放列表"""
        response = client.put(
            f"/api/playlists/{test_playlist.id}",
            json={"name": "Test"}
        )

        assert response.status_code in [401, 403]  # Unauthorized or Forbidden


# ============================================================================
# 删除播放列表端点测试
# ============================================================================

class TestDeletePlaylistEndpoint:
    """删除播放列表端点测试"""

    def test_delete_playlist(self, client, test_db, auth_headers):
        """测试删除播放列表"""
        from app.models.playlist import Playlist

        playlist = Playlist(name="To Delete")
        test_db.add(playlist)
        test_db.commit()
        test_db.refresh(playlist)

        response = client.delete(f"/api/playlists/{playlist.id}", headers=auth_headers)

        assert response.status_code == 204
        assert response.content == b""

        # 验证播放列表已删除
        deleted = test_db.query(Playlist).filter(Playlist.id == playlist.id).first()
        assert deleted is None

    def test_delete_nonexistent_playlist(self, client, auth_headers):
        """测试删除不存在的播放列表"""
        response = client.delete("/api/playlists/99999", headers=auth_headers)

        assert response.status_code == 404

    def test_delete_without_auth(self, client, test_playlist):
        """测试未认证删除播放列表"""
        response = client.delete(f"/api/playlists/{test_playlist.id}")

        assert response.status_code in [401, 403]  # Unauthorized or Forbidden


# ============================================================================
# 播放列表项端点测试
# ============================================================================

class TestPlaylistItemEndpoint:
    """播放列表项端点测试"""

    def test_add_item_to_playlist(self, client, test_playlist, test_media, auth_headers):
        """测试添加媒体到播放列表"""
        response = client.post(
            f"/api/playlists/{test_playlist.id}/items",
            json={
                "media_id": test_media.id,
                "display_duration": 30
            },
            headers=auth_headers
        )

        assert response.status_code == 200  # API returns 200 for successful add
        data = response.json()
        assert data["media_id"] == test_media.id
        assert data["display_order"] == 0
        assert data["display_duration"] == 30

    def test_add_multiple_items(self, client, test_playlist, multiple_test_media, auth_headers):
        """测试添加多个媒体到播放列表"""
        for media in multiple_test_media:
            response = client.post(
                f"/api/playlists/{test_playlist.id}/items",
                json={
                    "media_id": media.id,
                    "display_duration": 10
                },
                headers=auth_headers
            )
            assert response.status_code in [200, 201, 422]

    def test_add_item_to_nonexistent_playlist(self, client, test_media, auth_headers):
        """测试添加到不存在的播放列表"""
        response = client.post(
            "/api/playlists/99999/items",
            json={"media_id": test_media.id},
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_add_nonexistent_media(self, client, test_playlist, auth_headers):
        """测试添加不存在的媒体"""
        response = client.post(
            f"/api/playlists/{test_playlist.id}/items",
            json={"media_id": 99999},
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_add_item_without_auth(self, client, test_playlist, test_media):
        """测试未认证添加项"""
        response = client.post(
            f"/api/playlists/{test_playlist.id}/items",
            json={"media_id": test_media.id}
        )

        assert response.status_code in [401, 403]  # Unauthorized or Forbidden

    def test_remove_item_from_playlist(self, client, test_playlist_with_items, auth_headers):
        """测试从播放列表移除媒体"""
        playlist = test_playlist_with_items[0] if isinstance(test_playlist_with_items, tuple) else test_playlist_with_items
        # 获取第一个项的 ID
        detail_response = client.get(f"/api/playlists/{playlist.id}")
        items = detail_response.json()["items"]

        if len(items) > 0:
            item_id = items[0]["id"]
            response = client.delete(
                f"/api/playlists/{playlist.id}/items/{item_id}",
                headers=auth_headers
            )

            assert response.status_code == 204

    def test_remove_nonexistent_item(self, client, test_playlist, auth_headers):
        """测试移除不存在的项"""
        response = client.delete(
            f"/api/playlists/{test_playlist.id}/items/99999",
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_remove_item_without_auth(self, client, test_playlist_with_items):
        """测试未认证移除项"""
        playlist = test_playlist_with_items[0] if isinstance(test_playlist_with_items, tuple) else test_playlist_with_items
        detail_response = client.get(f"/api/playlists/{playlist.id}")
        items = detail_response.json()["items"]

        if len(items) > 0:
            item_id = items[0]["id"]
            response = client.delete(
                f"/api/playlists/{playlist.id}/items/{item_id}"
            )

            assert response.status_code in [401, 403]  # Unauthorized or Forbidden


# ============================================================================
# 重新排序端点测试
# ============================================================================

class TestReorderItemsEndpoint:
    """重新排序端点测试"""

    def test_reorder_items(self, client, test_playlist_with_items, auth_headers):
        """测试重新排序播放列表项"""
        playlist = test_playlist_with_items[0] if isinstance(test_playlist_with_items, tuple) else test_playlist_with_items
        detail_response = client.get(f"/api/playlists/{playlist.id}")
        items = detail_response.json()["items"]

        if len(items) >= 2:
            # 交换前两项的顺序
            reorder_data = {
                "items": [
                    {"id": items[0]["id"], "order": 1},
                    {"id": items[1]["id"], "order": 0}
                ]
            }

            response = client.put(
                f"/api/playlists/{playlist.id}/items/reorder",
                json=reorder_data,
                headers=auth_headers
            )

            assert response.status_code == 200
            assert "successfully" in response.json()["message"]

    def test_reorder_items_full_list(self, client, test_playlist_with_items, auth_headers):
        """测试完整重新排序"""
        playlist = test_playlist_with_items[0] if isinstance(test_playlist_with_items, tuple) else test_playlist_with_items
        detail_response = client.get(f"/api/playlists/{playlist.id}")
        items = detail_response.json()["items"]

        # 反转顺序
        reorder_data = {
            "items": [
                {"id": items[i]["id"], "order": len(items) - 1 - i}
                for i in range(len(items))
            ]
        }

        response = client.put(
            f"/api/playlists/{playlist.id}/items/reorder",
            json=reorder_data,
            headers=auth_headers
        )

        assert response.status_code == 200

    def test_reorder_items_nonexistent_playlist(self, client, auth_headers):
        """测试重新排序不存在的播放列表"""
        reorder_data = {"items": [{"id": 1, "order": 0}]}
        response = client.put(
            "/api/playlists/99999/items/reorder",
            json=reorder_data,
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_reorder_items_without_auth(self, client, test_playlist_with_items):
        """测试未认证重新排序"""
        playlist = test_playlist_with_items[0] if isinstance(test_playlist_with_items, tuple) else test_playlist_with_items
        reorder_data = {"items": [{"id": 1, "order": 0}]}
        response = client.put(
            f"/api/playlists/{playlist.id}/items/reorder",
            json=reorder_data
        )

        assert response.status_code in [401, 403]  # Unauthorized or Forbidden


# ============================================================================
# 设备分配端点测试
# ============================================================================

class TestDeviceAssignmentEndpoint:
    """设备分配端点测试"""

    def test_assign_playlist_to_device(self, client, test_playlist, test_device, auth_headers):
        """测试分配播放列表到设备"""
        response = client.post(
            f"/api/playlists/{test_playlist.id}/devices/{test_device.id}",
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["device_id"] == test_device.id
        assert data["playlist_id"] == test_playlist.id
        assert data["is_active"] is True

    def test_assign_duplicate(self, client, test_playlist, test_device, auth_headers):
        """测试重复分配（应该失败）"""
        # 第一次分配
        response1 = client.post(
            f"/api/playlists/{test_playlist.id}/devices/{test_device.id}",
            headers=auth_headers
        )
        assert response1.status_code == 201

        # 第二次分配（相同）
        response2 = client.post(
            f"/api/playlists/{test_playlist.id}/devices/{test_device.id}",
            headers=auth_headers
        )

        assert response2.status_code == 400
        assert "already assigned" in response2.json()["detail"].lower()

    def test_assign_nonexistent_playlist(self, client, test_device, auth_headers):
        """测试分配不存在的播放列表"""
        response = client.post(
            "/api/playlists/99999/devices/1",
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_assign_nonexistent_device(self, client, test_playlist, auth_headers):
        """测试分配到不存在的设备"""
        response = client.post(
            f"/api/playlists/{test_playlist.id}/devices/99999",
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_assign_without_auth(self, client, test_playlist, test_device):
        """测试未认证分配"""
        response = client.post(
            f"/api/playlists/{test_playlist.id}/devices/{test_device.id}"
        )

        assert response.status_code in [401, 403]  # Unauthorized or Forbidden

    def test_unassign_playlist_from_device(self, client, device_playlist_assignment, auth_headers):
        """测试取消设备的播放列表分配"""
        response = client.delete(
            f"/api/playlists/{device_playlist_assignment.playlist_id}/devices/{device_playlist_assignment.device_id}",
            headers=auth_headers
        )

        assert response.status_code == 204

    def test_unassign_nonexistent_assignment(self, client, test_playlist, auth_headers):
        """测试取消不存在的分配"""
        response = client.delete(
            f"/api/playlists/{test_playlist.id}/devices/99999",
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_unassign_without_auth(self, client, device_playlist_assignment):
        """测试未认证取消分配"""
        response = client.delete(
            f"/api/playlists/{device_playlist_assignment.playlist_id}/devices/{device_playlist_assignment.device_id}"
        )

        assert response.status_code in [401, 403]  # Unauthorized or Forbidden


# ============================================================================
# 激活/停用端点测试
# ============================================================================

class TestToggleActivationEndpoint:
    """激活/停用端点测试"""

    def test_activate_playlist(self, client, device_playlist_assignment, auth_headers):
        """测试激活设备上的播放列表"""
        response = client.put(
            f"/api/playlists/{device_playlist_assignment.playlist_id}/devices/{device_playlist_assignment.device_id}/activate",
            params={"is_active": True},
            headers=auth_headers
        )

        assert response.status_code == 200
        assert "activated" in response.json()["message"].lower()

    def test_deactivate_playlist(self, client, device_playlist_assignment, auth_headers):
        """测试停用设备上的播放列表"""
        response = client.put(
            f"/api/playlists/{device_playlist_assignment.playlist_id}/devices/{device_playlist_assignment.device_id}/activate",
            params={"is_active": False},
            headers=auth_headers
        )

        assert response.status_code == 200
        assert "deactivated" in response.json()["message"].lower()

    def test_toggle_nonexistent_assignment(self, client, test_playlist, auth_headers):
        """测试切换不存在的分配"""
        response = client.put(
            f"/api/playlists/{test_playlist.id}/devices/99999/activate",
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_toggle_without_auth(self, client, device_playlist_assignment):
        """测试未认证切换"""
        response = client.put(
            f"/api/playlists/{device_playlist_assignment.playlist_id}/devices/{device_playlist_assignment.device_id}/activate"
        )

        assert response.status_code in [401, 403]  # Unauthorized or Forbidden


# ============================================================================
# 边界条件测试
# ============================================================================

class TestPlaylistBoundaryConditions:
    """播放列表边界条件测试"""

    def test_very_long_name(self, client, auth_headers):
        """测试超长播放列表名称"""
        long_name = "a" * 500
        response = client.post(
            "/api/playlists/",
            json={"name": long_name},
            headers=auth_headers
        )

        assert response.status_code in [201, 422]

    def test_special_characters_name(self, client, auth_headers):
        """测试播放列表名称中的特殊字符"""
        response = client.post(
            "/api/playlists/",
            json={"name": "Playlist@#$%^&*()"},
            headers=auth_headers
        )

        assert response.status_code in [201, 422]

    def test_very_long_description(self, client, auth_headers):
        """测试超长描述"""
        long_desc = "a" * 5000
        response = client.post(
            "/api/playlists/",
            json={"name": "Test", "description": long_desc},
            headers=auth_headers
        )

        assert response.status_code in [201, 422]

    def test_display_duration_boundary(self, client, test_playlist, test_media, auth_headers):
        """测试显示时长边界值"""
        # 测试最小值
        response1 = client.post(
            f"/api/playlists/{test_playlist.id}/items",
            json={"media_id": test_media.id, "display_duration": 1},
            headers=auth_headers
        )

        # 测试大值
        response2 = client.post(
            f"/api/playlists/{test_playlist.id}/items",
            json={"media_id": test_media.id, "display_duration": 3600},
            headers=auth_headers
        )

        assert response1.status_code in [200, 201, 422]
        assert response2.status_code in [200, 201, 422]

    def test_assign_multiple_devices(self, client, test_playlist, multiple_test_devices, auth_headers):
        """测试分配到多个设备"""
        for device in multiple_test_devices:
            response = client.post(
                f"/api/playlists/{test_playlist.id}/devices/{device.id}",
                headers=auth_headers
            )
            assert response.status_code in [201, 400]


# ============================================================================
# 播放列表统计信息测试 (item_count, device_count)
# ============================================================================

class TestPlaylistStatistics:
    """播放列表统计信息测试"""

    def test_list_playlists_with_item_count(self, client, test_playlist_with_items):
        """测试播放列表返回 item_count"""
        # test_playlist_with_items returns (playlist, items)
        playlist = test_playlist_with_items[0] if isinstance(test_playlist_with_items, tuple) else test_playlist_with_items

        response = client.get("/api/playlists/")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data

        # 找到测试播放列表
        found_playlist = next(
            (p for p in data["items"] if p["id"] == playlist.id),
            None
        )
        assert found_playlist is not None
        assert "item_count" in found_playlist
        assert found_playlist["item_count"] > 0

    def test_list_playlists_with_device_count(self, client, test_playlist, test_device, test_db):
        """测试播放列表返回 device_count"""
        from app.models.playlist import DevicePlaylist

        # 创建设备分配
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

        # 找到测试播放列表
        playlist = next(
            (p for p in data["items"] if p["id"] == test_playlist.id),
            None
        )
        assert playlist is not None
        assert "device_count" in playlist
        assert playlist["device_count"] >= 1

    def test_empty_playlist_item_count(self, client, test_db, auth_headers):
        """测试空播放列表的 item_count 为 0"""
        from app.models.playlist import Playlist

        playlist = Playlist(name="Empty Playlist")
        test_db.add(playlist)
        test_db.commit()
        test_db.refresh(playlist)

        response = client.get("/api/playlists/")

        assert response.status_code == 200
        data = response.json()

        # 找到空播放列表
        empty_playlist = next(
            (p for p in data["items"] if p["id"] == playlist.id),
            None
        )
        assert empty_playlist is not None
        assert empty_playlist["item_count"] == 0
        assert empty_playlist["device_count"] == 0

    def test_playlist_with_multiple_items_and_devices(
        self, client, test_db, auth_headers, multiple_test_media, multiple_test_devices
    ):
        """测试包含多个媒体和设备的播放列表统计"""
        from app.models.playlist import Playlist, PlaylistItem, DevicePlaylist

        # 创建播放列表
        playlist = Playlist(name="Multi Stats Playlist")
        test_db.add(playlist)
        test_db.commit()
        test_db.refresh(playlist)

        # 添加多个媒体项
        for i, media in enumerate(multiple_test_media[:3]):
            item = PlaylistItem(
                playlist_id=playlist.id,
                media_id=media.id,
                display_order=i,
                display_duration=10
            )
            test_db.add(item)

        # 分配到多个设备
        for device in multiple_test_devices[:2]:
            assignment = DevicePlaylist(
                device_id=device.id,
                playlist_id=playlist.id,
                is_active=1
            )
            test_db.add(assignment)

        test_db.commit()

        response = client.get("/api/playlists/")

        assert response.status_code == 200
        data = response.json()

        # 找到测试播放列表
        found_playlist = next(
            (p for p in data["items"] if p["id"] == playlist.id),
            None
        )
        assert found_playlist is not None
        assert found_playlist["item_count"] == 3
        assert found_playlist["device_count"] == 2


# ============================================================================
# 批量添加媒体测试
# ============================================================================

class TestBatchAddItems:
    """批量添加媒体测试"""

    def test_batch_add_items(self, client, test_playlist, multiple_test_media, auth_headers):
        """测试批量添加媒体到播放列表"""
        media_ids = [m.id for m in multiple_test_media[:3]]

        response = client.post(
            f"/api/playlists/{test_playlist.id}/items/batch",
            json={
                "media_ids": media_ids,
                "display_duration": 5
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "added_count" in data
        assert data["added_count"] == 3
        assert len(data["items"]) == 3
        assert data["failed_media_ids"] == []

    def test_batch_add_items_partial_failure(self, client, test_playlist, test_media, auth_headers):
        """测试批量添加部分失败（部分媒体 ID 不存在）"""
        response = client.post(
            f"/api/playlists/{test_playlist.id}/items/batch",
            json={
                "media_ids": [test_media.id, 99998, 99999],
                "display_duration": 5
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["added_count"] == 1
        assert len(data["failed_media_ids"]) == 2

    def test_batch_add_items_to_nonexistent_playlist(self, client, test_media, auth_headers):
        """测试批量添加到不存在的播放列表"""
        response = client.post(
            "/api/playlists/99999/items/batch",
            json={
                "media_ids": [test_media.id],
                "display_duration": 5
            },
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_batch_add_items_empty_list(self, client, test_playlist, auth_headers):
        """测试批量添加空媒体列表"""
        response = client.post(
            f"/api/playlists/{test_playlist.id}/items/batch",
            json={
                "media_ids": [],
                "display_duration": 5
            },
            headers=auth_headers
        )

        assert response.status_code == 422

    def test_batch_add_items_without_auth(self, client, test_playlist, test_media):
        """测试未认证批量添加"""
        response = client.post(
            f"/api/playlists/{test_playlist.id}/items/batch",
            json={
                "media_ids": [test_media.id],
                "display_duration": 5
            }
        )

        assert response.status_code in [401, 403]
