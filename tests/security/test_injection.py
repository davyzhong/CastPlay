"""
安全测试 - 注入攻击

测试 SQL 注入、命令注入等攻击的防护
"""
import pytest


class TestSQLInjection:
    """SQL 注入测试"""

    @pytest.mark.security
    @pytest.mark.parametrize("payload", [
        "' OR '1'='1",
        "admin'--",
        "' UNION SELECT * FROM users--",
        "1; DROP TABLE users--",
        "' OR 1=1--",
        "1' AND '1'='1",
        "'; INSERT INTO users VALUES--",
        "' OR ''='",
        "1 OR 1=1",
        "admin'/*",
    ])
    def test_login_sql_injection(self, client, payload):
        """测试登录 SQL 注入"""
        response = client.post(
            "/api/auth/login",
            json={"username": payload, "password": "test"}
        )
        # 应该返回认证失败，而不是 500 错误
        assert response.status_code in [401, 422]
        # 不应该返回数据库错误信息
        if response.status_code not in [422]:
            assert "sql" not in response.json().get("detail", "").lower()
            assert "syntax" not in response.json().get("detail", "").lower()

    @pytest.mark.security
    @pytest.mark.parametrize("payload", [
        "' OR '1'='1",
        "test'; DROP TABLE devices;--",
        "' UNION SELECT * FROM devices--",
    ])
    def test_device_id_sql_injection(self, client, payload):
        """测试设备 ID SQL 注入"""
        response = client.post(
            "/api/devices/register",
            json={"device_id": payload, "device_name": "Test"}
        )
        # 应该正常处理，不应该有 SQL 错误
        assert response.status_code in [200, 201, 400, 422]
        if response.status_code >= 500:
            pytest.fail(f"Server error on SQL injection attempt: {response.status_code}")

    @pytest.mark.security
    def test_playlist_name_sql_injection(self, client, auth_headers, payload="' OR '1'='1"):
        """测试播放列表名称 SQL 注入"""
        response = client.post(
            "/api/playlists/",
            json={"name": payload, "description": "test"},
            headers=auth_headers
        )
        # 应该接受或拒绝，但不应该有服务器错误
        assert response.status_code in [201, 400, 422]

    @pytest.mark.security
    @pytest.mark.parametrize("endpoint", [
        "/api/devices/",
        "/api/media/",
        "/api/playlists/",
    ])
    def test_query_param_sql_injection(self, client, endpoint, auth_headers):
        """测试查询参数 SQL 注入"""
        injection_payloads = [
            "?id=1' OR '1'='1",
            "?limit=10; DROP TABLE users",
            "?sort=name'; SELECT * FROM users--",
        ]

        for payload in injection_payloads:
            response = client.get(endpoint + payload, headers=auth_headers)
            # 不应该返回 500 错误
            assert response.status_code != 500, f"Server error on: {payload}"


class TestCommandInjection:
    """命令注入测试"""

    @pytest.mark.security
    @pytest.mark.parametrize("filename", [
        "test; rm -rf /",
        "test$(whoami)",
        "test`id`",
        "test| cat /etc/passwd",
        "test && cat /etc/passwd",
        "test || cat /etc/passwd",
        "test\ncat /etc/passwd",
        "test\rcat /etc/passwd",
    ])
    def test_filename_command_injection(self, client, auth_headers, filename):
        """测试文件名命令注入"""
        # 尝试上传带有命令注入文件名的文件
        response = client.post(
            "/api/media/upload",
            files={"file": (filename, b"test content", "image/jpeg")},
            headers=auth_headers
        )
        # 应该安全处理或拒绝
        assert response.status_code in [201, 400, 415, 422]
        if response.status_code >= 500:
            pytest.fail(f"Server error on command injection attempt")

    @pytest.mark.security
    @pytest.mark.parametrize("device_name", [
        "Device; rm -rf /",
        "Device$(reboot)",
        "Device`shutdown`",
    ])
    def test_device_name_command_injection(self, client, device_name):
        """测试设备名称命令注入"""
        import uuid
        response = client.post(
            "/api/devices/register",
            json={
                "device_id": str(uuid.uuid4()),
                "device_name": device_name
            }
        )
        # 应该正常处理
        assert response.status_code in [200, 201, 400, 422]


class TestNoSQlInjection:
    """NoSQL 注入测试（如果使用 MongoDB 等数据库）"""

    @pytest.mark.security
    def test_query_operator_injection(self, client, auth_headers):
        """测试查询操作符注入"""
        # 尝试 MongoDB 风格的注入
        injection_payloads = [
            {"username": {"$ne": ""}},
            {"username": {"$gt": ""}},
            {"$where": "this.username == 'admin'"},
        ]

        for payload in injection_payloads:
            response = client.post(
                "/api/auth/login",
                json=payload
            )
            # 应该返回验证错误
            assert response.status_code in [401, 422]
