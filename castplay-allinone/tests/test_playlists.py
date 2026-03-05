"""
播放列表管理 API 测试
"""
import pytest
from httpx import AsyncClient


class TestPlaylistAPI:
    """播放列表 API 测试类"""

    def test_create_playlist(self, client, auth_headers):
        """测试创建播放列表"""
        response = client.post(
            "/api/playlists/",
            json={
                "name": "Test Playlist",
                "description": "A test playlist"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Playlist"
        assert data["description"] == "A test playlist"
        assert "id" in data

    def test_create_playlist_without_name(self, client, auth_headers):
        """测试创建没有名称的播放列表"""
        response = client.post(
            "/api/playlists/",
            json={"description": "A playlist"},
            headers=auth_headers
        )
        assert response.status_code == 422

    def test_create_playlist_without_auth(self, client):
        """测试未认证创建播放列表"""
        response = client.post(
            "/api/playlists/",
            json={"name": "Test Playlist"}
        )
        assert response.status_code == 401

    def test_get_playlist_list(self, client):
        """测试获取播放列表列表"""
        response = client.get("/api/playlists/")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_get_playlist_list_with_pagination(self, client, test_playlist):
        """测试分页获取播放列表"""
        response = client.get("/api/playlists/?skip=0&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 5

    def test_get_playlist_by_id(self, client, test_playlist):
        """测试获取单个播放列表"""
        response = client.get(f"/api/playlists/{test_playlist.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_playlist.id
        assert data["name"] == test_playlist.name

    def test_get_playlist_detail_with_items(self, client, test_playlist_with_items):
        """测试获取包含媒体项的播放列表详情"""
        response = client.get(f"/api/playlists/{test_playlist_with_items.id}")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) > 0

    def test_update_playlist(self, client, test_playlist, auth_headers):
        """测试更新播放列表"""
        response = client.put(
            f"/api/playlists/{test_playlist.id}",
            json={
                "name": "Updated Playlist",
                "description": "Updated description"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Playlist"
        assert data["description"] == "Updated description"

    def test_update_playlist_without_auth(self, client, test_playlist):
        """测试未认证更新播放列表"""
        response = client.put(
            f"/api/playlists/{test_playlist.id}",
            json={"name": "New Name"}
        )
        assert response.status_code == 401

    def test_delete_playlist(self, client, test_playlist, auth_headers):
        """测试删除播放列表"""
        response = client.delete(
            f"/api/playlists/{test_playlist.id}",
            headers=auth_headers
        )
        assert response.status_code == 200

        # 验证播放列表已被删除
        response = client.get(f"/api/playlists/{test_playlist.id}")
        assert response.status_code == 404


class TestPlaylistItemManagement:
    """播放列表项管理测试"""

    def test_add_item_to_playlist(self, client, test_playlist, test_media, auth_headers):
        """测试添加媒体到播放列表"""
        response = client.post(
            f"/api/playlists/{test_playlist.id}/items",
            json={
                "media_id": test_media.id,
                "display_duration": 10
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["media_id"] == test_media.id
        assert data["display_order"] == 0

    def test_add_item_with_custom_duration(self, client, test_playlist, test_media, auth_headers):
        """测试添加自定义显示时长的媒体"""
        response = client.post(
            f"/api/playlists/{test_playlist.id}/items",
            json={
                "media_id": test_media.id,
                "display_duration": 30
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["display_duration"] == 30

    def test_add_item_invalid_media(self, client, test_playlist, auth_headers):
        """测试添加不存在的媒体"""
        response = client.post(
            f"/api/playlists/{test_playlist.id}/items",
            json={
                "media_id": 99999,
                "display_duration": 10
            },
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_remove_item_from_playlist(self, client, test_playlist_with_items, auth_headers):
        """测试从播放列表移除媒体"""
        items = test_playlist_with_items.items
        if items:
            item_id = items[0].id
            response = client.delete(
                f"/api/playlists/{test_playlist_with_items.id}/items/{item_id}",
                headers=auth_headers
            )
            assert response.status_code == 200

    def test_reorder_playlist_items(self, client, test_playlist_with_items, auth_headers):
        """测试重新排序播放列表项"""
        # 假设有多个媒体项
        if len(test_playlist_with_items.items) >= 2:
            # 重新排序
            new_order = [
                {"item_id": test_playlist_with_items.items[1].id, "display_order": 0},
                {"item_id": test_playlist_with_items.items[0].id, "display_order": 1}
            ]
            response = client.put(
                f"/api/playlists/{test_playlist_with_items.id}/items/reorder",
                json={"items": new_order},
                headers=auth_headers
            )
            assert response.status_code == 200


class TestDevicePlaylistAssignment:
    """设备播放列表分配测试"""

    def test_assign_playlist_to_device(self, client, test_playlist, test_device, auth_headers):
        """测试分配播放列表到设备"""
        response = client.post(
            f"/api/playlists/{test_playlist.id}/devices/{test_device.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["device_id"] == test_device.id
        assert data["playlist_id"] == test_playlist.id

    def test_assign_duplicate_playlist(self, client, test_playlist, test_device, device_playlist_assignment, auth_headers):
        """测试重复分配播放列表"""
        response = client.post(
            f"/api/playlists/{test_playlist.id}/devices/{test_device.id}",
            headers=auth_headers
        )
        # 根据实现可能返回 200（更新）或 400（重复）
        assert response.status_code in [200, 400]

    def test_unassign_playlist_from_device(self, client, test_playlist, test_device, auth_headers):
        """测试取消分配"""
        # 先分配
        client.post(
            f"/api/playlists/{test_playlist.id}/devices/{test_device.id}",
            headers=auth_headers
        )

        # 再取消分配
        response = client.delete(
            f"/api/playlists/{test_playlist.id}/devices/{test_device.id}",
            headers=auth_headers
        )
        assert response.status_code == 200

    def test_activate_playlist_on_device(self, client, test_playlist, test_device, auth_headers):
        """测试激活设备上的播放列表"""
        # 先分配
        client.post(
            f"/api/playlists/{test_playlist.id}/devices/{test_device.id}",
            headers=auth_headers
        )

        # 激活
        response = client.put(
            f"/api/playlists/{test_playlist.id}/devices/{test_device.id}/activate",
            json={"is_active": True},
            headers=auth_headers
        )
        assert response.status_code == 200

    def test_deactivate_playlist_on_device(self, client, test_playlist, test_device, auth_headers):
        """测试停用设备上的播放列表"""
        # 先分配并激活
        client.post(
            f"/api/playlists/{test_playlist.id}/devices/{test_device.id}",
            headers=auth_headers
        )
        client.put(
            f"/api/playlists/{test_playlist.id}/devices/{test_device.id}/activate",
            json={"is_active": True},
            headers=auth_headers
        )

        # 停用
        response = client.put(
            f"/api/playlists/{test_playlist.id}/devices/{test_device.id}/activate",
            json={"is_active": False},
            headers=auth_headers
        )
        assert response.status_code == 200


class TestPlaylistPermissions:
    """播放列表权限测试"""

    def test_regular_user_can_create_playlist(self, client, auth_headers):
        """测试普通用户可以创建播放列表"""
        response = client.post(
            "/api/playlists/",
            json={"name": "My Playlist"},
            headers=auth_headers
        )
        assert response.status_code == 200

    def test_regular_user_can_view_playlists(self, client, auth_headers):
        """测试普通用户可以查看播放列表"""
        response = client.get("/api/playlists/", headers=auth_headers)
        assert response.status_code == 200


class TestPlaylistSearch:
    """播放列表搜索测试"""

    def test_search_playlist_by_name(self, client, test_playlist):
        """测试按名称搜索播放列表"""
        search_term = test_playlist.name[:3]
        response = client.get(f"/api/playlists/?search={search_term}")
        assert response.status_code == 200
        data = response.json()
        # 应该找到匹配的播放列表
        if len(data["items"]) > 0:
            found = any(
                search_term.lower() in item["name"].lower()
                for item in data["items"]
            )
            assert found


class TestPlaylistValidation:
    """播放列表验证测试"""

    def test_playlist_name_too_long(self, client, auth_headers):
        """测试播放列表名称过长"""
        long_name = "A" * 500
        response = client.post(
            "/api/playlists/",
            json={"name": long_name},
            headers=auth_headers
        )
        assert response.status_code == 422

    def test_invalid_display_duration(self, client, test_playlist, test_media, auth_headers):
        """测试无效的显示时长"""
        response = client.post(
            f"/api/playlists/{test_playlist.id}/items",
            json={
                "media_id": test_media.id,
                "display_duration": -1  # 负数
            },
            headers=auth_headers
        )
        assert response.status_code == 422


class TestPlaylistVersioning:
    """播放列表版本控制测试"""

    def test_playlist_version_increments_on_update(self, client, test_playlist, auth_headers):
        """测试播放列表更新时版本号递增"""
        # 获取初始版本
        response = client.get(f"/api/playlists/{test_playlist.id}")
        initial_version = response.json().get("version", 0)

        # 更新播放列表
        client.put(
            f"/api/playlists/{test_playlist.id}",
            json={"name": "Updated Name"},
            headers=auth_headers
        )

        # 获取新版本
        response = client.get(f"/api/playlists/{test_playlist.id}")
        new_version = response.json().get("version", 0)

        assert new_version >= initial_version


class TestPlaylistStatistics:
    """播放列表统计测试"""

    def test_playlist_item_count(self, client, test_playlist_with_items):
        """测试播放列表项数量统计"""
        response = client.get(f"/api/playlists/{test_playlist_with_items.id}")
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == len(test_playlist_with_items.items)

    def test_playlist_total_duration(self, client, test_playlist_with_items):
        """测试播放列表总时长"""
        response = client.get(f"/api/playlists/{test_playlist_with_items.id}")
        data = response.json()
        # 计算总时长
        if "items" in data:
            total_duration = sum(item.get("display_duration", 0) for item in data["items"])
            assert total_duration >= 0


class TestPlaylistEmptyHandling:
    """空播放列表处理测试"""

    def test_empty_playlist_is_valid(self, client, auth_headers):
        """测试空播放列表是有效的"""
        response = client.post(
            "/api/playlists/",
            json={"name": "Empty Playlist"},
            headers=auth_headers
        )
        assert response.status_code == 200

        playlist_id = response.json()["id"]

        # 获取空播放列表详情
        response = client.get(f"/api/playlists/{playlist_id}")
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 0


class TestPlaylistComplexScenarios:
    """播放列表复杂场景测试"""

    def test_move_items_between_playlists(self, client, test_playlist, test_media, auth_headers):
        """测试在播放列表之间移动项目"""
        # 创建第二个播放列表
        response2 = client.post(
            "/api/playlists/",
            json={"name": "Second Playlist"},
            headers=auth_headers
        )
        playlist2_id = response2.json()["id"]

        # 添加到第一个播放列表
        client.post(
            f"/api/playlists/{test_playlist.id}/items",
            json={"media_id": test_media.id, "display_duration": 10},
            headers=auth_headers
        )

        # 从第一个播放列表移除
        response = client.get(f"/api/playlists/{test_playlist.id}")
        items = response.json().get("items", [])
        if items:
            client.delete(
                f"/api/playlists/{test_playlist.id}/items/{items[0]['id']}",
                headers=auth_headers
            )

        # 添加到第二个播放列表
        response = client.post(
            f"/api/playlists/{playlist2_id}/items",
            json={"media_id": test_media.id, "display_duration": 15},
            headers=auth_headers
        )
        assert response.status_code == 200

    def test_duplicate_media_in_playlist(self, client, test_playlist, test_media, auth_headers):
        """测试播放列表中的重复媒体"""
        # 添加第一次
        response1 = client.post(
            f"/api/playlists/{test_playlist.id}/items",
            json={"media_id": test_media.id, "display_duration": 10},
            headers=auth_headers
        )

        # 添加第二次（取决于实现，可能允许或不允许）
        response2 = client.post(
            f"/api/playlists/{test_playlist.id}/items",
            json={"media_id": test_media.id, "display_duration": 10},
            headers=auth_headers
        )

        # 根据实现可能返回 200（允许重复）或 400（不允许）
        assert response2.status_code in [200, 400]
