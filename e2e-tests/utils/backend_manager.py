"""
后端服务管理工具

功能：
- 启动/停止后端 Flask 服务
- 健康检查
- 测试数据准备
- API 调用辅助
"""
import subprocess
import time
import logging
import requests
import json
from typing import Optional, Dict, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)


class BackendManager:
    """后端服务管理器"""

    def __init__(self, config):
        """
        初始化后端管理器

        Args:
            config: BackendConfig 配置对象
        """
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self._session = requests.Session()

    def is_running(self) -> bool:
        """检查后端服务是否运行"""
        try:
            response = self._session.get(
                f"{self.config.base_url}/api/health",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False

    def start(self, wait_ready: bool = True) -> bool:
        """
        启动后端服务

        Args:
            wait_ready: 是否等待服务就绪

        Returns:
            是否启动成功
        """
        if self.is_running():
            logger.info("后端服务已在运行")
            return True

        project_path = Path(self.config.project_path)
        if not project_path.exists():
            logger.error(f"项目路径不存在: {project_path}")
            return False

        logger.info(f"启动后端服务: {project_path}")

        try:
            # 启动 Flask 服务
            self.process = subprocess.Popen(
                ["python", "run.py"],
                cwd=str(project_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env={
                    **__import__('os').environ,
                    "FLASK_ENV": "testing",
                    "SKIP_AUTH": "True"
                }
            )

            if wait_ready:
                return self._wait_for_ready()

            return True

        except Exception as e:
            logger.error(f"启动后端服务失败: {e}")
            return False

    def _wait_for_ready(self) -> bool:
        """等待服务就绪"""
        logger.info(f"等待后端服务就绪（超时: {self.config.startup_timeout}秒）...")

        start_time = time.time()

        while time.time() - start_time < self.config.startup_timeout:
            if self.is_running():
                logger.info("后端服务已就绪")
                return True
            time.sleep(1)

        logger.error("后端服务启动超时")
        return False

    def stop(self) -> bool:
        """停止后端服务"""
        logger.info("停止后端服务...")

        try:
            if self.process:
                self.process.terminate()
                self.process.wait(timeout=10)
                self.process = None

            logger.info("后端服务已停止")
            return True

        except Exception as e:
            logger.error(f"停止后端服务失败: {e}")
            if self.process:
                self.process.kill()
            return False

    # ================================================================
    # API 辅助方法
    # ================================================================

    def api_get(self, endpoint: str, **kwargs) -> Optional[Dict]:
        """GET 请求"""
        try:
            url = f"{self.config.api_url}/{endpoint.lstrip('/')}"
            response = self._session.get(url, timeout=30, **kwargs)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"API GET 失败 [{endpoint}]: {e}")
            return None

    def api_post(self, endpoint: str, data: Dict = None, **kwargs) -> Optional[Dict]:
        """POST 请求"""
        try:
            url = f"{self.config.api_url}/{endpoint.lstrip('/')}"
            response = self._session.post(url, json=data, timeout=30, **kwargs)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"API POST 失败 [{endpoint}]: {e}")
            return None

    def api_delete(self, endpoint: str, **kwargs) -> bool:
        """DELETE 请求"""
        try:
            url = f"{self.config.api_url}/{endpoint.lstrip('/')}"
            response = self._session.delete(url, timeout=30, **kwargs)
            return response.status_code in [200, 204]
        except Exception as e:
            logger.error(f"API DELETE 失败 [{endpoint}]: {e}")
            return False

    # ================================================================
    # 测试数据准备
    # ================================================================

    def get_devices(self) -> List[Dict]:
        """获取所有设备"""
        result = self.api_get("devices")
        return result.get("devices", []) if result else []

    def get_device_by_id(self, device_id: str) -> Optional[Dict]:
        """根据设备 ID 获取设备信息"""
        devices = self.get_devices()
        for device in devices:
            if device.get("device_id") == device_id:
                return device
        return None

    def get_playlists(self) -> List[Dict]:
        """获取所有播放列表"""
        result = self.api_get("playlists")
        return result.get("playlists", []) if result else []

    def create_playlist(self, name: str, description: str = "") -> Optional[Dict]:
        """创建播放列表"""
        result = self.api_post("playlists", {
            "name": name,
            "description": description
        })
        return result.get("playlist") if result else None

    def add_media_to_playlist(self, playlist_id: int, media_id: int,
                              duration: int = 10) -> bool:
        """添加媒体到播放列表"""
        result = self.api_post(f"playlists/{playlist_id}/items", {
            "media_id": media_id,
            "display_duration": duration
        })
        return result is not None

    def assign_playlist_to_device(self, device_id: int, playlist_id: int) -> bool:
        """分配播放列表到设备"""
        result = self.api_post(f"devices/{device_id}/playlists", {
            "playlist_id": playlist_id
        })
        return result is not None

    def get_media_files(self) -> List[Dict]:
        """获取所有媒体文件"""
        result = self.api_get("media")
        return result.get("media", []) if result else []

    def upload_test_media(self, file_path: str, file_type: str = "image") -> Optional[Dict]:
        """上传测试媒体文件"""
        try:
            url = f"{self.config.api_url}/media/upload"
            with open(file_path, 'rb') as f:
                files = {'file': (Path(file_path).name, f)}
                data = {'file_type': file_type}
                response = self._session.post(
                    url, files=files, data=data, timeout=60)
                response.raise_for_status()
                return response.json().get("media")
        except Exception as e:
            logger.error(f"上传媒体文件失败: {e}")
            return None

    def set_device_schedule(self, device_id: int, start_time: str,
                            end_time: str, enabled: bool = True) -> bool:
        """设置设备定时计划"""
        result = self.api_post(f"devices/{device_id}/schedule", {
            "start_time": start_time,
            "end_time": end_time,
            "enabled": enabled
        })
        return result is not None

    def get_device_schedule(self, device_id: int) -> Optional[Dict]:
        """获取设备定时计划"""
        result = self.api_get(f"devices/{device_id}/schedule")
        return result.get("schedule") if result else None

    def trigger_force_sync(self, device_id: str) -> bool:
        """触发强制同步"""
        result = self.api_post(f"devices/{device_id}/sync")
        return result is not None

    # ================================================================
    # 测试数据清理
    # ================================================================

    def cleanup_test_data(self):
        """清理测试数据"""
        logger.info("清理测试数据...")

        # 删除测试播放列表
        playlists = self.get_playlists()
        for playlist in playlists:
            if playlist.get("name", "").startswith("E2E_Test_"):
                self.api_delete(f"playlists/{playlist['id']}")

        # 删除测试媒体
        media_files = self.get_media_files()
        for media in media_files:
            if media.get("file_name", "").startswith("e2e_test_"):
                self.api_delete(f"media/{media['id']}")

    def prepare_test_data(self) -> Dict[str, Any]:
        """
        准备测试数据

        Returns:
            包含测试数据的字典 {playlist_id, media_ids, ...}
        """
        logger.info("准备测试数据...")

        # 创建测试播放列表
        playlist = self.create_playlist(
            name=f"E2E_Test_Playlist_{int(time.time())}",
            description="E2E 自动化测试播放列表"
        )

        if not playlist:
            logger.error("创建测试播放列表失败")
            return {}

        # 使用已有的媒体文件（或上传新的）
        media_files = self.get_media_files()
        ready_media = [m for m in media_files if m.get("status") == "ready"]

        if ready_media:
            # 添加前 3 个媒体到播放列表
            for media in ready_media[:3]:
                self.add_media_to_playlist(
                    playlist["id"], media["id"], duration=10)

        return {
            "playlist_id": playlist["id"],
            "playlist_name": playlist["name"],
            "media_count": min(3, len(ready_media))
        }
