"""
API 性能测试

测试 API 响应时间和性能指标
"""
import pytest
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Lock


class TestAPIResponseTime:
    """API 响应时间测试"""

    @pytest.mark.slow
    def test_health_check_response_time(self, client, performance_threshold):
        """测试健康检查响应时间"""
        start = time.time()
        response = client.get("/health")
        end = time.time()
        duration_ms = (end - start) * 1000

        assert response.status_code == 200
        assert duration_ms < performance_threshold["api_response_time_ms"]

    @pytest.mark.slow
    def test_list_devices_response_time(self, client, performance_threshold):
        """测试设备列表响应时间"""
        start = time.time()
        response = client.get("/api/devices/")
        end = time.time()
        duration_ms = (end - start) * 1000

        assert response.status_code == 200
        assert duration_ms < performance_threshold["api_response_time_ms"]

    @pytest.mark.slow
    def test_list_media_response_time(self, client, performance_threshold):
        """测试媒体列表响应时间"""
        start = time.time()
        response = client.get("/api/media/")
        end = time.time()
        duration_ms = (end - start) * 1000

        assert response.status_code == 200
        assert duration_ms < performance_threshold["api_response_time_ms"]

    @pytest.mark.slow
    def test_list_playlists_response_time(self, client, performance_threshold):
        """测试播放列表响应时间"""
        start = time.time()
        response = client.get("/api/playlists/")
        end = time.time()
        duration_ms = (end - start) * 1000

        assert response.status_code == 200
        assert duration_ms < performance_threshold["api_response_time_ms"]

    @pytest.mark.slow
    def test_device_registration_response_time(self, client, performance_threshold):
        """测试设备注册响应时间"""
        import uuid

        start = time.time()
        response = client.post(
            "/api/devices/register",
            json={"device_id": str(uuid.uuid4())}
        )
        end = time.time()
        duration_ms = (end - start) * 1000

        assert response.status_code in [200, 201]
        assert duration_ms < performance_threshold["api_response_time_ms"]

    @pytest.mark.slow
    def test_login_response_time(self, client, test_user, performance_threshold):
        """测试登录响应时间"""
        start = time.time()
        response = client.post(
            "/api/auth/login",
            json={
                "username": test_user.username,
                "password": "testpass123"
            }
        )
        end = time.time()
        duration_ms = (end - start) * 1000

        assert response.status_code == 200
        assert duration_ms < performance_threshold["api_response_time_ms"]


class TestAPIPerformanceWithLargeData:
    """大数据量 API 性能测试"""

    @pytest.mark.slow
    def test_list_many_devices_performance(self, client, test_db, performance_threshold):
        """测试列出多个设备的性能"""
        import uuid

        # 创建 100 个设备
        for _ in range(100):
            device_id = str(uuid.uuid4())
            from app.models.device import Device
            device = Device(
                device_id=device_id,
                device_name=f"Device {_}",
                status="online"
            )
            test_db.add(device)
        test_db.commit()

        start = time.time()
        response = client.get("/api/devices/")
        end = time.time()
        duration_ms = (end - start) * 1000

        assert response.status_code == 200
        # 大数据量可以放宽要求
        assert duration_ms < performance_threshold["api_response_time_ms"] * 2

    @pytest.mark.slow
    def test_list_many_media_performance(self, client, test_db, performance_threshold):
        """测试列出多个媒体的性能"""
        # 创建 100 个媒体
        for i in range(100):
            from app.models.media import MediaFile
            media = MediaFile(
                file_name=f"media_{i}.jpg",
                file_type="image",
                file_path=f"/tmp/media_{i}.jpg",
                file_size=102400,
                md5_hash=f"hash{i}"
            )
            test_db.add(media)
        test_db.commit()

        start = time.time()
        response = client.get("/api/media/")
        end = time.time()
        duration_ms = (end - start) * 1000

        assert response.status_code == 200
        assert duration_ms < performance_threshold["api_response_time_ms"] * 2

    @pytest.mark.slow
    def test_playlist_detail_with_many_items_performance(
        self, client, test_db, auth_headers, performance_threshold
    ):
        """测试包含多个项目的播放列表详情性能"""
        # 创建播放列表
        playlist_response = client.post(
            "/api/playlists/",
            json={"name": "Large Playlist"},
            headers=auth_headers
        )
        playlist_id = playlist_response.json()["id"]

        # 创建并添加 50 个媒体
        for i in range(50):
            from app.models.media import MediaFile
            media = MediaFile(
                file_name=f"item_{i}.jpg",
                file_type="image",
                file_path=f"/tmp/item_{i}.jpg",
                file_size=102400,
                md5_hash=f"hash{i}"
            )
            test_db.add(media)
            test_db.commit()

            client.post(
                f"/api/playlists/{playlist_id}/items",
                json={"media_id": media.id},
                headers=auth_headers
            )

        # 获取详情
        start = time.time()
        response = client.get(f"/api/playlists/{playlist_id}")
        end = time.time()
        duration_ms = (end - start) * 1000

        assert response.status_code == 200
        assert duration_ms < performance_threshold["api_response_time_ms"] * 3


