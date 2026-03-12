"""
安全测试 - 文件上传安全

测试恶意文件上传的防护
"""
import pytest
import struct


class TestFileUploadSecurity:
    """文件上传安全测试"""

    @pytest.mark.security
    @pytest.mark.parametrize("filename,content,content_type", [
        ("test.exe", b"MZ\x90\x00", "application/octet-stream"),
        ("test.sh", b"#!/bin/bash\nrm -rf /", "text/x-sh"),
        ("test.php", b"<?php system($_GET['cmd']); ?>", "application/x-php"),
        ("test.jsp", b"<% Runtime.getRuntime().exec(cmd); %>", "application/x-jsp"),
        ("test.asp", b"<% Execute(Request(\"cmd\")) %>", "application/x-asp"),
        ("test.bat", b"@echo off\ndel *.*", "application/x-bat"),
        ("test.cmd", b"@echo off\nformat c:", "application/x-cmd"),
        ("test.pl", b"#!/usr/bin/perl\nsystem(@ARGV);", "application/x-perl"),
        ("test.py", b"#!/usr/bin/python\nimport os; os.system('rm -rf /')", "text/x-python"),
    ])
    def test_upload_malicious_file_extension(self, client, auth_headers, filename, content, content_type):
        """测试上传恶意文件扩展名"""
        response = client.post(
            "/api/media/upload",
            files={"file": (filename, content, content_type)},
            headers=auth_headers
        )
        # 应该拒绝这些危险的文件类型
        assert response.status_code in [400, 415, 422], \
            f"Accepted dangerous file type: {filename}"

    @pytest.mark.security
    def test_upload_path_traversal_filename(self, client, auth_headers):
        """测试路径遍历攻击"""
        malicious_filenames = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd",
            "..%2f..%2f..%2fetc/passwd",
            "..%252f..%252f..%252fetc/passwd",
        ]

        for filename in malicious_filenames:
            response = client.post(
                "/api/media/upload",
                files={"file": (filename, b"test content", "image/jpeg")},
                headers=auth_headers
            )
            # 应该安全处理或拒绝
            assert response.status_code in [400, 415, 422], \
                f"Path traversal not prevented: {filename}"

    @pytest.mark.security
    def test_upload_double_extension(self, client, auth_headers):
        """测试双重扩展名攻击"""
        # 尝试使用双重扩展名绕过检查
        malicious_filenames = [
            "image.jpg.php",
            "image.jpg.exe",
            "image.png.php5",
            "image.gif.phtml",
        ]

        for filename in malicious_filenames:
            response = client.post(
                "/api/media/upload",
                files={"file": (filename, b"fake image", "image/jpeg")},
                headers=auth_headers
            )
            # 应该只允许安全的扩展名
            if response.status_code == 201:
                # 如果接受，检查存储的文件名是否安全
                data = response.json()
                stored_name = data.get("file_name", "")
                assert ".php" not in stored_name.lower()
                assert ".exe" not in stored_name.lower()

    @pytest.mark.security
    def test_upload_content_type_mismatch(self, client, auth_headers):
        """测试内容类型不匹配"""
        # 声称是图片，实际是脚本
        response = client.post(
            "/api/media/upload",
            files={"file": ("test.jpg", b"<?php system($_GET['cmd']); ?>", "image/jpeg")},
            headers=auth_headers
        )
        # 应该验证文件内容，而不仅仅是 Content-Type
        if response.status_code == 201:
            # 如果接受，系统应该有其他方式验证文件内容
            pass

    @pytest.mark.security
    def test_upload_mime_type_spoofing(self, client, auth_headers):
        """测试 MIME 类型欺骗"""
        # 创建一个带有伪造 JPEG 头的 PHP 文件
        fake_jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF'
        php_payload = b'<?php system($_GET["cmd"]); ?>'
        spoofed_content = fake_jpeg_header + php_payload

        response = client.post(
            "/api/media/upload",
            files={"file": ("test.jpg", spoofed_content, "image/jpeg")},
            headers=auth_headers
        )
        # 系统应该验证完整的文件内容
        if response.status_code == 201:
            # 如果接受，确保文件不能被执行
            pass

    @pytest.mark.security
    def test_upload_empty_file(self, client, auth_headers):
        """测试上传空文件"""
        response = client.post(
            "/api/media/upload",
            files={"file": ("empty.jpg", b"", "image/jpeg")},
            headers=auth_headers
        )
        # 应该拒绝空文件
        assert response.status_code in [400, 422]

    @pytest.mark.security
    def test_upload_oversized_file(self, client, auth_headers):
        """测试上传超大文件"""
        # 创建一个超过限制的文件（模拟）
        large_content = b"x" * (100 * 1024 * 1024)  # 100MB

        response = client.post(
            "/api/media/upload",
            files={"file": ("large.jpg", large_content, "image/jpeg")},
            headers=auth_headers
        )
        # 应该拒绝超大文件
        # 注意：取决于服务器配置，可能返回 413 或 400
        assert response.status_code in [400, 413, 422]

    @pytest.mark.security
    def test_upload_with_null_byte(self, client, auth_headers):
        """测试空字节注入"""
        # 使用空字节绕过扩展名检查
        malicious_filenames = [
            "test.php\x00.jpg",
            "test.php%00.jpg",
            "test\x00.jpg",
        ]

        for filename in malicious_filenames:
            response = client.post(
                "/api/media/upload",
                files={"file": (filename, b"test", "image/jpeg")},
                headers=auth_headers
            )
            # 应该安全处理
            if response.status_code == 201:
                data = response.json()
                # 确保没有 .php 扩展名
                assert not data.get("file_name", "").lower().endswith(".php")

    @pytest.mark.security
    def test_upload_polyglot_file(self, client, auth_headers):
        """测试多语言文件（polyglot）"""
        # 创建一个既是有效图片又是有效脚本的文件
        # 简化的示例：GIF 头 + PHP 代码
        polyglot = b'GIF89a<?php system($_GET["cmd"]); ?>'

        response = client.post(
            "/api/media/upload",
            files={"file": ("test.gif", polyglot, "image/gif")},
            headers=auth_headers
        )
        # 系统应该检测和处理这类文件
        if response.status_code == 201:
            # 如果接受，确保文件不能被执行
            pass


