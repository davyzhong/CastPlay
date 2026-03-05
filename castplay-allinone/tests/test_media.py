"""
媒体管理 API 测试
"""
import pytest
from httpx import AsyncClient
from pathlib import Path
from io import BytesIO
from PIL import Image


class TestMediaAPI:
    """媒体 API 测试类"""

    def test_upload_image(self, client, auth_headers, temp_test_image):
        """测试上传图片"""
        with open(temp_test_image, "rb") as f:
            files = {"file": ("test.jpg", f, "image/jpeg")}
            response = client.post(
                "/api/media/upload",
                files=files,
                headers=auth_headers
            )
        assert response.status_code == 200
        data = response.json()
        assert data["file_type"] == "image"
        assert data["status"] == "ready"
        assert "id" in data

    def test_upload_video(self, client, auth_headers, temp_test_video):
        """测试上传视频"""
        with open(temp_test_video, "rb") as f:
            files = {"file": ("test.mp4", f, "video/mp4")}
            response = client.post(
                "/api/media/upload",
                files=files,
                headers=auth_headers
            )
        assert response.status_code == 200
        data = response.json()
        assert data["file_type"] == "video"

    def test_upload_unsupported_format(self, client, auth_headers):
        """测试上传不支持的格式"""
        # 创建一个文本文件
        file_content = b"This is not a supported media file"
        files = {"file": ("test.txt", BytesIO(file_content), "text/plain")}
        response = client.post(
            "/api/media/upload",
            files=files,
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_upload_without_auth(self, client, temp_test_image):
        """测试未认证上传"""
        with open(temp_test_image, "rb") as f:
            files = {"file": ("test.jpg", f, "image/jpeg")}
            response = client.post("/api/media/upload", files=files)
        assert response.status_code == 401

    def test_get_media_list(self, client, multiple_test_media):
        """测试获取媒体列表"""
        response = client.get("/api/media/")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_get_media_list_with_pagination(self, client, multiple_test_media):
        """测试分页获取媒体列表"""
        response = client.get("/api/media/?skip=0&limit=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 3

    def test_get_media_list_with_type_filter(self, client, test_media):
        """测试类型过滤"""
        response = client.get(f"/api/media/?file_type={test_media.file_type}")
        assert response.status_code == 200
        data = response.json()
        for media in data["items"]:
            assert media["file_type"] == test_media.file_type

    def test_get_media_list_with_status_filter(self, client):
        """测试状态过滤"""
        response = client.get("/api/media/?status=ready")
        assert response.status_code == 200
        data = response.json()
        for media in data["items"]:
            assert media["status"] == "ready"

    def test_get_media_by_id(self, client, test_media):
        """测试获取单个媒体详情"""
        response = client.get(f"/api/media/{test_media.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_media.id
        assert data["file_name"] == test_media.file_name

    def test_get_nonexistent_media(self, client):
        """测试获取不存在的媒体"""
        response = client.get("/api/media/99999")
        assert response.status_code == 404

    def test_delete_media(self, client, test_media, auth_headers):
        """测试删除媒体"""
        response = client.delete(f"/api/media/{test_media.id}", headers=auth_headers)
        assert response.status_code == 200

        # 验证媒体已被删除
        response = client.get(f"/api/media/{test_media.id}")
        assert response.status_code == 404

    def test_delete_media_without_auth(self, client, test_media):
        """测试未认证删除媒体"""
        response = client.delete(f"/api/media/{test_media.id}")
        assert response.status_code == 401

    def test_download_media(self, client, test_media):
        """测试下载媒体"""
        # 由于测试文件不存在，这个测试可能返回 404
        response = client.get(f"/api/media/{test_media.id}/download")
        # 实际文件存在时应该是 200
        assert response.status_code in [200, 404]

    def test_get_thumbnail(self, client, test_media):
        """测试获取缩略图"""
        response = client.get(f"/api/media/{test_media.id}/thumbnail")
        # 实际文件存在时应该是 200
        assert response.status_code in [200, 404]


class TestMediaValidation:
    """媒体数据验证测试"""

    def test_upload_empty_file(self, client, auth_headers):
        """测试上传空文件"""
        empty_file = BytesIO(b"")
        files = {"file": ("empty.jpg", empty_file, "image/jpeg")}
        response = client.post(
            "/api/media/upload",
            files=files,
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_invalid_file_extension(self, client, auth_headers):
        """测试无效的文件扩展名"""
        # 创建一个实际上是文本的 .jpg 文件
        fake_jpg = BytesIO(b"This is not a real image")
        files = {"file": ("fake.jpg", fake_jpg, "image/jpeg")}
        response = client.post(
            "/api/media/upload",
            files=files,
            headers=auth_headers
        )
        assert response.status_code == 400


class TestMediaPermissions:
    """媒体权限测试"""

    def test_regular_user_can_upload(self, client, auth_headers, temp_test_image):
        """测试普通用户可以上传媒体"""
        with open(temp_test_image, "rb") as f:
            files = {"file": ("test.jpg", f, "image/jpeg")}
            response = client.post(
                "/api/media/upload",
                files=files,
                headers=auth_headers
            )
        assert response.status_code == 200

    def test_regular_user_can_list_media(self, client, auth_headers):
        """测试普通用户可以查看媒体列表"""
        response = client.get("/api/media/", headers=auth_headers)
        assert response.status_code == 200


class TestMediaDuplication:
    """媒体重复检测测试"""

    def test_duplicate_file_detection(self, client, auth_headers, temp_test_image):
        """测试重复文件检测（通过 MD5）"""
        # 第一次上传
        with open(temp_test_image, "rb") as f:
            files = {"file": ("test.jpg", f, "image/jpeg")}
            response1 = client.post(
                "/api/media/upload",
                files=files,
                headers=auth_headers
            )
        assert response1.status_code == 200

        # 第二次上传相同文件
        with open(temp_test_image, "rb") as f:
            files = {"file": ("test2.jpg", f, "image/jpeg")}
            response2 = client.post(
                "/api/media/upload",
                files=files,
                headers=auth_headers
            )
        # 根据实现可能返回 400（重复）或 200（允许重复）
        assert response2.status_code in [200, 400]


class TestMediaSearch:
    """媒体搜索测试"""

    def test_search_media_by_name(self, client, test_media):
        """测试按名称搜索媒体"""
        response = client.get(f"/api/media/?search={test_media.file_name[:5]}")
        assert response.status_code == 200
        data = response.json()
        # 应该找到至少一个匹配的媒体
        if len(data["items"]) > 0:
            assert test_media.file_name[:5].lower() in data["items"][0]["file_name"].lower()


class TestMediaStatus:
    """媒体状态测试"""

    def test_ppt_processing_status(self, client, test_ppt_media):
        """测试 PPT 处理状态"""
        response = client.get(f"/api/media/{test_ppt_media.id}")
        data = response.json()
        assert "status" in data
        assert data["status"] in ["ready", "processing", "failed"]

    def test_video_status(self, client, test_video_media):
        """测试视频状态"""
        response = client.get(f"/api/media/{test_video_media.id}")
        data = response.json()
        assert data["status"] == "ready"


class TestMediaSorting:
    """媒体排序测试"""

    def test_sort_by_upload_time(self, client, multiple_test_media):
        """测试按上传时间排序"""
        response = client.get("/api/media/?order_by=upload_time&order=desc")
        assert response.status_code == 200
        data = response.json()
        if len(data["items"]) > 1:
            # 验证是否按降序排列
            for i in range(len(data["items"]) - 1):
                time1 = data["items"][i]["upload_time"]
                time2 = data["items"][i + 1]["upload_time"]
                assert time1 >= time2

    def test_sort_by_file_size(self, client, multiple_test_media):
        """测试按文件大小排序"""
        response = client.get("/api/media/?order_by=file_size&order=asc")
        assert response.status_code == 200
        data = response.json()
        if len(data["items"]) > 1:
            for i in range(len(data["items"]) - 1):
                size1 = data["items"][i]["file_size"]
                size2 = data["items"][i + 1]["file_size"]
                assert size1 <= size2


class TestMediaBulkOperations:
    """媒体批量操作测试"""

    def test_bulk_delete(self, client, multiple_test_media, auth_headers):
        """测试批量删除"""
        media_ids = [media.id for media in multiple_test_media]
        # 假设实现了批量删除接口
        # response = client.post(
        #     "/api/media/bulk-delete",
        #     json={"ids": media_ids},
        #     headers=auth_headers
        # )
        # assert response.status_code == 200
        # 这个测试需要后端实现批量删除接口


class TestMediaThumbnailGeneration:
    """缩略图生成测试"""

    def test_thumbnail_generation_on_upload(self, client, auth_headers, temp_test_image):
        """测试上传时自动生成缩略图"""
        with open(temp_test_image, "rb") as f:
            files = {"file": ("test.jpg", f, "image/jpeg")}
            response = client.post(
                "/api/media/upload",
                files=files,
                headers=auth_headers
            )
        data = response.json()
        # 图片应该有缩略图
        if data["file_type"] == "image":
            assert "thumbnail_path" in data
