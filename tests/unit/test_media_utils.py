"""
Media API 额外测试
提高 media.py API 的测试覆盖率
"""
import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from io import BytesIO


class TestMediaFileValidation:
    """媒体文件验证测试"""

    def test_validate_file_type_image(self):
        """测试图片类型验证"""
        from app.utils.file_utils import validate_file_type
        assert validate_file_type("test.jpg", "image") is True
        assert validate_file_type("test.png", "image") is True
        assert validate_file_type("test.gif", "image") is True
        assert validate_file_type("test.bmp", "image") is True

    def test_validate_file_type_video(self):
        """测试视频类型验证"""
        from app.utils.file_utils import validate_file_type
        assert validate_file_type("test.mp4", "video") is True
        assert validate_file_type("test.avi", "video") is True
        assert validate_file_type("test.mov", "video") is True
        assert validate_file_type("test.mkv", "video") is True

    def test_validate_file_type_ppt(self):
        """测试 PPT 类型验证"""
        from app.utils.file_utils import validate_file_type
        assert validate_file_type("test.ppt", "ppt") is True
        assert validate_file_type("test.pptx", "ppt") is True

    def test_validate_file_type_invalid(self):
        """测试无效类型验证"""
        from app.utils.file_utils import validate_file_type
        assert validate_file_type("test.exe", "image") is False
        assert validate_file_type("test.doc", "video") is False
        assert validate_file_type("test.pdf", "ppt") is False


class TestFileSignatureValidation:
    """文件签名验证测试"""

    def test_validate_jpg_signature(self):
        """测试 JPG 签名验证"""
        from app.utils.file_utils import validate_file_content
        # JPG 文件签名
        jpg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF'
        valid, error = validate_file_content(jpg_header, 'image')
        assert valid is True

    def test_validate_png_signature(self):
        """测试 PNG 签名验证"""
        from app.utils.file_utils import validate_file_content
        # PNG 文件签名
        png_header = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
        valid, error = validate_file_content(png_header, 'image')
        assert valid is True

    def test_validate_gif_signature(self):
        """测试 GIF 签名验证"""
        from app.utils.file_utils import validate_file_content
        # GIF 文件签名（需要至少 8 字节）
        gif_header = b'GIF89a\x00\x00'  # 添加额外字节以满足最小长度要求
        valid, error = validate_file_content(gif_header, 'image')
        assert valid is True

    def test_validate_invalid_signature(self):
        """测试无效签名验证"""
        from app.utils.file_utils import validate_file_content
        # 无效的文件内容
        invalid_content = b'This is not an image'
        valid, error = validate_file_content(invalid_content, 'image')
        assert valid is False
        assert error != ""

    def test_validate_small_file(self):
        """测试过小的文件"""
        from app.utils.file_utils import validate_file_content
        small_content = b'x'
        valid, error = validate_file_content(small_content, 'image')
        assert valid is False
        assert "too small" in error.lower()


class TestMimeTypes:
    """MIME 类型测试"""

    def test_get_mime_type_jpeg(self):
        """测试 JPEG MIME 类型"""
        from app.utils.file_utils import get_mime_type
        assert get_mime_type("test.jpg") == "image/jpeg"
        assert get_mime_type("test.jpeg") == "image/jpeg"

    def test_get_mime_type_png(self):
        """测试 PNG MIME 类型"""
        from app.utils.file_utils import get_mime_type
        assert get_mime_type("test.png") == "image/png"

    def test_get_mime_type_mp4(self):
        """测试 MP4 MIME 类型"""
        from app.utils.file_utils import get_mime_type
        assert get_mime_type("test.mp4") == "video/mp4"

    def test_get_mime_type_unknown(self):
        """测试未知类型"""
        from app.utils.file_utils import get_mime_type
        result = get_mime_type("test.unknown")
        # 应该返回一个默认类型
        assert result is not None


class TestMediaPathConfig:
    """媒体路径配置测试"""

    def test_uploads_dir_exists(self):
        """测试上传目录存在"""
        from app.config import settings
        assert settings.UPLOADS_DIR is not None

    def test_thumbnails_dir_exists(self):
        """测试缩略图目录存在"""
        from app.config import settings
        assert settings.THUMBNAILS_DIR is not None

    def test_converted_dir_exists(self):
        """测试转换目录存在"""
        from app.config import settings
        assert settings.CONVERTED_DIR is not None

    def test_max_file_size_configured(self):
        """测试最大文件大小配置"""
        from app.config import settings
        assert settings.MAX_FILE_SIZE > 0


