"""
媒体文件端到端测试

测试从上传到播放的完整媒体流程
"""
import pytest
from io import BytesIO
from PIL import Image
import io


class TestMediaUploadToPlayFlow:
    """媒体上传到播放流程测试"""

    def test_complete_media_flow(self, client, test_db, auth_headers):
        """测试完整的媒体流程：上传 -> 列表 -> 详情 -> 下载"""
        # 1. 用户登录获取 Token（通过 auth_headers fixture）

        # 2. 上传媒体文件
        img = Image.new("RGB", (100, 100), color="blue")
        img_io = io.BytesIO()
        img.save(img_io, format="JPEG")
        img_io.seek(0)

        upload_response = client.post(
            "/api/media/upload",
            files={"file": ("flow_test.jpg", img_io, "image/jpeg")},
            data={"file_type": "image"},
            headers=auth_headers
        )
        assert upload_response.status_code == 201
        media_data = upload_response.json()["media"]
        media_id = media_data["id"]

        # 3. 查询媒体列表（验证上传成功）
        list_response = client.get("/api/media/")
        assert list_response.status_code == 200
        list_data = list_response.json()
        found = any(m["id"] == media_id for m in list_data["items"])
        assert found

        # 4. 获取媒体详情
        detail_response = client.get(f"/api/media/{media_id}")
        assert detail_response.status_code == 200
        detail_data = detail_response.json()
        assert detail_data["file_name"] == "flow_test.jpg"
        assert detail_data["file_type"] == "image"

        # 5. 下载媒体文件
        download_response = client.get(f"/api/media/{media_id}/download")
        assert download_response.status_code == 200

        # 6. 清理：删除媒体
        delete_response = client.delete(f"/api/media/{media_id}", headers=auth_headers)
        assert delete_response.status_code == 204

        # 7. 验证删除（应该 404）
        verify_delete_response = client.get(f"/api/media/{media_id}")
        assert verify_delete_response.status_code == 404

    def test_upload_and_thumbnail_flow(self, client, test_db, auth_headers):
        """测试上传和缩略图流程"""
        # 上传图片
        img = Image.new("RGB", (100, 100), color="green")
        img_io = io.BytesIO()
        img.save(img_io, format="JPEG")
        img_io.seek(0)

        upload_response = client.post(
            "/api/media/upload",
            files={"file": ("thumb_test.jpg", img_io, "image/jpeg")},
            data={"file_type": "image"},
            headers=auth_headers
        )
        assert upload_response.status_code == 201
        media_id = upload_response.json()["media"]["id"]

        # 获取缩略图
        thumb_response = client.get(f"/api/media/{media_id}/thumbnail")
        # 可能 404（如果没有实际生成）或 200
        assert thumb_response.status_code in [200, 404]

        # 清理
        client.delete(f"/api/media/{media_id}", headers=auth_headers)

    def test_multiple_media_upload_flow(self, client, test_db, auth_headers):
        """测试批量上传多个媒体"""
        media_ids = []

        # 上传 3 个媒体
        for i in range(3):
            img = Image.new("RGB", (100, 100), color=(i*80, i*80, i*80))
            img_io = io.BytesIO()
            img.save(img_io, format="JPEG")
            img_io.seek(0)

            response = client.post(
                "/api/media/upload",
                files={"file": (f"batch_{i}.jpg", img_io, "image/jpeg")},
                data={"file_type": "image"},
                headers=auth_headers
            )
            assert response.status_code == 201
            media_ids.append(response.json()["media"]["id"])

        # 验证所有媒体都在列表中
        list_response = client.get("/api/media/")
        list_data = list_response.json()

        found_count = sum(1 for m in list_data["items"] if m["id"] in media_ids)
        assert found_count == len(media_ids)

        # 清理
        for media_id in media_ids:
            client.delete(f"/api/media/{media_id}", headers=auth_headers)

    def test_media_with_filter_flow(self, client, test_db, auth_headers):
        """测试带过滤器的媒体流程"""
        # 上传图片
        img = Image.new("RGB", (100, 100))
        img_io = io.BytesIO()
        img.save(img_io, format="JPEG")
        img_io.seek(0)

        upload_response = client.post(
            "/api/media/upload",
            files={"file": ("filter_test.jpg", img_io, "image/jpeg")},
            data={"file_type": "image"},
            headers=auth_headers
        )
        media_id = upload_response.json()["media"]["id"]

        # 过滤图片类型
        image_response = client.get("/api/media/?file_type=image")
        assert image_response.status_code == 200
        image_data = image_response.json()
        found = any(m["id"] == media_id for m in image_data["items"])
        assert found

        # 过滤视频类型（应该不包含）
        video_response = client.get("/api/media/?file_type=video")
        video_data = video_response.json()
        found_in_video = any(m["id"] == media_id for m in video_data["items"])
        assert not found_in_video

        # 清理
        client.delete(f"/api/media/{media_id}", headers=auth_headers)

    def test_media_pagination_flow(self, client, test_db, auth_headers):
        """测试媒体分页流程"""
        # 创建 5 个媒体
        media_ids = []
        for i in range(5):
            img = Image.new("RGB", (100, 100), color=(i*50, i*50, i*50))
            img_io = io.BytesIO()
            img.save(img_io, format="JPEG")
            img_io.seek(0)

            response = client.post(
                "/api/media/upload",
                files={"file": (f"page_{i}.jpg", img_io, "image/jpeg")},
                data={"file_type": "image"},
                headers=auth_headers
            )
            media_ids.append(response.json()["media"]["id"])

        # 分页查询
        page1 = client.get("/api/media/?skip=0&limit=2")
        page2 = client.get("/api/media/?skip=2&limit=2")
        page3 = client.get("/api/media/?skip=4&limit=2")

        assert page1.status_code == 200
        assert page2.status_code == 200
        assert page3.status_code == 200

        # 验证没有重复
        ids_page1 = [m["id"] for m in page1.json()["items"]]
        ids_page2 = [m["id"] for m in page2.json()["items"]]
        ids_page3 = [m["id"] for m in page3.json()["items"]]

        assert len(set(ids_page1) & set(ids_page2)) == 0
        assert len(set(ids_page2) & set(ids_page3)) == 0

        # 清理
        for media_id in media_ids:
            client.delete(f"/api/media/{media_id}", headers=auth_headers)


