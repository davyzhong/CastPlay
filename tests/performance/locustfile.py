"""
CastPlay 性能测试配置文件
使用 Locust 进行负载测试
"""
from locust import HttpUser, task, between, events
import random


class CastPlayUser(HttpUser):
    """CastPlay 用户行为模拟"""

    # 等待时间：请求之间的随机间隔（1-3 秒）
    wait_time = between(1, 3)

    def on_start(self):
        """用户启动时调用"""
        # 登录获取 token
        response = self.client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "testpass123"}
        )
        if response.status_code == 200:
            self.token = response.json()["access_token"]
        else:
            self.token = None

    @task(3)
    def view_dashboard(self):
        """查看仪表盘 - 高频操作"""
        if self.token:
            self.client.get(
                "/",
                headers={"Authorization": f"Bearer {self.token}"}
            )

    @task(2)
    def view_devices(self):
        """查看设备列表 - 中频操作"""
        if self.token:
            self.client.get(
                "/api/devices/",
                headers={"Authorization": f"Bearer {self.token}"}
            )

    @task(2)
    def view_media(self):
        """查看媒体列表 - 中频操作"""
        if self.token:
            self.client.get(
                "/api/media/",
                headers={"Authorization": f"Bearer {self.token}"}
            )

    @task(1)
    def view_playlists(self):
        """查看播放列表 - 低频操作"""
        if self.token:
            self.client.get(
                "/api/playlists/",
                headers={"Authorization": f"Bearer {self.token}"}
            )

    @task(1)
    def upload_media(self):
        """上传媒体 - 低频操作（需要文件）"""
        # 仅模拟请求，不实际上传文件
        if self.token:
            self.client.post(
                "/api/media/upload",
                headers={"Authorization": f"Bearer {self.token}"}
            )


class AdminUser(HttpUser):
    """管理员用户行为模拟"""

    wait_time = between(2, 5)
    weight = 1  # 管理员用户占比少

    def on_start(self):
        """管理员启动时调用"""
        response = self.client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        if response.status_code == 200:
            self.token = response.json()["access_token"]
        else:
            self.token = None

    @task(3)
    def view_all_users(self):
        """查看所有用户"""
        if self.token:
            self.client.get(
                "/api/auth/users",
                headers={"Authorization": f"Bearer {self.token}"}
            )

    @task(2)
    def create_playlist(self):
        """创建播放列表"""
        if self.token:
            self.client.post(
                "/api/playlists/",
                json={
                    "name": f"Test Playlist {random.randint(1, 1000)}",
                    "description": "Performance test playlist"
                },
                headers={"Authorization": f"Bearer {self.token}"}
            )


# 性能测试事件监听器
class PerformanceStatsListener:
    """收集性能统计"""

    def __init__(self):
        self.requests = []
        self.errors = []

    def request(self, request_type, name, response_time, response_length, **kwargs):
        self.requests.append({
            "type": request_type,
            "name": name,
            "time": response_time,
            "length": response_length,
            "success": kwargs.get("response").status_code < 400
        })

    def response(self, **kwargs):
        pass

    def error(self, **kwargs):
        self.errors.append(kwargs)


# 测试场景配置
test_scenarios = {
    "normal_load": {
        "users": 100,
        "spawn_rate": 10,
        "run_time": "10m",
        "description": "正常负载：100 并发用户，每秒 10 新用户"
    },
    "high_load": {
        "users": 500,
        "spawn_rate": 50,
        "run_time": "5m",
        "description": "高负载：500 并发用户，每秒 50 新用户"
    },
    "stress_test": {
        "users": 1000,
        "spawn_rate": 100,
        "run_time": "2m",
        "description": "压力测试：1000 并发用户，每秒 100 新用户"
    },
    "soak_test": {
        "users": 200,
        "spawn_rate": 20,
        "run_time": "60m",
        "description": "持久测试：200 并发用户，运行 60 分钟"
    },
}


def get_scenario_config(scenario_name: str) -> dict:
    """获取指定测试场景的配置"""
    return test_scenarios.get(scenario_name, test_scenarios["normal_load"])
