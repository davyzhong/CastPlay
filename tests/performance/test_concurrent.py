"""
并发测试

测试 API 在并发请求下的表现
"""
import pytest
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import uuid


class TestConcurrentRequests:
    """并发请求测试"""

    @pytest.mark.slow
    def test_concurrent_device_registrations(
        self, client, performance_threshold
    ):
        """测试并发设备注册"""
        num_requests = 10
        success_count = 0
        errors = []
        lock = Lock()

        def register_device():
            nonlocal success_count
            try:
                response = client.post(
                    "/api/devices/register",
                    json={
                        "device_id": str(uuid.uuid4()),
                        "device_name": f"Concurrent Device"
                    }
                )
                with lock:
                    if response.status_code in [200, 201]:
                        success_count += 1
                    else:
                        errors.append(f"Status: {response.status_code}")
            except Exception as e:
                with lock:
                    errors.append(str(e))

        with ThreadPoolExecutor(max_workers=num_requests) as executor:
            futures = [executor.submit(register_device) for _ in range(num_requests)]
            list(as_completed(futures))

        # 验证成功率
        success_rate = success_count / num_requests
        assert success_rate >= performance_threshold["success_rate"]
        assert len(errors) <= num_requests * (1 - performance_threshold["success_rate"])

    @pytest.mark.slow
    def test_concurrent_health_checks(self, client, performance_threshold):
        """测试并发健康检查"""
        num_requests = 50
        success_count = 0
        errors = []
        lock = Lock()

        def health_check():
            nonlocal success_count
            try:
                start = time.time()
                response = client.get("/health")
                duration = (time.time() - start) * 1000

                with lock:
                    if response.status_code == 200:
                        success_count += 1
                        if duration > performance_threshold["api_response_time_ms"]:
                            errors.append(f"Slow: {duration:.2f}ms")
                    else:
                        errors.append(f"Status: {response.status_code}")
            except Exception as e:
                with lock:
                    errors.append(str(e))

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(health_check) for _ in range(num_requests)]
            list(as_completed(futures))

        success_rate = success_count / num_requests
        assert success_rate >= performance_threshold["success_rate"]

    @pytest.mark.slow
    def test_concurrent_list_requests(self, client, performance_threshold):
        """测试并发列表请求"""
        num_requests = 20
        endpoints = [
            "/api/devices/",
            "/api/media/",
            "/api/playlists/"
        ]
        success_count = 0
        errors = []
        lock = Lock()

        def make_request(endpoint):
            nonlocal success_count
            try:
                response = client.get(endpoint)
                with lock:
                    if response.status_code == 200:
                        success_count += 1
                    else:
                        errors.append(f"{endpoint}: {response.status_code}")
            except Exception as e:
                with lock:
                    errors.append(str(e))

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(make_request, endpoints[i % len(endpoints)])
                for i in range(num_requests)
            ]
            list(as_completed(futures))

        success_rate = success_count / num_requests
        assert success_rate >= performance_threshold["success_rate"]


class TestConcurrentSameResource:
    """同一资源的并发操作测试"""

    @pytest.mark.slow
    def test_concurrent_device_heartbeats(self, client, test_device):
        """测试对同一设备的并发心跳"""
        num_requests = 10
        success_count = 0
        lock = Lock()

        def send_heartbeat():
            nonlocal success_count
            try:
                response = client.put(f"/api/devices/{test_device.id}/heartbeat")
                with lock:
                    if response.status_code == 200:
                        success_count += 1
            except Exception as e:
                pass

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(send_heartbeat) for _ in range(num_requests)]
            list(as_completed(futures))

        # 所有请求应该成功
        assert success_count == num_requests

    @pytest.mark.slow
    def test_concurrent_playlist_updates(
        self, client, test_playlist, auth_headers
    ):
        """测试对同一播放列表的并发更新"""
        num_requests = 5
        success_count = 0
        errors = []
        lock = Lock()

        def update_playlist(index):
            nonlocal success_count
            try:
                response = client.put(
                    f"/api/playlists/{test_playlist.id}",
                    json={"name": f"Concurrent Update {index}"},
                    headers=auth_headers
                )
                with lock:
                    if response.status_code == 200:
                        success_count += 1
                    else:
                        errors.append(f"Status: {response.status_code}")
            except Exception as e:
                with lock:
                    errors.append(str(e))

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(update_playlist, i)
                for i in range(num_requests)
            ]
            list(as_completed(futures))

        # 应该有一些成功的更新
        assert success_count > 0