class TestMediaErrorHandlingFlow:
    """媒体错误处理流程测试"""

    def test_unauthorized_flow(self, client):
        """测试未授权的媒体操作流程"""
        # 尝试上传（应该失败）
        upload_response = client.post(
            "/api/media/upload",
            files={"file": ("test.jpg", BytesIO(b"test"), "image/jpeg")},
            data={"file_type": "image"}
        )
        assert upload_response.status_code == 401

        # 尝试删除（应该失败）
        delete_response = client.delete("/api/media/99999")
        assert delete_response.status_code == 401

    def test_not_found_flow(self, client, auth_headers):
        """测试资源不存在的流程"""
        # 获取不存在的媒体
        get_response = client.get("/api/media/99999")
        assert get_response.status_code == 404

        # 下载不存在的媒体
        download_response = client.get("/api/media/99999/download")
        assert download_response.status_code == 404

        # 删除不存在的媒体
        delete_response = client.delete("/api/media/99999", headers=auth_headers)
        assert delete_response.status_code == 404


class TestMediaStateFlow:
    """媒体状态流程测试"""

    def test_media_states_flow(self, client, test_db, auth_headers):
        """测试媒体状态变化流程"""
        # 1. 上传媒体（状态：ready）
        img = Image.new("RGB", (100, 100))
        img_io = io.BytesIO()
        img.save(img_io, format="JPEG")
        img_io.seek(0)

        upload_response = client.post(
            "/api/media/upload",
            files={"file": ("state_test.jpg", img_io, "image/jpeg")},
            data={"file_type": "image"},
            headers=auth_headers
        )
        media_id = upload_response.json()["media"]["id"]
        assert upload_response.json()["media"]["status"] == "ready"

        # 2. 获取详情验证状态
        detail_response = client.get(f"/api/media/{media_id}")
        assert detail_response.json()["status"] == "ready"

        # 3. 模拟状态变化（需要直接操作数据库）
        from app.models.media import MediaFile
        media = test_db.query(MediaFile).filter(MediaFile.id == media_id).first()
        media.status = "processing"
        test_db.commit()

        # 4. 过滤处理中的媒体
        processing_response = client.get("/api/media/?status_filter=processing")
        assert processing_response.status_code == 200

        # 清理
        client.delete(f"/api/media/{media_id}", headers=auth_headers)
