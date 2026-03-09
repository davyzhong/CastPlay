"""
告警配置模型单元测试
"""
import pytest
from datetime import datetime

from app.models.alert import AlertConfig, AlertHistory


class TestAlertConfig:
    """测试告警配置模型"""

    def test_default_config_creation(self):
        """测试默认配置创建"""
        config = AlertConfig.get_default_config()

        assert config.alert_enabled is True
        assert config.offline_alert_enabled is True
        assert config.offline_threshold_hours == 4
        assert config.download_failure_alert_enabled is True
        assert config.download_failure_threshold == 3
        assert config.storage_alert_enabled is True
        assert config.storage_threshold_percent == 90
        assert config.storage_min_free_gb == 1.0
        assert config.playback_alert_enabled is True
        assert config.playback_error_threshold == 5
        assert config.email_enabled is False
        assert config.dingtalk_enabled is False
        assert config.quiet_hours_enabled is False

    def test_config_to_dict(self):
        """测试转换为字典"""
        config = AlertConfig(
            alert_enabled=True,
            offline_threshold_hours=5
        )
        result = config.to_dict()

        assert isinstance(result, dict)
        assert result["alert_enabled"] is True
        assert result["offline_threshold_hours"] == 5
        assert "created_at" in result
        assert "updated_at" in result

    def test_config_with_device_id(self):
        """测试设备级配置"""
        config = AlertConfig(
            device_id=1,
            alert_enabled=True,
            offline_threshold_hours=2
        )

        assert config.device_id == 1
        assert config.offline_threshold_hours == 2

    def test_global_config_no_device_id(self):
        """测试全局配置（无设备 ID）"""
        config = AlertConfig(
            device_id=None,
            alert_enabled=True
        )

        assert config.device_id is None

    def test_quiet_hours_config(self):
        """测试静默时段配置"""
        config = AlertConfig(
            quiet_hours_enabled=True,
            quiet_hours_start="22:00",
            quiet_hours_end="08:00"
        )

        assert config.quiet_hours_enabled is True
        assert config.quiet_hours_start == "22:00"
        assert config.quiet_hours_end == "08:00"

    def test_notification_channels(self):
        """测试通知渠道配置"""
        config = AlertConfig(
            email_enabled=True,
            email_recipients="admin@example.com,user@example.com",
            dingtalk_enabled=True,
            dingtalk_webhook="https://oapi.dingtalk.com/robot/send?access_token=xxx"
        )

        assert config.email_enabled is True
        assert "admin@example.com" in config.email_recipients
        assert config.dingtalk_enabled is True
        assert "oapi.dingtalk.com" in config.dingtalk_webhook

    def test_repr(self):
        """测试字符串表示"""
        config = AlertConfig(id=1, device_id=2, alert_enabled=True)
        repr_str = repr(config)

        assert "AlertConfig" in repr_str
        assert "id=1" in repr_str
        assert "device_id=2" in repr_str


class TestAlertHistory:
    """测试告警历史模型"""

    def test_history_creation(self):
        """测试历史记录创建"""
        history = AlertHistory(
            device_id=1,
            alert_type="offline",
            severity="warning",
            message="Device offline for 5 hours",
            status="pending"  # 显式设置默认值
        )

        assert history.device_id == 1
        assert history.alert_type == "offline"
        assert history.severity == "warning"
        assert history.status == "pending"

    def test_history_to_dict(self):
        """测试转换为字典"""
        history = AlertHistory(
            id=1,
            device_id=1,
            alert_type="download_failed",
            severity="error",
            message="Download failed after 3 retries",
            status="pending"
        )
        result = history.to_dict()

        assert result["id"] == 1
        assert result["device_id"] == 1
        assert result["alert_type"] == "download_failed"
        assert result["severity"] == "error"
        assert result["status"] == "pending"

    def test_history_status_flow(self):
        """测试状态流程"""
        history = AlertHistory(
            device_id=1,
            alert_type="offline",
            severity="warning",
            message="Test alert",
            status="pending"  # 显式设置默认值
        )

        # 初始状态
        assert history.status == "pending"

        # 确认后
        history.status = "acknowledged"
        history.acknowledged_by = 1
        history.acknowledged_at = datetime.utcnow()

        assert history.status == "acknowledged"

        # 解决后
        history.status = "resolved"
        history.resolved_at = datetime.utcnow()

        assert history.status == "resolved"

    def test_alert_types(self):
        """测试不同告警类型"""
        types = ["offline", "download_failed", "storage", "playback_error"]

        for alert_type in types:
            history = AlertHistory(
                device_id=1,
                alert_type=alert_type,
                severity="warning",
                message=f"Test {alert_type}"
            )
            assert history.alert_type == alert_type

    def test_severity_levels(self):
        """测试不同严重级别"""
        severities = ["info", "warning", "error", "critical"]

        for severity in severities:
            history = AlertHistory(
                device_id=1,
                alert_type="offline",
                severity=severity,
                message="Test"
            )
            assert history.severity == severity

    def test_history_with_details(self):
        """测试带详情的历史记录"""
        details = '{"retry_count": 3, "file_size": 1024000}'
        history = AlertHistory(
            device_id=1,
            alert_type="download_failed",
            severity="error",
            message="Download failed",
            details=details
        )

        assert history.details == details

    def test_repr(self):
        """测试字符串表示"""
        history = AlertHistory(
            id=1,
            device_id=1,
            alert_type="offline",
            severity="warning",
            message="Test",
            status="pending"
        )
        repr_str = repr(history)

        assert "AlertHistory" in repr_str
        assert "id=1" in repr_str
        assert "offline" in repr_str
        assert "pending" in repr_str


class TestAlertConfigValidation:
    """测试告警配置验证"""

    def test_valid_threshold_values(self):
        """测试有效的阈值"""
        config = AlertConfig(
            offline_threshold_hours=12,  # 最大 24
            download_failure_threshold=5,  # 最大 10
            storage_threshold_percent=95,  # 最大 99
            storage_min_free_gb=10.0,
            playback_error_threshold=10
        )

        # 应该不抛出异常
        assert config.offline_threshold_hours == 12

    def test_quiet_hours_format(self):
        """测试静默时段格式"""
        # 有效的 HH:MM 格式
        config = AlertConfig(
            quiet_hours_start="22:00",
            quiet_hours_end="08:00"
        )

        assert config.quiet_hours_start == "22:00"
        assert config.quiet_hours_end == "08:00"