class TestMediaFileOperations:
    """媒体文件操作测试"""

    def test_calculate_md5(self, tmp_path):
        """测试 MD5 计算"""
        from app.utils.file_utils import calculate_md5

        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello World")

        md5_hash = calculate_md5(str(test_file))
        assert len(md5_hash) == 32
        assert md5_hash == "b10a8db164e0754105b7a99be72e3fe5"

    def test_calculate_md5_empty_file(self, tmp_path):
        """测试空文件 MD5"""
        from app.utils.file_utils import calculate_md5

        test_file = tmp_path / "empty.txt"
        test_file.write_text("")

        md5_hash = calculate_md5(str(test_file))
        assert md5_hash == "d41d8cd98f00b204e9800998ecf8427e"

    def test_calculate_md5_large_file(self, tmp_path):
        """测试大文件 MD5"""
        from app.utils.file_utils import calculate_md5

        test_file = tmp_path / "large.bin"
        # 创建 1MB 的文件
        test_file.write_bytes(os.urandom(1024 * 1024))

        md5_hash = calculate_md5(str(test_file))
        assert len(md5_hash) == 32


class TestFileExtension:
    """文件扩展名测试"""

    def test_get_extension_lowercase(self):
        """测试扩展名小写转换"""
        from app.utils.file_utils import get_file_extension
        assert get_file_extension("TEST.JPG") == "jpg"
        assert get_file_extension("Image.PNG") == "png"

    def test_get_extension_no_dot(self):
        """测试无扩展名"""
        from app.utils.file_utils import get_file_extension
        assert get_file_extension("filename") == ""

    def test_get_extension_multiple_dots(self):
        """测试多个点的文件名"""
        from app.utils.file_utils import get_file_extension
        assert get_file_extension("file.name.test.jpg") == "jpg"


class TestSafeDelete:
    """安全删除测试"""

    def test_safe_delete_existing(self, tmp_path):
        """测试删除存在的文件"""
        from app.utils.file_utils import safe_delete_file

        test_file = tmp_path / "to_delete.txt"
        test_file.write_text("content")

        result = safe_delete_file(str(test_file))
        assert result is True
        assert not test_file.exists()

    def test_safe_delete_nonexistent(self, tmp_path):
        """测试删除不存在的文件"""
        from app.utils.file_utils import safe_delete_file

        result = safe_delete_file(str(tmp_path / "nonexistent.txt"))
        assert result is True

    def test_safe_delete_none(self):
        """测试删除 None 路径（应该返回 False）"""
        from app.utils.file_utils import safe_delete_file

        result = safe_delete_file(None)
        # None 路径会导致错误，返回 False
        assert result is False

    def test_safe_delete_empty_string(self):
        """测试删除空字符串路径（应该返回 False）"""
        from app.utils.file_utils import safe_delete_file

        result = safe_delete_file("")
        # 空字符串会导致错误，返回 False
        assert result is False


class TestThumbnailGeneration:
    """缩略图生成测试"""

    def test_generate_thumbnail_from_image(self, tmp_path):
        """测试从图片生成缩略图"""
        from app.utils.file_utils import generate_thumbnail
        from PIL import Image

        # 创建测试图片
        source = tmp_path / "source.jpg"
        img = Image.new("RGB", (800, 600), color="red")
        img.save(source)

        thumbnail = tmp_path / "thumb.jpg"
        result = generate_thumbnail(str(source), str(thumbnail))

        assert result is True
        assert thumbnail.exists()

        # 验证缩略图尺寸
        with Image.open(thumbnail) as thumb:
            assert thumb.width <= 640
            assert thumb.height <= 480

    def test_generate_thumbnail_png_with_alpha(self, tmp_path):
        """测试 PNG 带透明通道"""
        from app.utils.file_utils import generate_thumbnail
        from PIL import Image

        # 创建带透明通道的 PNG
        source = tmp_path / "source.png"
        img = Image.new("RGBA", (800, 600), color=(255, 0, 0, 128))
        img.save(source)

        thumbnail = tmp_path / "thumb.jpg"
        result = generate_thumbnail(str(source), str(thumbnail))

        assert result is True
        assert thumbnail.exists()

    def test_generate_thumbnail_invalid_source(self, tmp_path):
        """测试无效源文件"""
        from app.utils.file_utils import generate_thumbnail

        result = generate_thumbnail(
            str(tmp_path / "nonexistent.jpg"),
            str(tmp_path / "thumb.jpg")
        )
        assert result is False