class TestDatabaseQueryPerformance:
    """数据库查询性能测试"""

    @pytest.mark.slow
    def test_user_query_performance(self, client, test_db, performance_threshold):
        """测试用户查询性能"""
        # 创建 50 个用户
        from app.models.user import User
        from app.utils.security import get_password_hash

        for i in range(50):
            user = User(
                username=f"user{i}",
                password_hash=get_password_hash("pass123"),
                is_active=True
            )
            test_db.add(user)
        test_db.commit()

        # 查询用户列表
        start = time.time()
        client.get("/api/auth/users", headers={
            "Authorization": f"Bearer {create_test_jwt_token(1, 'admin')}"
        })
        end = time.time()

        duration_ms = (end - start) * 1000
        assert duration_ms < performance_threshold["api_response_time_ms"] * 2


class TestComplexOperationPerformance:
    """复杂操作性能测试"""

    @pytest.mark.slow
    def test_complete_media_upload_flow_performance(
        self, client, test_db, auth_headers, performance_threshold
    ):
        """测试完整媒体上传流程性能"""
        from PIL import Image
        import io

        # 上传
        img = Image.new("RGB", (100, 100))
        img_io = io.BytesIO()
        img.save(img_io, format="JPEG")
        img_io.seek(0)

        start = time.time()
        upload_response = client.post(
            "/api/media/upload",
            files={"file": ("perf_test.jpg", img_io, "image/jpeg")},
            data={"file_type": "image"},
            headers=auth_headers
        )
        upload_end = time.time()

        media_id = upload_response.json()["media"]["id"]

        # 查询
        list_response = client.get("/api/media/")
        list_end = time.time()

        # 详情
        detail_response = client.get(f"/api/media/{media_id}")
        detail_end = time.time()

        total_duration_ms = (detail_end - start) * 1000

        assert upload_response.status_code == 201
        assert list_response.status_code == 200
        assert detail_response.status_code == 200
        # 完整流程可以放宽要求
        assert total_duration_ms < performance_threshold["api_response_time_ms"] * 5


def create_test_jwt_token(user_id: int, username: str) -> str:
    """创建测试 Token（辅助函数）"""
    from app.utils.security import create_access_token
    return create_access_token(data={"sub": str(user_id), "username": username})


# ============================================================================
# 内存使用测试
# ============================================================================

class TestMemoryUsage:
    """内存使用测试"""

    @pytest.mark.slow
    def test_memory_leak_detection(self, client, test_db):
        """测试内存泄漏"""
        import gc
        import sys

        # 获取初始内存
        gc.collect()
        initial_objects = len(gc.get_objects())

        # 执行多次操作
        for _ in range(100):
            client.get("/api/devices/")
            client.get("/api/media/")
            client.get("/api/playlists/")

        # 获取最终内存
        gc.collect()
        final_objects = len(gc.get_objects())

        # 对象增长不应该太多
        object_growth = final_objects - initial_objects
        # 允许一定程度的增长
        assert object_growth < 10000
