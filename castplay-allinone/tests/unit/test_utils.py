"""
工具函数单元测试

测试所有工具函数的功能
"""
import os
import pytest
import hashlib
from pathlib import Path
from unittest.mock import patch, Mock
from PIL import Image

from app.utils.file_utils import (
    get_file_extension,
    validate_file_type,
    get_unique_filename,
    calculate_md5,
    generate_thumbnail,
    safe_delete_file,
    format_file_size
)


# ============================================================================
# 文件扩展名测试
# ============================================================================

class TestGetFileExtension:
    """get_file_extension 函数测试"""

    def test_jpg_extension(self):
        """测试 JPG 扩展名"""
        assert get_file_extension("test.jpg") == "jpg"
        assert get_file_extension("test.JPG") == "jpg"

    def test_png_extension(self):
        """测试 PNG 扩展名"""
        assert get_file_extension("test.png") == "png"

    def test_mp4_extension(self):
        """测试 MP4 扩展名"""
        assert get_file_extension("test.mp4") == "mp4"

    def test_pptx_extension(self):
        """测试 PPTX 扩展名"""
        assert get_file_extension("test.pptx") == "pptx"

    def test_path_with_extension(self):
        """测试带路径的文件名"""
        assert get_file_extension("/path/to/file.jpg") == "jpg"
        assert get_file_extension("./uploads/video.mp4") == "mp4"

    def test_no_extension(self):
        """测试没有扩展名的文件"""
        assert get_file_extension("noextension") == ""

    def test_multiple_dots(self):
        """测试文件名中有多个点"""
        assert get_file_extension("my.backup.file.jpg") == "jpg"


# ============================================================================
# 文件类型验证测试
# ============================================================================

class TestValidateFileType:
    """validate_file_type 函数测试"""

    def test_valid_image_types(self):
        """测试有效的图片类型"""
        valid_images = ["test.jpg", "test.jpeg", "test.png", "test.gif", "test.bmp"]
        for filename in valid_images:
            assert validate_file_type(filename, "image") is True

    def test_valid_video_types(self):
        """测试有效的视频类型"""
        valid_videos = ["test.mp4", "test.avi", "test.mov", "test.mkv", "test.flv"]
        for filename in valid_videos:
            assert validate_file_type(filename, "video") is True

    def test_valid_ppt_types(self):
        """测试有效的 PPT 类型"""
        valid_ppt = ["test.ppt", "test.pptx"]
        for filename in valid_ppt:
            assert validate_file_type(filename, "ppt") is True

    def test_invalid_image_type(self):
        """测试无效的图片类型"""
        invalid_files = ["test.txt", "test.pdf", "test.doc", "test.mp3"]
        for filename in invalid_files:
            assert validate_file_type(filename, "image") is False

    def test_invalid_video_type(self):
        """测试无效的视频类型"""
        invalid_files = ["test.txt", "test.pdf", "test.jpg", "test.mp3"]
        for filename in invalid_files:
            assert validate_file_type(filename, "video") is False

    def test_invalid_ppt_type(self):
        """测试无效的 PPT 类型"""
        invalid_files = ["test.txt", "test.pdf", "test.jpg", "test.mp4"]
        for filename in invalid_files:
            assert validate_file_type(filename, "ppt") is False

    def test_case_insensitive(self):
        """测试不区分大小写"""
        assert validate_file_type("TEST.JPG", "image") is True
        assert validate_file_type("Test.Mp4", "video") is True
        assert validate_file_type("TEST.PPTX", "ppt") is True

    def test_mismatch_type(self):
        """测试文件类型不匹配"""
        assert validate_file_type("test.jpg", "video") is False
        assert validate_file_type("test.mp4", "image") is False


# ============================================================================
# 唯一文件名测试
# ============================================================================

