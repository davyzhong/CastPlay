"""
API 客户端

用于 CLI 与 CastPlay 服务器通信
"""
import httpx
from typing import Optional, Dict, Any, List

from cli.config import config_manager


class APIError(Exception):
    """API 错误"""
    def __init__(self, status_code: int, message: str, detail: Optional[str] = None):
        self.status_code = status_code
        self.message = message
        self.detail = detail
        super().__init__(f"[{status_code}] {message}: {detail or 'No detail'}")


class APIClient:
    """API 客户端"""

    def __init__(self, server_url: Optional[str] = None, token: Optional[str] = None):
        self.config = config_manager.config
        self.server_url = server_url or self.config.server_url
        self.token = token or self.config.token
        self.timeout = self.config.timeout

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """发送请求"""
        url = f"{self.server_url}{endpoint}"

        with httpx.Client(timeout=self.timeout) as client:
            response = client.request(
                method=method,
                url=url,
                headers=self._get_headers(),
                params=params,
                json=json_data,
                data=data,
            )

        if response.status_code >= 400:
            try:
                error_data = response.json()
                detail = error_data.get("detail", str(error_data))
            except Exception:
                detail = response.text
            raise APIError(response.status_code, response.reason_phrase, detail)

        # 处理空响应
        if response.status_code == 204:
            return {"success": True}

        return response.json()

    # ==================== 认证 ====================

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """用户登录"""
        return self._request("POST", "/api/auth/login", json_data={
            "username": username,
            "password": password
        })

    # ==================== 设备管理 ====================

    def list_devices(
        self,
        status_filter: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """获取设备列表"""
        params = {"skip": skip, "limit": limit}
        if status_filter:
            params["status_filter"] = status_filter
        return self._request("GET", "/api/devices/", params=params)

    def get_device(self, device_id: int) -> Dict[str, Any]:
        """获取设备详情"""
        return self._request("GET", f"/api/devices/{device_id}")

    def get_device_playlists(self, device_id: int) -> Dict[str, Any]:
        """获取设备关联的播放列表"""
        return self._request("GET", f"/api/devices/{device_id}/playlists")

    def update_device(self, device_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新设备信息"""
        return self._request("PUT", f"/api/devices/{device_id}", json_data=data)

    def disable_device(self, device_id: int, is_disabled: bool = True) -> Dict[str, Any]:
        """启用/禁用设备"""
        return self._request("PUT", f"/api/devices/{device_id}/disable", json_data={"is_disabled": is_disabled})

    def set_device_schedule(
        self,
        device_id: int,
        power_on_time: Optional[str] = None,
        power_off_time: Optional[str] = None,
        is_enabled: bool = True,
        weekdays: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """设置设备定时配置"""
        data = {"is_enabled": is_enabled}
        if power_on_time:
            data["power_on_time"] = power_on_time
        if power_off_time:
            data["power_off_time"] = power_off_time
        if weekdays:
            data["weekdays"] = weekdays
        return self._request("POST", f"/api/devices/{device_id}/schedule", json_data=data)

    def get_device_schedule(self, device_id: int) -> Dict[str, Any]:
        """获取设备定时配置"""
        return self._request("GET", f"/api/devices/{device_id}/schedule")

    def cleanup_devices(self) -> Dict[str, Any]:
        """清理无效设备"""
        return self._request("POST", "/api/devices/cleanup")

    # ==================== 播放列表管理 ====================

    def list_playlists(self, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """获取播放列表列表"""
        return self._request("GET", "/api/playlists/", params={"skip": skip, "limit": limit})

    def get_playlist(self, playlist_id: int) -> Dict[str, Any]:
        """获取播放列表详情"""
        return self._request("GET", f"/api/playlists/{playlist_id}")

    def get_device_playlists(self, device_id: int) -> Dict[str, Any]:
        """获取设备关联的播放列表"""
        return self._request("GET", f"/api/devices/{device_id}/playlists")

    def create_playlist(self, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """创建播放列表"""
        data = {"name": name}
        if description:
            data["description"] = description
        return self._request("POST", "/api/playlists/", json_data=data)

    def update_playlist(self, playlist_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新播放列表"""
        return self._request("PUT", f"/api/playlists/{playlist_id}", json_data=data)

    def delete_playlist(self, playlist_id: int) -> Dict[str, Any]:
        """删除播放列表"""
        return self._request("DELETE", f"/api/playlists/{playlist_id}")

    def assign_playlist(self, playlist_id: int, device_id: int) -> Dict[str, Any]:
        """分配播放列表到设备"""
        return self._request("POST", f"/api/playlists/{playlist_id}/devices/{device_id}")

    def unassign_playlist(self, playlist_id: int, device_id: int) -> Dict[str, Any]:
        """取消播放列表分配"""
        return self._request("DELETE", f"/api/playlists/{playlist_id}/devices/{device_id}")

    def activate_playlist(self, playlist_id: int, device_id: int, is_active: bool = True) -> Dict[str, Any]:
        """激活/停用设备上的播放列表"""
        return self._request(
            "PUT",
            f"/api/playlists/{playlist_id}/devices/{device_id}/activate",
            json_data={"is_active": is_active}
        )

    # ==================== 播放列表项管理 ====================

    def add_playlist_item(
        self,
        playlist_id: int,
        media_id: int,
        display_duration: Optional[int] = None,
        display_order: Optional[int] = None
    ) -> Dict[str, Any]:
        """添加媒体到播放列表"""
        data = {"media_id": media_id}
        if display_duration is not None:
            data["display_duration"] = display_duration
        if display_order is not None:
            data["display_order"] = display_order
        return self._request("POST", f"/api/playlists/{playlist_id}/items", json_data=data)

    def add_playlist_items_batch(
        self,
        playlist_id: int,
        media_ids: List[int],
        display_duration: Optional[int] = None
    ) -> Dict[str, Any]:
        """批量添加媒体到播放列表"""
        data = {
            "media_ids": media_ids,
            "default_duration": display_duration
        }
        return self._request("POST", f"/api/playlists/{playlist_id}/items/batch/", json_data=data)

    def update_playlist_item(
        self,
        playlist_id: int,
        item_id: int,
        display_duration: Optional[int] = None,
        display_order: Optional[int] = None
    ) -> Dict[str, Any]:
        """更新播放列表项"""
        data = {}
        if display_duration is not None:
            data["display_duration"] = display_duration
        if display_order is not None:
            data["display_order"] = display_order
        return self._request("PUT", f"/api/playlists/{playlist_id}/items/{item_id}", json_data=data)

    def remove_playlist_item(
        self,
        playlist_id: int,
        item_id: int
    ) -> Dict[str, Any]:
        """从播放列表移除媒体"""
        return self._request("DELETE", f"/api/playlists/{playlist_id}/items/{item_id}")

    def reorder_playlist_items(
        self,
        playlist_id: int,
        item_ids: List[int]
    ) -> Dict[str, Any]:
        """重新排序播放列表项"""
        # API expects items as [{"id": 1, "order": 0}, {"id": 2, "order": 1}, ...]
        items = [{"id": item_id, "order": order} for order, item_id in enumerate(item_ids)]
        return self._request(
            "PUT",
            f"/api/playlists/{playlist_id}/items/reorder",
            json_data={"items": items}
        )

    # ==================== 播放控制 ====================

    def control_pause(self, device_id: int) -> Dict[str, Any]:
        """发送暂停指令"""
        return self._request("POST", f"/api/control/{device_id}/pause")

    def control_resume(self, device_id: int) -> Dict[str, Any]:
        """发送恢复播放指令"""
        return self._request("POST", f"/api/control/{device_id}/resume")

    def control_volume(self, device_id: int, volume: int) -> Dict[str, Any]:
        """发送音量调节指令"""
        return self._request("POST", f"/api/control/{device_id}/volume", json_data={"volume": volume})

    def control_reload(self, device_id: int) -> Dict[str, Any]:
        """发送重新加载指令"""
        return self._request("POST", f"/api/control/{device_id}/reload")

    def control_next(self, device_id: int) -> Dict[str, Any]:
        """发送下一个指令"""
        return self._request("POST", f"/api/control/{device_id}/next")

    def control_prev(self, device_id: int) -> Dict[str, Any]:
        """发送上一个指令"""
        return self._request("POST", f"/api/control/{device_id}/prev")

    def control_switch(self, device_id: int, playlist_id: int) -> Dict[str, Any]:
        """发送切换播放列表指令"""
        return self._request("POST", f"/api/control/{device_id}/switch", json_data={"playlist_id": playlist_id})

    def control_reboot(self, device_id: int) -> Dict[str, Any]:
        """发送重启指令"""
        return self._request("POST", f"/api/control/{device_id}/reboot")

    # ==================== 媒体管理 ====================

    def list_media(
        self,
        file_type: Optional[str] = None,
        status_filter: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """获取媒体文件列表"""
        params = {"skip": skip, "limit": limit}
        if file_type:
            params["file_type"] = file_type
        if status_filter:
            params["status_filter"] = status_filter
        return self._request("GET", "/api/media/", params=params)

    def get_media(self, media_id: int) -> Dict[str, Any]:
        """获取媒体文件详情"""
        return self._request("GET", f"/api/media/{media_id}")

    def delete_media(self, media_id: int) -> Dict[str, Any]:
        """删除媒体文件"""
        return self._request("DELETE", f"/api/media/{media_id}")

    def upload_media(
        self,
        file_path: str,
        file_type: str,
        slide_duration: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        上传媒体文件

        Args:
            file_path: 本地文件路径
            file_type: 文件类型 (image, video, ppt)
            slide_duration: PPT 幻灯片间隔时长(秒)
        """
        from pathlib import Path
        import mimetypes

        path = Path(file_path)
        if not path.exists():
            raise ValueError(f"文件不存在: {file_path}")

        # 获取文件名和 MIME 类型
        filename = path.name
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type is None:
            mime_type = "application/octet-stream"

        # 构建请求 URL 和参数
        url = f"{self.server_url}/api/media/upload"
        params = {"file_type": file_type}
        if slide_duration is not None:
            params["slide_duration"] = slide_duration

        # 读取文件并上传
        with open(file_path, "rb") as f:
            file_content = f.read()

        with httpx.Client(timeout=self.timeout) as client:
            # 使用 files 参数上传，不设置 Content-Type 让 httpx 自动处理
            headers = {}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"

            response = client.post(
                url,
                params=params,
                files={"file": (filename, file_content, mime_type)},
                headers=headers
            )

        if response.status_code >= 400:
            try:
                error_data = response.json()
                detail = error_data.get("detail", str(error_data))
            except Exception:
                detail = response.text
            raise APIError(response.status_code, response.reason_phrase, detail)

        return response.json()

    # ==================== 状态查询 ====================

    def get_player_status(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取设备播放状态"""
        params = {}
        if status_filter:
            params["status_filter"] = status_filter
        return self._request("GET", "/api/player/status", params=params)

    def get_online_devices(self) -> List[Dict[str, Any]]:
        """获取在线设备列表"""
        return self._request("GET", "/api/player/status", params={"status_filter": "online"})

    # ==================== 排程管理 ====================

    def list_schedules(
        self,
        device_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """获取排程列表"""
        params = {"skip": skip, "limit": limit}
        if device_id:
            params["device_id"] = device_id
        return self._request("GET", "/api/schedules/", params=params)

    def get_schedule(self, schedule_id: int) -> Dict[str, Any]:
        """获取排程详情"""
        return self._request("GET", f"/api/schedules/{schedule_id}")

    def create_schedule(
        self,
        device_id: int,
        playlist_id: int,
        start_time: str,
        end_time: str,
        weekdays: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """创建排程"""
        data = {
            "device_id": device_id,
            "playlist_id": playlist_id,
            "start_time": start_time,
            "end_time": end_time,
        }
        if weekdays is not None:
            # Convert list of weekdays to bitmask (API expects days_of_week)
            bitmask = 0
            for day in weekdays:
                bitmask |= (1 << day)
            data["days_of_week"] = bitmask
        return self._request("POST", "/api/schedules/", json_data=data)

    def update_schedule(
        self,
        schedule_id: int,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        weekdays: Optional[List[int]] = None,
        playlist_id: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        """更新排程"""
        data = {}
        if start_time is not None:
            data["start_time"] = start_time
        if end_time is not None:
            data["end_time"] = end_time
        if weekdays is not None:
            # Convert list of weekdays to bitmask (API expects days_of_week)
            bitmask = 0
            for day in weekdays:
                bitmask |= (1 << day)
            data["days_of_week"] = bitmask
        if playlist_id is not None:
            data["playlist_id"] = playlist_id
        if is_active is not None:
            data["enabled"] = is_active  # API uses 'enabled' not 'is_active'
        return self._request("PUT", f"/api/schedules/{schedule_id}", json_data=data)

    def delete_schedule(self, schedule_id: int) -> Dict[str, Any]:
        """删除排程"""
        return self._request("DELETE", f"/api/schedules/{schedule_id}")

    def get_active_schedule(self, device_id: int) -> Dict[str, Any]:
        """获取设备当前激活的排程"""
        return self._request("GET", "/api/schedules/active", params={"device_id": device_id})


# 全局 API 客户端实例
api_client = APIClient()
