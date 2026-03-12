"""
播放列表管理端到端测试

测试从创建播放列表到播放的完整流程
"""
import pytest


class TestPlaylistCreationToPlayFlow:
    """播放列表创建到播放流程测试"""

    def test_complete_playlist_flow(self, client, test_db, auth_headers):
        """测试完整的播放列表流程：创建 -> 添加媒体 -> 分配设备 -> 播放"""
        # 1. 创建播放列表
        create_response = client.post(
            "/api/playlists/",
            json={
                "name": "Complete Flow Playlist",
                "description": "A complete test playlist"
            },
            headers=auth_headers
        )
        assert create_response.status_code == 201
        playlist_id = create_response.json()["id"]

        # 2. 创建媒体
        from app.models.media import MediaFile
        media = MediaFile(
            file_name="test.jpg",
            file_type="image",
            file_path="/tmp/test.jpg",
            file_size=102400,
            md5_hash="hash123"
        )
        test_db.add(media)
        test_db.commit()

        # 3. 添加媒体到播放列表
        add_item_response = client.post(
            f"/api/playlists/{playlist_id}/items",
            json={
                "media_id": media.id,
                "display_duration": 15
            },
            headers=auth_headers
        )
        assert add_item_response.status_code == 201

        # 4. 验证播放列表详情包含媒体
        detail_response = client.get(f"/api/playlists/{playlist_id}")
        assert detail_response.status_code == 200
        detail_data = detail_response.json()
        assert len(detail_data["items"]) > 0

        # 5. 创建设备
        import uuid
        device_id = str(uuid.uuid4())
        register_response = client.post(
            "/api/devices/register",
            json={"device_id": device_id}
        )
        device_internal_id = register_response.json()["id"]

        # 6. 分配播放列表到设备
        assign_response = client.post(
            f"/api/playlists/{playlist_id}/devices/{device_internal_id}",
            headers=auth_headers
        )
        assert assign_response.status_code == 201

        # 7. 播放端初始化
        init_response = client.post(
            "/api/player/init",
            json={"device_id": device_id}
        )
        assert init_response.status_code == 200
        init_data = init_response.json()
        assert len(init_data["playlists"]) >= 1

        # 8. 检查播放列表版本
        playlist_data = init_data["playlists"][0]
        version = playlist_data.get("version")

        if version:
            version_response = client.post(
                f"/api/player/playlist/{playlist_id}/check",
                json={"version": version}
            )
            assert version_response.status_code == 200

    def test_playlist_items_management_flow(self, client, test_db, auth_headers):
        """测试播放列表项管理流程"""
        # 创建播放列表
        create_response = client.post(
            "/api/playlists/",
            json={"name": "Items Management Playlist"},
            headers=auth_headers
        )
        playlist_id = create_response.json()["id"]

        # 创建多个媒体
        from app.models.media import MediaFile
        media_items = []
        for i in range(3):
            media = MediaFile(
                file_name=f"media_{i}.jpg",
                file_type="image",
                file_path=f"/tmp/media_{i}.jpg",
                file_size=102400,
                md5_hash=f"hash{i}"
            )
            test_db.add(media)
            media_items.append(media)
        test_db.commit()

        # 添加所有媒体到播放列表
        for media in media_items:
            add_response = client.post(
                f"/api/playlists/{playlist_id}/items",
                json={
                    "media_id": media.id,
                    "display_duration": 10
                },
                headers=auth_headers
            )
            assert add_response.status_code == 201

        # 验证所有项目都在播放列表中
        detail_response = client.get(f"/api/playlists/{playlist_id}")
        detail_data = detail_response.json()
        assert len(detail_data["items"]) == 3

        # 重新排序
        items = detail_data["items"]
        if len(items) >= 2:
            reorder_data = {
                "items": [
                    {"id": items[0]["id"], "order": 1},
                    {"id": items[1]["id"], "order": 0}
                ]
            }
            reorder_response = client.put(
                f"/api/playlists/{playlist_id}/items/reorder",
                json=reorder_data,
                headers=auth_headers
            )
            assert reorder_response.status_code == 200

        # 移除一个项目
        if len(items) > 0:
            remove_response = client.delete(
                f"/api/playlists/{playlist_id}/items/{items[0]['id']}",
                headers=auth_headers
            )
            assert remove_response.status_code == 204

            # 验证已移除
            detail_after = client.get(f"/api/playlists/{playlist_id}")
            assert len(detail_after.json()["items"]) == 2

    def test_playlist_device_assignment_flow(self, client, test_db, auth_headers):
        """测试播放列表设备分配流程"""
        # 创建播放列表
        playlist_response = client.post(
            "/api/playlists/",
            json={"name": "Assignment Playlist"},
            headers=auth_headers
        )
        playlist_id = playlist_response.json()["id"]

        # 创建多个设备
        import uuid
        devices = []
        for i in range(2):
            device_id = str(uuid.uuid4())
            response = client.post(
                "/api/devices/register",
                json={
                    "device_id": device_id,
                    "device_name": f"Device {i}"
                }
            )
            devices.append(response.json())

        # 分配播放列表到所有设备
        for device in devices:
            assign_response = client.post(
                f"/api/playlists/{playlist_id}/devices/{device['id']}",
                headers=auth_headers
            )
            assert assign_response.status_code == 201

        # 验证播放列表详情包含所有设备
        detail_response = client.get(f"/api/playlists/{playlist_id}")
        detail_data = detail_response.json()
        assert len(detail_data["devices"]) == 2

        # 停用其中一个设备
        toggle_response = client.put(
            f"/api/playlists/{playlist_id}/devices/{devices[0]['id']}/activate",
            params={"is_active": False},
            headers=auth_headers
        )
        assert toggle_response.status_code == 200

        # 取消分配
        unassign_response = client.delete(
            f"/api/playlists/{playlist_id}/devices/{devices[1]['id']}",
            headers=auth_headers
        )
        assert unassign_response.status_code == 204

        # 验证取消分配后设备列表变化
        detail_after = client.get(f"/api/playlists/{playlist_id}")
        assert len(detail_after.json()["devices"]) == 1

    def test_playlist_update_flow(self, client, test_db, auth_headers):
        """测试播放列表更新流程"""
        # 创建播放列表
        create_response = client.post(
            "/api/playlists/",
            json={
                "name": "Original Name",
                "description": "Original description"
            },
            headers=auth_headers
        )
        playlist_id = create_response.json()["id"]

        # 更新名称
        update1_response = client.put(
            f"/api/playlists/{playlist_id}",
            json={"name": "Updated Name"},
            headers=auth_headers
        )
        assert update1_response.status_code == 200

        # 验证名称已更新
        detail1 = client.get(f"/api/playlists/{playlist_id}")
        assert detail1.json()["name"] == "Updated Name"
        assert detail1.json()["description"] == "Original description"

        # 更新描述
        update2_response = client.put(
            f"/api/playlists/{playlist_id}",
            json={"description": "Updated description"},
            headers=auth_headers
        )
        assert update2_response.status_code == 200

        # 验证描述已更新
        detail2 = client.get(f"/api/playlists/{playlist_id}")
        assert detail2.json()["description"] == "Updated description"

    def test_empty_playlist_flow(self, client, test_db, auth_headers):
        """测试空播放列表流程"""
        # 创建空播放列表
        create_response = client.post(
            "/api/playlists/",
            json={"name": "Empty Playlist"},
            headers=auth_headers
        )
        playlist_id = create_response.json()["id"]

        # 验证播放列表为空
        detail_response = client.get(f"/api/playlists/{playlist_id}")
        detail_data = detail_response.json()
        assert len(detail_data["items"]) == 0

        # 分配到设备（空播放列表）
        import uuid
        device_id = str(uuid.uuid4())
        register_response = client.post(
            "/api/devices/register",
            json={"device_id": device_id}
        )
        device_internal_id = register_response.json()["id"]

        assign_response = client.post(
            f"/api/playlists/{playlist_id}/devices/{device_internal_id}",
            headers=auth_headers
        )
        assert assign_response.status_code == 201

        # 播放端初始化
        init_response = client.post(
            "/api/player/init",
            json={"device_id": device_id}
        )
        assert init_response.status_code == 200
        init_data = init_response.json()

        # 验证返回的播放列表项为空
        if len(init_data["playlists"]) > 0:
            assert len(init_data["playlists"][0]["items"]) == 0

    def test_playlist_deletion_flow(self, client, test_db, auth_headers):
        """测试播放列表删除流程"""
        # 创建播放列表
        create_response = client.post(
            "/api/playlists/",
            json={"name": "To Delete"},
            headers=auth_headers
        )
        playlist_id = create_response.json()["id"]

        # 添加媒体
        from app.models.media import MediaFile
        media = MediaFile(
            file_name="to_delete.jpg",
            file_type="image",
            file_path="/tmp/to_delete.jpg",
            file_size=102400,
            md5_hash="hash123"
        )
        test_db.add(media)
        test_db.commit()

        client.post(
            f"/api/playlists/{playlist_id}/items",
            json={"media_id": media.id},
            headers=auth_headers
        )

        # 删除播放列表
        delete_response = client.delete(
            f"/api/playlists/{playlist_id}",
            headers=auth_headers
        )
        assert delete_response.status_code == 204

        # 验证已删除
        verify_response = client.get(f"/api/playlists/{playlist_id}")
        assert verify_response.status_code == 404