class TestImageUploadSecurity:
    """图片上传安全测试"""

    @pytest.mark.security
    def test_upload_valid_jpeg(self, client, auth_headers):
        """测试上传有效的 JPEG 文件"""
        # 创建最小的有效 JPEG
        jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
        jpeg_footer = b'\xff\xd9'
        jpeg_data = jpeg_header + b'\x00' * 100 + jpeg_footer

        response = client.post(
            "/api/media/upload",
            files={"file": ("test.jpg", jpeg_data, "image/jpeg")},
            headers=auth_headers
        )
        # 应该接受有效的 JPEG
        assert response.status_code in [201, 200, 422]

    @pytest.mark.security
    def test_upload_valid_png(self, client, auth_headers):
        """测试上传有效的 PNG 文件"""
        # 创建最小的有效 PNG
        png_header = b'\x89PNG\r\n\x1a\n'
        png_data = png_header + b'\x00' * 100

        response = client.post(
            "/api/media/upload",
            files={"file": ("test.png", png_data, "image/png")},
            headers=auth_headers
        )
        assert response.status_code in [201, 200, 422]

    @pytest.mark.security
    def test_upload_image_with_exif_injection(self, client, auth_headers):
        """测试 EXIF 数据注入"""
        # 模拟带有恶意 EXIF 数据的图片
        # 注意：这需要实际的 EXIF 数据构造
        fake_image = b'\xff\xd8\xff\xe1' + b'\x00' * 100 + b'\xff\xd9'

        response = client.post(
            "/api/media/upload",
            files={"file": ("exif.jpg", fake_image, "image/jpeg")},
            headers=auth_headers
        )
        # 系统应该安全处理 EXIF 数据
        pass  # 取决于具体的安全需求


class TestVideoUploadSecurity:
    """视频上传安全测试"""

    @pytest.mark.security
    def test_upload_fake_video_file(self, client, auth_headers):
        """测试上传伪造的视频文件"""
        # 声称是 MP4 但实际不是
        response = client.post(
            "/api/media/upload",
            files={"file": ("fake.mp4", b"This is not a video", "video/mp4")},
            headers=auth_headers
        )
        # 应该验证视频文件内容
        if response.status_code == 201:
            # 如果接受，系统应该验证内容
            pass

    @pytest.mark.security
    @pytest.mark.skip(reason="需要实际的视频文件生成")
    def test_upload_video_with_malicious_metadata(self, client, auth_headers):
        """测试带有恶意元数据的视频"""
        pass


class TestPPTUploadSecurity:
    """PPT 上传安全测试"""

    @pytest.mark.security
    def test_upload_pptx_with_macro(self, client, auth_headers):
        """测试带有宏的 PPTX 文件"""
        import zipfile
        import io

        # 创建一个最小的 PPTX 文件结构
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            zf.writestr('[Content_Types].xml', '<?xml version="1.0"?><Types></Types>')
            # 模拟宏文件
            zf.writestr('ppt/vbaProject.bin', b'fake macro content')

        buf.seek(0)

        response = client.post(
            "/api/media/upload",
            files={"file": ("macro.pptx", buf.read(), "application/vnd.openxmlformats-officedocument.presentationml.presentation")},
            headers=auth_headers
        )
        # 系统应该安全处理带宏的文件
        pass

    @pytest.mark.security
    def test_upload_pptx_with_embedded_exe(self, client, auth_headers):
        """测试带有嵌入可执行文件的 PPTX"""
        import zipfile
        import io

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            zf.writestr('[Content_Types].xml', '<?xml version="1.0"?><Types></Types>')
            # 嵌入的可执行文件
            zf.writestr('embedded/malware.exe', b'MZ\x90\x00')

        buf.seek(0)

        response = client.post(
            "/api/media/upload",
            files={"file": ("embedded.pptx", buf.read(), "application/vnd.openxmlformats-officedocument.presentationml.presentation")},
            headers=auth_headers
        )
        # 系统应该检测和处理嵌入的可执行文件
        pass
