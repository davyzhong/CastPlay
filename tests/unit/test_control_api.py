"""
播放控制 API 单元测试

测试 app/api/control.py 中的远程控制 API 端点
使用 mock 隔离测试 API 层，不依赖实际 WebSocket 连接
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from pydantic import ValidationError

from app.api.control import VolumeRequest, SwitchPlaylistRequest


class TestVolumeRequestModel:
    """测试音量请求模型"""

    def test_volume_request_valid(self):
        """测试有效音量请求"""
        request = VolumeRequest(volume=50)
        assert request.volume == 50

    def test_volume_request_boundary_min(self):
        """测试音量边界值：最小值 0"""
        request = VolumeRequest(volume=0)
        assert request.volume == 0

    def test_volume_request_boundary_max(self):
        """测试音量边界值：最大值 100"""
        request = VolumeRequest(volume=100)
        assert request.volume == 100

    def test_volume_request_invalid_high(self):
        """测试无效音量：超过最大值 100"""
        with pytest.raises(ValidationError):
            VolumeRequest(volume=101)

    def test_volume_request_invalid_negative(self):
        """测试无效音量：负数"""
        with pytest.raises(ValidationError):
            VolumeRequest(volume=-1)

    def test_volume_request_invalid_very_high(self):
        """测试无效音量：非常大的值"""
        with pytest.raises(ValidationError):
            VolumeRequest(volume=200)


class TestSwitchPlaylistRequestModel:
    """测试切换播放列表请求模型"""

    def test_switch_playlist_request_valid(self):
        """测试有效切换播放列表请求"""
        request = SwitchPlaylistRequest(playlist_id=5)
        assert request.playlist_id == 5

    def test_switch_playlist_request_min_id(self):
        """测试最小播放列表 ID"""
        request = SwitchPlaylistRequest(playlist_id=1)
        assert request.playlist_id == 1

    def test_switch_playlist_request_missing(self):
        """测试缺少播放列表 ID"""
        with pytest.raises(ValidationError):
            SwitchPlaylistRequest()


class TestControlEndpointsAuthentication:
    """测试控制端点认证要求"""

    def test_pause_requires_auth(self, client, test_device):
        """测试暂停需要认证"""
        response = client.post(f"/api/control/{test_device.id}/pause")
        assert response.status_code in [401, 403]

    def test_resume_requires_auth(self, client, test_device):
        """测试恢复播放需要认证"""
        response = client.post(f"/api/control/{test_device.id}/resume")
        assert response.status_code in [401, 403]

    def test_volume_requires_auth(self, client, test_device):
        """测试音量调节需要认证"""
        response = client.post(
            f"/api/control/{test_device.id}/volume",
            json={"volume": 50},
        )
        assert response.status_code in [401, 403]

    def test_reload_requires_auth(self, client, test_device):
        """测试重新加载需要认证"""
        response = client.post(f"/api/control/{test_device.id}/reload")
        assert response.status_code in [401, 403]

    def test_next_requires_auth(self, client, test_device):
        """测试下一个需要认证"""
        response = client.post(f"/api/control/{test_device.id}/next")
        assert response.status_code in [401, 403]

    def test_prev_requires_auth(self, client, test_device):
        """测试上一个需要认证"""
        response = client.post(f"/api/control/{test_device.id}/prev")
        assert response.status_code in [401, 403]

    def test_switch_requires_auth(self, client, test_device):
        """测试切换播放列表需要认证"""
        response = client.post(
            f"/api/control/{test_device.id}/switch",
            json={"playlist_id": 5},
        )
        assert response.status_code in [401, 403]

    def test_reboot_requires_auth(self, client, test_device):
        """测试重启需要认证"""
        response = client.post(f"/api/control/{test_device.id}/reboot")
        assert response.status_code in [401, 403]


class TestControlEndpointsValidation:
    """测试控制端点请求验证"""

    def test_volume_out_of_range_high(self, client, test_device, auth_headers):
        """测试音量超出范围（高）"""
        response = client.post(
            f"/api/control/{test_device.id}/volume",
            headers=auth_headers,
            json={"volume": 101},
        )
        assert response.status_code == 422

    def test_volume_out_of_range_low(self, client, test_device, auth_headers):
        """测试音量超出范围（低）"""
        response = client.post(
            f"/api/control/{test_device.id}/volume",
            headers=auth_headers,
            json={"volume": -1},
        )
        assert response.status_code == 422

    def test_switch_missing_playlist_id(self, client, test_device, auth_headers):
        """测试切换播放列表缺少 ID"""
        response = client.post(
            f"/api/control/{test_device.id}/switch",
            headers=auth_headers,
            json={},
        )
        assert response.status_code == 422


class TestControlEndpointsDeviceNotFound:
    """测试控制端点设备未找到的情况"""

    def test_pause_device_not_found(self, client, auth_headers):
        """测试暂停不存在的设备"""
        response = client.post(
            "/api/control/99999/pause",
            headers=auth_headers,
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_resume_device_not_found(self, client, auth_headers):
        """测试恢复播放不存在的设备"""
        response = client.post(
            "/api/control/99999/resume",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_volume_device_not_found(self, client, auth_headers):
        """测试音量调节不存在的设备"""
        response = client.post(
            "/api/control/99999/volume",
            headers=auth_headers,
            json={"volume": 50},
        )
        assert response.status_code == 404

    def test_reload_device_not_found(self, client, auth_headers):
        """测试重新加载不存在的设备"""
        response = client.post(
            "/api/control/99999/reload",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_next_device_not_found(self, client, auth_headers):
        """测试下一个不存在的设备"""
        response = client.post(
            "/api/control/99999/next",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_prev_device_not_found(self, client, auth_headers):
        """测试上一个不存在的设备"""
        response = client.post(
            "/api/control/99999/prev",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_switch_device_not_found(self, client, auth_headers):
        """测试切换播放列表不存在的设备"""
        response = client.post(
            "/api/control/99999/switch",
            headers=auth_headers,
            json={"playlist_id": 5},
        )
        assert response.status_code == 404

    def test_reboot_device_not_found(self, client, auth_headers):
        """测试重启不存在的设备"""
        response = client.post(
            "/api/control/99999/reboot",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestNotificationServiceIntegration:
    """测试通知服务集成"""

    def test_notification_service_import(self):
        """测试通知服务可以正确导入"""
        from app.services.notification import NotificationService
        assert NotificationService is not None

    def test_notification_service_is_device_online(self):
        """测试检查设备在线状态方法存在"""
        from app.services.notification import NotificationService
        # 验证方法存在
        assert hasattr(NotificationService, 'is_device_online')

    def test_notification_service_send_pause(self):
        """测试暂停方法存在"""
        from app.services.notification import NotificationService
        assert hasattr(NotificationService, 'send_pause')

    def test_notification_service_send_volume(self):
        """测试音量方法存在"""
        from app.services.notification import NotificationService
        assert hasattr(NotificationService, 'send_volume')

    def test_notification_service_send_switch_playlist(self):
        """测试切换播放列表方法存在"""
        from app.services.notification import NotificationService
        assert hasattr(NotificationService, 'send_switch_playlist')