class TestPlaylistPaginationFlow:
    """播放列表分页流程测试"""

    def test_playlist_pagination_flow(self, client, test_db, auth_headers):
        """测试播放列表分页流程"""
        # 创建多个播放列表
        playlist_ids = []
        for i in range(5):
            response = client.post(
                "/api/playlists/",
                json={"name": f"Playlist {i}"},
                headers=auth_headers
            )
            playlist_ids.append(response.json()["id"])

        # 分页查询
        page1 = client.get("/api/playlists/?skip=0&limit=2")
        page2 = client.get("/api/playlists/?skip=2&limit=2")
        page3 = client.get("/api/playlists/?skip=4&limit=2")

        assert page1.status_code == 200
        assert page2.status_code == 200
        assert page3.status_code == 200

        # 验证页面大小
        assert len(page1.json()["items"]) <= 2
        assert len(page2.json()["items"]) <= 2


class TestPlaylistErrorHandlingFlow:
    """播放列表错误处理流程测试"""

    def test_unauthorized_playlist_flow(self, client, test_db):
        """测试未授权的播放列表操作"""
        # 尝试创建（应该失败）
        create_response = client.post(
            "/api/playlists/",
            json={"name": "Test"}
        )
        assert create_response.status_code == 401

        # 创建播放列表后尝试修改（应该失败）
        from app.models.playlist import Playlist
        playlist = Playlist(name="Test Playlist")
        test_db.add(playlist)
        test_db.commit()

        update_response = client.put(
            f"/api/playlists/{playlist.id}",
            json={"name": "Updated"}
        )
        assert update_response.status_code == 401

        # 尝试删除（应该失败）
        delete_response = client.delete(f"/api/playlists/{playlist.id}")
        assert delete_response.status_code == 401

    def test_not_found_playlist_flow(self, client, test_db, auth_headers):
        """测试播放列表不存在的流程"""
        # 获取不存在的播放列表
        get_response = client.get("/api/playlists/99999")
        assert get_response.status_code == 404

        # 更新不存在的播放列表
        update_response = client.put(
            "/api/playlists/99999",
            json={"name": "Test"},
            headers=auth_headers
        )
        assert update_response.status_code == 404

        # 删除不存在的播放列表
        delete_response = client.delete(
            "/api/playlists/99999",
            headers=auth_headers
        )
        assert delete_response.status_code == 404

        # 添加项目到不存在的播放列表
        from app.models.media import MediaFile
        media = MediaFile(
            file_name="test.jpg",
            file_type="image",
            file_path="/tmp/test.jpg",
            file_size=102400,
            md5_hash="hash123"
        )
        test_db.add(media)
        test_db.commit()

        add_response = client.post(
            "/api/playlists/99999/items",
            json={"media_id": media.id},
            headers=auth_headers
        )
        assert add_response.status_code == 404