class TestGetUniqueFilename:
    """get_unique_filename 函数测试"""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """临时目录 fixture"""
        upload_dir = tmp_path / "uploads"
        upload_dir.mkdir()
        return upload_dir

    def test_unique_filename_new_file(self, temp_dir):
        """测试新文件名（不存在冲突）"""
        filename = get_unique_filename(str(temp_dir), "test.jpg")
        assert filename == "test.jpg"

    def test_unique_filename_with_counter(self, temp_dir):
        """测试带计数器的文件名"""
        # 创建已存在的文件
        (temp_dir / "test.jpg").touch()

        filename = get_unique_filename(str(temp_dir), "test.jpg")
        assert filename == "test_1.jpg"

    def test_unique_filename_multiple_counters(self, temp_dir):
        """测试多个计数器"""
        # 创建已存在的文件
        (temp_dir / "test.jpg").touch()
        (temp_dir / "test_1.jpg").touch()
        (temp_dir / "test_2.jpg").touch()

        filename = get_unique_filename(str(temp_dir), "test.jpg")
        assert filename == "test_3.jpg"

    def test_unique_filename_path_preservation(self, tmp_path):
        """测试路径不包含在返回值中"""
        upload_dir = tmp_path / "uploads"
        upload_dir.mkdir()

        filename = get_unique_filename(str(upload_dir), "subdir/test.jpg")
        assert "subdir" not in filename
        assert filename.startswith("test")


# ============================================================================
# MD5 计算测试
# ============================================================================

class TestCalculateMD5:
    """calculate_md5 函数测试"""

    @pytest.fixture
    def temp_file(self, tmp_path):
        """临时文件 fixture"""
        file_path = tmp_path / "test.txt"
        file_path.write_text("Hello, World!")
        return file_path

    def test_md5_calculation(self, temp_file):
        """测试 MD5 计算"""
        md5 = calculate_md5(str(temp_file))

        # 验证返回的是 32 字符的十六进制字符串
        assert len(md5) == 32
        assert all(c in "0123456789abcdef" for c in md5)

    def test_md5_consistency(self, temp_file):
        """测试 MD5 一致性（多次计算结果相同）"""
        md5_1 = calculate_md5(str(temp_file))
        md5_2 = calculate_md5(str(temp_file))
        assert md5_1 == md5_2

    def test_md5_different_files(self, tmp_path):
        """测试不同文件的 MD5 不同"""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("content1")
        file2.write_text("content2")

        md5_1 = calculate_md5(str(file1))
        md5_2 = calculate_md5(str(file2))
        assert md5_1 != md5_2

    def test_md5_known_value(self, tmp_path):
        """测试已知内容的 MD5 值"""
        file_path = tmp_path / "known.txt"
        content = "The quick brown fox jumps over the lazy dog"
        file_path.write_text(content)

        # Python hashlib 的结果
        expected = hashlib.md5(content.encode()).hexdigest()
        actual = calculate_md5(str(file_path))
        assert actual == expected

    def test_md5_empty_file(self, tmp_path):
        """测试空文件的 MD5"""
        file_path = tmp_path / "empty.txt"
        file_path.touch()

        md5 = calculate_md5(str(file_path))
        # 空文件的 MD5 应该是 d41d8cd98f00b204e9800998ecf8427e
        assert md5 == "d41d8cd98f00b204e9800998ecf8427e"


# ============================================================================
# 缩略图生成测试
# ============================================================================