class TestConcurrentMixedOperations:
    """混合并发操作测试"""

    @pytest.mark.slow
    def test_concurrent_mixed_operations(
        self, client, test_db, auth_headers, performance_threshold
    ):
        """测试混合并发操作"""
        operations_performed = []
        lock = Lock()
        success_count = 0

        def operation_register():
            response = client.post(
                "/api/devices/register",
                json={"device_id": str(uuid.uuid4())}
            )
            with lock:
                operations_performed.append(("register", response.status_code))

        def operation_list():
            response = client.get("/api/devices/")
            with lock:
                operations_performed.append(("list", response.status_code))

        def operation_detail():
            response = client.get("/api/devices/1")
            with lock:
                operations_performed.append(("detail", response.status_code))

        def operation_health():
            response = client.get("/health")
            with lock:
                operations_performed.append(("health", response.status_code))

        operations = [
            operation_register,
            operation_list,
            operation_detail,
            operation_health
        ]

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(operations[i % len(operations)])
                for i in range(50)
            ]
            list(as_completed(futures))

        # 统计成功操作
        for op, status in operations_performed:
            if status in [200, 201]:
                success_count += 1

        success_rate = success_count / len(operations_performed)
        assert success_rate >= performance_threshold["success_rate"]


class TestConcurrentUnderLoad:
    """负载下的并发测试"""

    @pytest.mark.slow
    def test_load_test_get_requests(self, client):
        """负载测试：GET 请求"""
        num_requests = 100
        endpoints = [
            "/health",
            "/api/devices/",
            "/api/media/",
            "/api/playlists/"
        ]

        start_time = time.time()
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [
                executor.submit(client.get, endpoints[i % len(endpoints)])
                for i in range(num_requests)
            ]
            results = [f.result() for f in as_completed(futures)]
        end_time = time.time()

        duration = end_time - start_time
        requests_per_second = num_requests / duration

        # 计算成功率
        success_count = sum(1 for r in results if r.status_code == 200)
        success_rate = success_count / num_requests

        # 至少应该有 90% 成功率
        assert success_rate >= 0.90
        # 每秒至少处理 10 个请求
        assert requests_per_second >= 10

    @pytest.mark.slow
    def test_load_test_mixed_requests(
        self, client, test_db, auth_headers
    ):
        """负载测试：混合请求类型"""
        num_requests = 50
        results = []

        def make_request(request_type):
            if request_type == "get":
                return client.get("/api/devices/")
            elif request_type == "post":
                return client.post(
                    "/api/devices/register",
                    json={"device_id": str(uuid.uuid4())}
                )
            elif request_type == "put":
                return client.put("/api/devices/1/heartbeat")
            else:  # head
                return client.head("/health")

        start_time = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(
                    make_request,
                    ["get", "post", "put", "head"][i % 4]
                )
                for i in range(num_requests)
            ]
            results = [f.result() for f in as_completed(futures)]
        end_time = time.time()

        duration = end_time - start_time
        success_count = sum(
            1 for r in results
            if r.status_code in [200, 201]
        )
        success_rate = success_count / num_requests

        assert duration < 10  # 应该在 10 秒内完成
        assert success_rate >= 0.85


class TestRateLimiting:
    """速率限制测试（如果实现）"""

    @pytest.mark.slow
    def test_many_rapid_requests(self, client):
        """测试大量快速请求"""
        results = []
        for _ in range(100):
            response = client.get("/health")
            results.append(response.status_code)

        # 统计状态码
        success = sum(1 for s in results if s == 200)
        too_many = sum(1 for s in results if s == 429)

        # 大部分应该成功
        assert success >= 90

        # 如果实现了速率限制，429 是可接受的
        # 否则，不应该有 429
        assert too_many <= 10
