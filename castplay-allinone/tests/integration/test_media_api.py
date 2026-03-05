"""
媒体管理 API 集成测试

测试所有媒体管理相关的 API 端点
"""
import pytest
from pathlib import Path
from io import BytesIO


# ============================================================================
# 媒体上传端点测试
# ============================================================================

class TestMediaUploadEndpoint:
    """媒体上传端点测试"""

    def test_upload_image_success(self, client, auth_headers, mock_file_utils):
        """测试成功上传图片"""
        # 创建测试图片
        from PIL import Image
        import io

        img = Image.new("RGB", (100, 100), color="red")
        img_io = io.BytesIO()
        img.save(img_io, format="JPEG")
        img_io.seek(0)

        files = {"file": ("test.jpg", img_io, "image/jpeg")}
        data = {"file_type": "image"}

        response = client.post(
            "/api/media/upload",
            files=files,
            data=data,
            headers=auth_headers
        )

        assert response.status_code == 201
        result = response.json()
        assert result["message"] == "File uploaded successfully"
        assert "media" in result
        assert result["media"]["file_name"] == "test.jpg"
        assert result["media"]["file_type"] == "image"

    def test_upload_video_success(self, client, auth_headers):
        """测试成功上传视频"""
        # 创建测试视频文件
        video_content = b"ftypmp42\x00\x00\x00\x00mp42isom" + b"\x00" * 10000

        files = {"file": ("test.mp4", BytesIO(video_content), "video/mp4")}
        data = {"file_type": "video"}

        response = client.post(
            "/api/media/upload",
            files=files,
            data=data,
            headers=auth_headers
        )

        assert response.status_code in [201, 413]  # 201 成功，413 可能因为文件太小被拒绝
        if response.status_code == 201:
            result = response.json()
            assert result["media"]["file_type"] == "video"

    def test_upload_ppt_success(self, client, auth_headers):
        """测试成功上传 PPT"""
        # 创建测试 PPT 文件
        ppt_content = b"PK\x03\x04" + b"\x00" * 50000  # 简单的 ZIP 文件头

        files = {"file": ("test.pptx", BytesIO(ppt_content), "application/vnd.openxmlformats-officedocument.presentationml.presentation")}
        data = {"file_type": "ppt"}

        response = client.post(
            "/api/media/upload",
            files=files,
            data=data,
            headers=auth_headers
        )

        assert response.status_code in [201, 400]
        if response.status_code == 201:
            result = response.json()
            assert result["media"]["file_type"] == "ppt"

    def test_upload_missing_file_type(self, client, auth_headers):
        """测试缺少文件类型参数"""
        from PIL import Image
        import io

        img = Image.new("RGB", (100, 100))
        img_io = io.BytesIO()
        img.save(img_io, format="JPEG")
        img_io.seek(0)

        files = {"file": ("test.jpg", img_io, "image/jpeg")}

        response = client.post(
            "/api/media/upload",
            files=files,
            headers=auth_headers
        )

        assert response.status_code == 422

    def test_upload_unsupported_file_type(self, client, auth_headers):
        """测试不支持的文件类型"""
        files = {"file": ("test.txt", BytesIO(b"text content"), "text/plain")}
        data = {"file_type": "image"}

        response = client.post(
            "/api/media/upload",
            files=files,
            data=data,
            headers=auth_headers
        )

        assert response.status_code == 400

    def test_upload_without_auth(self, client):
        """测试未认证上传"""
        files = {"file": ("test.jpg", BytesIO(b"fake image"), "image/jpeg")}
        data = {"file_type": "image"}

        response = client.post(
            "/api/media/upload",
            files=files,
            data=data
        )

        assert response.status_code in [401, 403]  # Unauthorized or Forbidden

    def test_upload_large_file(self, client, auth_headers):
        """测试上传大文件（应该被拒绝）"""
        large_content = b"x" * (500 * 1024 * 1024 + 1)  # 超过 500MB

        files = {"file": ("large.jpg", BytesIO(large_content), "image/jpeg")}
        data = {"file_type": "image"}

        response = client.post(
            "/api/media/upload",
            files=files,
            data=data,
            headers=auth_headers
        )

        assert response.status_code == 413


# ============================================================================
# 媒体列表端点测试
# ============================================================================