class TestGenerateThumbnail:
    """generate_thumbnail 函数测试"""

    @pytest.fixture
    def temp_image(self, tmp_path):
        """创建临时测试图片"""
        image_path = tmp_path / "test_image.jpg"
        img = Image.new("RGB", (800, 600), color="blue")
        img.save(image_path)
        return image_path

    def test_thumbnail_generation(self, temp_image, tmp_path):
        """测试生成缩略图"""
        thumbnail_path = tmp_path / "thumb.jpg"
        generate_thumbnail(str(temp_image), str(thumbnail_path))

        assert thumbnail_path.exists()

        # 验证缩略图尺寸
        with Image.open(thumbnail_path) as thumb:
            assert thumb.width <= 300  # 默认最大宽度
            assert thumb.height <= 200  # 默认最大高度

    def test_thumbnail_aspect_ratio(self, temp_image, tmp_path):
        """测试缩略图保持宽高比"""
        thumbnail_path = tmp_path / "thumb_aspect.jpg"
        generate_thumbnail(str(temp_image), str(thumbnail_path))

        original = Image.open(temp_image)
        thumbnail = Image.open(thumbnail_path)

        # 计算宽高比
        original_ratio = original.width / original.height
        thumbnail_ratio = thumbnail.width / thumbnail.height

        # 允许小的误差
        assert abs(original_ratio - thumbnail_ratio) < 0.01

    def test_thumbnail_overwrite(self, temp_image, tmp_path):
        """测试覆盖已存在的缩略图"""
        thumbnail_path = tmp_path / "thumb_overwrite.jpg"

        # 第一次生成
        generate_thumbnail(str(temp_image), str(thumbnail_path))
        thumb_size_1 = os.path.getsize(thumbnail_path)

        # 第二次生成（覆盖）
        generate_thumbnail(str(temp_image), str(thumbnail_path))
        thumb_size_2 = os.path.getsize(thumbnail_path)

        # 文件应该被覆盖
        assert thumb_size_1 == thumb_size_2

    def test_thumbnail_invalid_source(self, tmp_path):
        """测试无效的源文件"""
        source_path = tmp_path / "nonexistent.jpg"
        thumbnail_path = tmp_path / "thumb.jpg"

        with pytest.raises(FileNotFoundError):
            generate_thumbnail(str(source_path), str(thumbnail_path))


# ============================================================================
# 安全删除测试
# ============================================================================

class TestSafeDeleteFile:
    """safe_delete_file 函数测试"""

    def test_delete_existing_file(self, tmp_path):
        """测试删除存在的文件"""
        file_path = tmp_path / "to_delete.txt"
        file_path.write_text("content")

        safe_delete_file(str(file_path))
        assert not file_path.exists()

    def test_delete_nonexistent_file(self, tmp_path):
        """测试删除不存在的文件（不应该抛出异常）"""
        file_path = tmp_path / "nonexistent.txt"

        # 不应该抛出异常
        safe_delete_file(str(file_path))
        assert True

    def test_delete_with_none_path(self):
        """测试 None 路径（不应该抛出异常）"""
        # 不应该抛出异常
        safe_delete_file(None)
        assert True

    def test_delete_empty_string(self):
        """测试空字符串路径（不应该抛出异常）"""
        # 不应该抛出异常
        safe_delete_file("")
        assert True


# ============================================================================
# 文件大小格式化测试
# ============================================================================

class TestFormatFileSize:
    """format_file_size 函数测试"""

    def test_format_bytes(self):
        """测试字节格式化"""
        assert format_file_size(500) == "500 B"
        assert format_file_size(999) == "999 B"

    def test_format_kilobytes(self):
        """测试千字节格式化"""
        assert format_file_size(1024) == "1 KB"
        assert format_file_size(1536) == "1.5 KB"
        assert format_file_size(1024000) == "1000 KB"

    def test_format_megabytes(self):
        """测试兆字节格式化"""
        assert format_file_size(1048576) == "1 MB"
        assert format_file_size(2097152) == "2 MB"
        assert format_file_size(5242880) == "5 MB"

    def test_format_gigabytes(self):
        """测试吉字节格式化"""
        assert format_file_size(1073741824) == "1 GB"
        assert format_file_size(2147483648) == "2 GB"

    def test_format_zero(self):
        """测试零字节"""
        assert format_file_size(0) == "0 B"

    def test_format_large_file(self):
        """测试大文件"""
        size = 10 * 1024 * 1024 * 1024  # 10 GB
        assert format_file_size(size) == "10 GB"

    def test_format_precision(self):
        """测试格式化精度"""
        # 检查小数位数
        result = format_file_size(1537)
        assert "KB" in result
        assert "1.5" in result or "1.50" in result


# ============================================================================
# 其他工具函数测试（如果存在）
# ============================================================================

class TestOtherUtils:
    """其他工具函数测试"""

    def test_logger_import(self):
        """测试日志模块可以导入"""
        from app.utils.logger import logger
        assert logger is not None

    def test_config_import(self):
        """测试配置模块可以导入"""
        from app.config import settings
        assert settings is not None
        assert hasattr(settings, 'APP_NAME')
