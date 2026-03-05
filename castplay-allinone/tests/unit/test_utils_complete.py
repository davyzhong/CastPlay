"""
工具函数完整测试

测试所有工具函数的功能
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import os
import tempfile


class TestFileValidators:
    """文件验证器测试"""

    def test_validate_file_type_valid_image(self):
        """测试有效图片类型"""
        from app.utils.file_utils import validate_file_type
        # 根据 settings.ALLOWED_IMAGE_TYPES 验证
        result = validate_file_type("test.jpg", "image")
        assert result is True

    def test_validate_file_type_valid_video(self):
        """测试有效视频类型"""
        from app.utils.file_utils import validate_file_type
        # 根据 settings.ALLOWED_VIDEO_TYPES 验证
        result = validate_file_type("test.mp4", "video")
        assert result is True

    def test_validate_file_type_valid_ppt(self):
        """测试有效 PPT 类型"""
        from app.utils.file_utils import validate_file_type
        result = validate_file_type("test.pptx", "ppt")
        assert result is True

    def test_validate_file_type_invalid(self):
        """测试无效文件类型"""
        from app.utils.file_utils import validate_file_type
        result = validate_file_type("test.exe", "image")
        assert result is False

    def test_get_file_extension(self):
        """测试获取文件扩展名"""
        from app.utils.file_utils import get_file_extension
        assert get_file_extension("test.jpg") == "jpg"
        assert get_file_extension("document.pdf") == "pdf"
        assert get_file_extension("no_extension") == ""
        assert get_file_extension("multiple.dots.txt") == "txt"

    def test_get_mime_type(self):
        """测试获取 MIME 类型"""
        from app.utils.file_utils import get_mime_type
        assert get_mime_type("test.jpg") == "image/jpeg"
        assert get_mime_type("test.png") == "image/png"
        assert get_mime_type("test.mp4") == "video/mp4"


class TestMd5Calculator:
    """MD5 计算器测试"""

    def test_calculate_md5_file(self):
        """测试计算文件 MD5"""
        from app.utils.file_utils import calculate_md5

        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            f.write(b"Hello, World!")
            temp_path = f.name

        try:
            result = calculate_md5(temp_path)
            assert len(result) == 32  # MD5 是 32 个十六进制字符
        finally:
            os.unlink(temp_path)

    def test_calculate_md5_empty_file(self):
        """测试空文件 MD5"""
        from app.utils.file_utils import calculate_md5

        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            temp_path = f.name

        try:
            result = calculate_md5(temp_path)
            assert result == "d41d8cd98f00b204e9800998ecf8427e"  # 空 MD5
        finally:
            os.unlink(temp_path)

    def test_calculate_md5_consistency(self):
        """测试 MD5 一致性"""
        from app.utils.file_utils import calculate_md5

        content = b"Test content"

        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            f.write(content)
            temp_path = f.name

        try:
            result1 = calculate_md5(temp_path)
            result2 = calculate_md5(temp_path)
            assert result1 == result2
        finally:
            os.unlink(temp_path)


class TestFormatFileSize:
    """文件大小格式化测试"""

    def test_format_bytes(self):
        """测试字节格式化"""
        from app.utils.file_utils import format_file_size
        result = format_file_size(500)
        assert "B" in result

    def test_format_kilobytes(self):
        """测试 KB 格式化"""
        from app.utils.file_utils import format_file_size
        result = format_file_size(1024)
        assert "KB" in result

    def test_format_megabytes(self):
        """测试 MB 格式化"""
        from app.utils.file_utils import format_file_size
        result = format_file_size(1048576)
        assert "MB" in result

    def test_format_gigabytes(self):
        """测试 GB 格式化"""
        from app.utils.file_utils import format_file_size
        result = format_file_size(1073741824)
        assert "GB" in result

    def test_format_zero(self):
        """测试零字节"""
        from app.utils.file_utils import format_file_size
        result = format_file_size(0)
        assert "0" in result

    def test_format_large_file(self):
        """测试大文件"""
        from app.utils.file_utils import format_file_size
        # 10 GB
        result = format_file_size(10737418240)
        assert "GB" in result


class TestGetUniqueFilename:
    """唯一文件名生成测试"""

    def test_unique_filename_new_file(self):
        """测试新文件名"""
        from app.utils.file_utils import get_unique_filename

        with tempfile.TemporaryDirectory() as temp_dir:
            result = get_unique_filename(temp_dir, "test.jpg")
            assert result == "test.jpg"

    def test_unique_filename_conflict(self):
        """测试文件名冲突"""
        from app.utils.file_utils import get_unique_filename

        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建一个已存在的文件
            with open(os.path.join(temp_dir, "test.jpg"), "w") as f:
                f.write("existing")

            result = get_unique_filename(temp_dir, "test.jpg")
            assert result == "test_1.jpg"


class TestSafeDeleteFile:
    """安全删除文件测试"""

    def test_safe_delete_existing_file(self):
        """测试删除存在的文件"""
        from app.utils.file_utils import safe_delete_file

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test content")
            temp_path = f.name

        assert os.path.exists(temp_path)
        safe_delete_file(temp_path)
        assert not os.path.exists(temp_path)

    def test_safe_delete_nonexistent_file(self):
        """测试删除不存在的文件"""
        from app.utils.file_utils import safe_delete_file
        # 应该不抛出异常
        result = safe_delete_file("/nonexistent/file/path.txt")
        assert result is True


class TestPasswordHashing:
    """密码哈希测试"""

    def test_password_hashing(self):
        """测试密码哈希"""
        from app.utils.security import get_password_hash, verify_password
        password = "test_password_123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert verify_password(password, hashed) is True

    def test_password_hash_uniqueness(self):
        """测试密码哈希唯一性"""
        from app.utils.security import get_password_hash
        password = "same_password"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # bcrypt 每次生成不同的哈希
        assert hash1 != hash2

    def test_verify_wrong_password(self):
        """测试验证错误密码"""
        from app.utils.security import get_password_hash, verify_password
        password = "correct_password"
        hashed = get_password_hash(password)

        assert verify_password("wrong_password", hashed) is False


class TestJWTToken:
    """JWT Token 测试"""

    def test_create_access_token(self):
        """测试创建访问令牌"""
        from app.utils.security import create_access_token
        data = {"sub": "1", "username": "testuser"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_access_token(self):
        """测试解码访问令牌"""
        from app.utils.security import create_access_token, decode_access_token
        data = {"sub": "1", "username": "testuser"}
        token = create_access_token(data)

        decoded = decode_access_token(token)
        assert decoded["sub"] == "1"
        assert decoded["username"] == "testuser"

    def test_decode_invalid_token(self):
        """测试解码无效令牌"""
        from app.utils.security import decode_access_token

        result = decode_access_token("invalid_token")
        assert result is None


class TestValidateFileContent:
    """文件内容验证测试"""

    def test_validate_jpeg_content(self):
        """测试 JPEG 内容验证"""
        from app.utils.file_utils import validate_file_content

        # JPEG 文件头
        jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF'
        result, msg = validate_file_content(jpeg_header, "image")
        assert result is True

    def test_validate_png_content(self):
        """测试 PNG 内容验证"""
        from app.utils.file_utils import validate_file_content

        # PNG 文件头
        png_header = b'\x89PNG\r\n\x1a\n'
        result, msg = validate_file_content(png_header, "image")
        assert result is True

    def test_validate_invalid_content(self):
        """测试无效内容验证"""
        from app.utils.file_utils import validate_file_content

        # 无效内容
        invalid_content = b'This is not an image'
        result, msg = validate_file_content(invalid_content, "image")
        assert result is False


if __name__ == "__main__":
    pytest.main()