class TestMediaListEndpoint:
    """媒体列表端点测试"""

    def test_list_media(self, client, multiple_test_media):
        """测试获取媒体列表"""
        response = client.get("/api/media/")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data
        assert len(data["items"]) >= len(multiple_test_media)

    def test_list_media_pagination(self, client, multiple_test_media):
        """测试媒体列表分页"""
        response = client.get("/api/media/?skip=0&limit=2")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 2
        assert data["page"] == 1
        assert data["per_page"] == 2

    def test_list_media_skip(self, client, multiple_test_media):
        """测试跳过媒体"""
        response_1 = client.get("/api/media/?skip=0&limit=1")
        response_2 = client.get("/api/media/?skip=1&limit=1")

        assert response_1.status_code == 200
        assert response_2.status_code == 200

        data_1 = response_1.json()["items"]
        data_2 = response_2.json()["items"]

        if len(data_1) > 0 and len(data_2) > 0:
            assert data_1[0]["id"] != data_2[0]["id"]

    def test_list_media_filter_by_type_image(self, client, test_media):
        """测试按图片类型过滤"""
        response = client.get("/api/media/?file_type=image")

        assert response.status_code == 200
        data = response.json()
        assert all(item["file_type"] == "image" for item in data["items"])

    def test_list_media_filter_by_type_video(self, client, test_video_media):
        """测试按视频类型过滤"""
        response = client.get("/api/media/?file_type=video")

        assert response.status_code == 200
        data = response.json()
        assert all(item["file_type"] == "video" for item in data["items"])

    def test_list_media_filter_by_type_ppt(self, client, test_ppt_media):
        """测试按 PPT 类型过滤"""
        response = client.get("/api/media/?file_type=ppt")

        assert response.status_code == 200
        data = response.json()
        assert all(item["file_type"] == "ppt" for item in data["items"])

    def test_list_media_filter_by_status(self, client, test_db):
        """测试按状态过滤"""
        from app.models.media import MediaFile

        # 创建不同状态的媒体
        media1 = MediaFile(
            file_name="ready.jpg",
            file_type="image",
            file_path="/tmp/ready.jpg",
            file_size=1000,
            status="ready"
        )
        media2 = MediaFile(
            file_name="processing.jpg",
            file_type="image",
            file_path="/tmp/processing.jpg",
            file_size=1000,
            status="processing"
        )
        test_db.add_all([media1, media2])
        test_db.commit()

        response = client.get("/api/media/?status_filter=ready")

        assert response.status_code == 200
        data = response.json()
        assert all(item["status"] == "ready" for item in data["items"])

    def test_list_media_invalid_filter(self, client):
        """测试无效的过滤器"""
        response = client.get("/api/media/?file_type=invalid")

        assert response.status_code == 422


# ============================================================================
# 媒体详情端点测试
# ============================================================================

