"""
时区工具单元测试
"""
import pytest
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.utils.timezone import (
    get_device_timezone,
    utc_to_device_time,
    device_time_to_utc,
    is_time_in_range,
    get_device_current_time,
    parse_time_string,
    check_device_schedule,
    get_next_scheduled_event
)


class TestGetDeviceTimezone:
    """测试获取设备时区"""

    def test_valid_timezone(self):
        """测试有效时区"""
        tz = get_device_timezone("Asia/Shanghai")
        assert isinstance(tz, ZoneInfo)
        assert str(tz) == "Asia/Shanghai"

    def test_empty_timezone_returns_utc(self):
        """测试空时区返回 UTC"""
        tz = get_device_timezone(None)
        assert str(tz) == "UTC"

        tz = get_device_timezone("")
        assert str(tz) == "UTC"

    def test_invalid_timezone_fallback_to_utc(self):
        """测试无效时区回退到 UTC"""
        tz = get_device_timezone("Invalid/Timezone")
        assert str(tz) == "UTC"


class TestUtcToDeviceTime:
    """测试 UTC 转设备时间"""

    def test_convert_utc_to_shanghai(self):
        """测试 UTC 转上海时间"""
        # UTC 00:00 -> 上海 08:00
        utc_dt = datetime(2024, 1, 1, 0, 0, 0, tzinfo=ZoneInfo("UTC"))
        local_dt = utc_to_device_time(utc_dt, "Asia/Shanghai")

        assert local_dt.hour == 8
        assert local_dt.tzinfo is not None

    def test_convert_without_timezone_info(self):
        """测试无时区信息的 UTC 时间"""
        utc_dt = datetime(2024, 1, 1, 0, 0, 0)  # 无时区信息
        local_dt = utc_to_device_time(utc_dt, "Asia/Shanghai")

        # 应该自动添加 UTC 时区
        assert local_dt.tzinfo is not None

    def test_convert_none_returns_none(self):
        """测试 None 输入"""
        result = utc_to_device_time(None, "Asia/Shanghai")
        assert result is None


class TestDeviceTimeToUtc:
    """测试设备时间转 UTC"""

    def test_convert_shanghai_to_utc(self):
        """测试上海时间转 UTC"""
        local_dt = datetime(2024, 1, 1, 8, 0, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
        utc_dt = device_time_to_utc(local_dt, "Asia/Shanghai")

        assert utc_dt.hour == 0
        assert str(utc_dt.tzinfo) == "UTC"

    def test_convert_none_returns_none(self):
        """测试 None 输入"""
        result = device_time_to_utc(None, "Asia/Shanghai")
        assert result is None


class TestIsTimeInRange:
    """测试时间范围检查"""

    def test_time_in_normal_range(self):
        """测试在正常范围内"""
        check_time = time(10, 0)
        start_time = time(8, 0)
        end_time = time(18, 0)

        assert is_time_in_range(check_time, start_time, end_time) is True

    def test_time_outside_normal_range(self):
        """测试在正常范围外"""
        check_time = time(6, 0)
        start_time = time(8, 0)
        end_time = time(18, 0)

        assert is_time_in_range(check_time, start_time, end_time) is False

    def test_time_cross_midnight_in_range(self):
        """测试跨午夜范围（在范围内）"""
        # 23:00 - 02:00 的范围
        check_time = time(23, 30)
        start_time = time(23, 0)
        end_time = time(2, 0)

        assert is_time_in_range(check_time, start_time, end_time) is True

        # 凌晨 1 点也应该在范围内
        check_time = time(1, 0)
        assert is_time_in_range(check_time, start_time, end_time) is True

    def test_time_cross_midnight_out_range(self):
        """测试跨午夜范围（在范围外）"""
        # 23:00 - 02:00 的范围
        check_time = time(12, 0)  # 中午不在范围内
        start_time = time(23, 0)
        end_time = time(2, 0)

        assert is_time_in_range(check_time, start_time, end_time) is False


class TestParseTimeString:
    """测试时间字符串解析"""

    def test_parse_hh_mm(self):
        """解析 HH:MM 格式"""
        result = parse_time_string("08:30")
        assert result == time(8, 30)

    def test_parse_hh_mm_ss(self):
        """解析 HH:MM:SS 格式"""
        result = parse_time_string("08:30:45")
        assert result == time(8, 30, 45)

    def test_parse_empty_returns_none(self):
        """解析空字符串"""
        assert parse_time_string(None) is None
        assert parse_time_string("") is None

    def test_parse_invalid_returns_none(self):
        """解析无效格式"""
        assert parse_time_string("invalid") is None
        assert parse_time_string("25:00") is None  # 无效小时


class TestCheckDeviceSchedule:
    """测试设备定时检查"""

    def test_should_play_in_schedule(self):
        """测试在播放时间内"""
        # 当前时间在 08:00 - 18:00 范围内
        should_play, reason = check_device_schedule(
            "Asia/Shanghai",
            "08:00",
            "18:00"
        )
        # 结果取决于当前时间
        assert isinstance(should_play, bool)
        assert isinstance(reason, str)

    def test_no_schedule_means_play(self):
        """测试无定时配置时默认播放"""
        should_play, reason = check_device_schedule(
            "Asia/Shanghai",
            None,
            None
        )
        assert should_play is True
        assert "No schedule" in reason

    def test_weekday_restriction(self):
        """测试工作日限制"""
        # 只在工作日播放（周一到周五）
        should_play, reason = check_device_schedule(
            "Asia/Shanghai",
            "08:00",
            "18:00",
            weekdays=[0, 1, 2, 3, 4]  # 周一到周五
        )
        # 结果取决于今天是周几
        assert isinstance(should_play, bool)

    def test_weekend_only(self):
        """测试仅周末"""
        should_play, reason = check_device_schedule(
            "Asia/Shanghai",
            "08:00",
            "18:00",
            weekdays=[5, 6]  # 周六周日
        )
        assert isinstance(should_play, bool)


class TestGetNextScheduledEvent:
    """测试获取下一个定时事件"""

    def test_returns_event_info(self):
        """测试返回事件信息"""
        next_time, event_type = get_next_scheduled_event(
            "Asia/Shanghai",
            "08:00",
            "18:00"
        )

        # 应该返回时间或 None
        if next_time:
            assert isinstance(next_time, datetime)
            assert event_type in ["power_on", "power_off", "none"]

    def test_no_schedule_returns_none(self):
        """测试无定时配置"""
        next_time, event_type = get_next_scheduled_event(
            "Asia/Shanghai",
            None,
            None
        )
        assert next_time is None
        assert event_type == "none"


class TestGetDeviceCurrentTime:
    """测试获取设备当前时间"""

    def test_returns_datetime_with_timezone(self):
        """测试返回带时区的 datetime"""
        now = get_device_current_time("Asia/Shanghai")

        assert isinstance(now, datetime)
        assert now.tzinfo is not None

    def test_utc_timezone(self):
        """测试 UTC 时区"""
        now = get_device_current_time(None)

        assert isinstance(now, datetime)
        assert str(now.tzinfo) == "UTC"