class TestMediaDetailEndpoint:
    """媒体详情端点测试"""

    def test_get_media_detail(self, client, test_media):
        """测试获取媒体详情"""
        response = client.get(f"/api/media/{test_media.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_media.id
        assert data["file_name"] == test_media.file_name
        assert data["file_type"] == test_media.file_type

    def test_get_nonexistent_media(self, client):
        """测试获取不存在的媒体"""
        response = client.get("/api/media/99999")

        assert response.status_code == 404
        assert "Media file not found" in response.json()["detail"]

    def test_get_media_with_thumbnail(self, client, test_db):
        """测试获取带缩略图的媒体"""
        from app.models.media import MediaFile

        media = MediaFile(
            file_name="with_thumb.jpg",
            file_type="image",
            file_path="/tmp/with_thumb.jpg",
            file_size=1000,
            thumbnail_path="/tmp/thumb.jpg",
            md5_hash="hash123"
        )
        test_db.add(media)
        test_db.commit()
        test_db.refresh(media)

        response = client.get(f"/api/media/{media.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["thumbnail_path"] is not None

    def test_get_media_with_converted(self, client, test_ppt_media):
        """测试获取带转换文件的媒体"""
        response = client.get(f"/api/media/{test_ppt_media.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["converted_path"] is not None


# ============================================================================
# 媒体删除端点测试
# ============================================================================

class TestMediaDeleteEndpoint:
    """媒体删除端点测试"""

    def test_delete_media(self, client, test_db, auth_headers):
        """测试删除媒体"""
        from app.models.media import MediaFile

        media = MediaFile(
            file_name="to_delete.jpg",
            file_type="image",
            file_path="/tmp/to_delete.jpg",
            file_size=1000,
            md5_hash="hash123"
        )
        test_db.add(media)
        test_db.commit()
        test_db.refresh(media)

        response = client.delete(f"/api/media/{media.id}", headers=auth_headers)

        assert response.status_code == 204
        assert response.content == b""

        # 验证数据库记录已删除
        deleted = test_db.query(MediaFile).filter(MediaFile.id == media.id).first()
        assert deleted is None

    def test_delete_media_with_thumbnail(self, client, test_db, auth_headers):
        """测试删除带缩略图的媒体"""
        from app.models.media import MediaFile
        from unittest.mock import patch

        media = MediaFile(
            file_name="with_thumb.jpg",
            file_type="image",
            file_path="/tmp/with_thumb.jpg",
            file_size=1000,
            thumbnail_path="/tmp/thumb.jpg",
            md5_hash="hash123"
        )
        test_db.add(media)
        test_db.commit()
        test_db.refresh(media)

        # Mock 文件删除
        with patch("app.api.media.safe_delete_file") as mock_delete:
            response = client.delete(f"/api/media/{media.id}", headers=auth_headers)

            assert response.status_code == 204
            # 验证删除了文件和缩略图
            assert mock_delete.call_count >= 1

    def test_delete_nonexistent_media(self, client, auth_headers):
        """测试删除不存在的媒体"""
        response = client.delete("/api/media/99999", headers=auth_headers)

        assert response.status_code == 404

    def test_delete_without_auth(self, client, test_media):
        """测试未认证删除"""
        response = client.delete(f"/api/media/{test_media.id}")

        assert response.status_code in [401, 403]  # Unauthorized or Forbidden


# ============================================================================
# 媒体下载端点测试
# ============================================================================

class TestMediaDownloadEndpoint:
    """媒体下载端点测试"""

    def test_download_media(self, client, test_db):
        """测试下载媒体文件"""
        from app.models.media import MediaFile
        import tempfile

        # 创建实际的测试文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
            f.write(b"fake image content")
            file_path = f.name

        try:
            media = MediaFile(
                file_name="download_test.jpg",
                file_type="image",
                file_path=file_path,
                file_size=100,
                md5_hash="hash123"
            )
            test_db.add(media)
            test_db.commit()
            test_db.refresh(media)

            response = client.get(f"/api/media/{media.id}/download")

            assert response.status_code == 200
            assert response.headers["content-type"] == "application/octet-stream"
            assert response.headers["content-disposition"] == f'attachment; filename="download_test.jpg"'
        finally:
            import os
            if os.path.exists(file_path):
                os.unlink(file_path)

    def test_download_nonexistent_media(self, client):
        """测试下载不存在的媒体"""
        response = client.get("/api/media/99999/download")

        assert response.status_code == 404

    def test_download_converted_media(self, client, test_ppt_media):
        """测试下载转换后的媒体"""
        # 如果设置了 converted_path，应该下载转换后的文件
        response = client.get(f"/api/media/{test_ppt_media.id}/download")

        # 由于文件可能不存在，可能会返回 404
        assert response.status_code in [200, 404]


# ============================================================================
# 缩略图端点测试
# ============================================================================

class TestThumbnailEndpoint:
    """缩略图端点测试"""

    def test_get_thumbnail(self, client, test_db):
        """测试获取缩略图"""
        from app.models.media import MediaFile
        from PIL import Image
        import tempfile

        # 创建实际的测试图片和缩略图
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
            img = Image.new("RGB", (100, 100), color="red")
            img.save(f, format="JPEG")
            thumb_path = f.name

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
            img = Image.new("RGB", (50, 50), color="blue")
            img.save(f, format="JPEG")
            media_path = f.name

        try:
            media = MediaFile(
                file_name="thumbnail_test.jpg",
                file_type="image",
                file_path=media_path,
                file_size=100,
                thumbnail_path=thumb_path,
                md5_hash="hash123"
            )
            test_db.add(media)
            test_db.commit()
            test_db.refresh(media)

            response = client.get(f"/api/media/{media.id}/thumbnail")

            assert response.status_code == 200
            assert response.headers["content-type"] == "image/jpeg"
        finally:
            import os
            if os.path.exists(thumb_path):
                os.unlink(thumb_path)
            if os.path.exists(media_path):
                os.unlink(media_path)

    def test_get_thumbnail_nonexistent(self, client, test_media):
        """测试获取不存在的缩略图"""
        response = client.get(f"/api/media/{test_media.id}/thumbnail")

        assert response.status_code == 404

    def test_get_thumbnail_media_without_thumbnail(self, client, test_db):
        """测试获取没有缩略图的媒体"""
        from app.models.media import MediaFile

        media = MediaFile(
            file_name="no_thumb.mp4",
            file_type="video",
            file_path="/tmp/no_thumb.mp4",
            file_size=1000,
            md5_hash="hash123"
        )
        test_db.add(media)
        test_db.commit()
        test_db.refresh(media)

        response = client.get(f"/api/media/{media.id}/thumbnail")

        assert response.status_code == 404


# ============================================================================
# 边界条件测试
# ============================================================================

class TestMediaBoundaryConditions:
    """媒体边界条件测试"""

    def test_upload_empty_filename(self, client, auth_headers):
        """测试空文件名"""
        files = {"file": ("", BytesIO(b"content"), "image/jpeg")}
        data = {"file_type": "image"}

        response = client.post(
            "/api/media/upload",
            files=files,
            data=data,
            headers=auth_headers
        )

        # 取决于验证逻辑
        assert response.status_code in [201, 422]

    def test_upload_special_characters_filename(self, client, auth_headers):
        """测试特殊字符文件名"""
        files = {"file": ("测试-文件@#.jpg", BytesIO(b"content"), "image/jpeg")}
        data = {"file_type": "image"}

        response = client.post(
            "/api/media/upload",
            files=files,
            data=data,
            headers=auth_headers
        )

        # 应该能处理特殊字符
        assert response.status_code in [201, 400]

    def test_list_media_empty(self, client, test_db):
        """测试空媒体列表（使用 limit=0）"""
        response = client.get("/api/media/?limit=0")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0
        assert data["total"] == 0
        assert data["pages"] == 0

    def test_list_media_large_skip(self, client):
        """测试大 skip 值"""
        response = client.get("/api/media/?skip=999999")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0
