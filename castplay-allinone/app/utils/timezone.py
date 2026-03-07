"""
时区工具模块
提供 UTC 与设备时区转换、时间范围检查等功能
"""
from datetime import datetime, timedelta, time
from typing import Optional, Tuple
from zoneinfo import ZoneInfo
import logging

logger = logging.getLogger(__name__)


def get_device_timezone(timezone_str: Optional[str]) -> ZoneInfo:
    """
    获取设备时区对象

    Args:
        timezone_str: 时区字符串（如 "Asia/Shanghai"），为空则使用 UTC

    Returns:
        ZoneInfo 对象
    """
    if not timezone_str:
        return ZoneInfo("UTC")

    try:
        return ZoneInfo(timezone_str)
    except Exception as e:
        logger.warning(f"Invalid timezone '{timezone_str}', falling back to UTC: {e}")
        return ZoneInfo("UTC")


def utc_to_device_time(utc_dt: datetime, timezone_str: Optional[str]) -> datetime:
    """
    将 UTC 时间转换为设备本地时间

    Args:
        utc_dt: UTC 时间的 datetime 对象
        timezone_str: 设备时区字符串

    Returns:
        设备本地时间的 datetime 对象
    """
    if utc_dt is None:
        return None

    tz = get_device_timezone(timezone_str)

    # 确保 UTC 时间带时区信息
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=ZoneInfo("UTC"))

    return utc_dt.astimezone(tz)


def device_time_to_utc(local_dt: datetime, timezone_str: Optional[str]) -> datetime:
    """
    将设备本地时间转换为 UTC 时间

    Args:
        local_dt: 本地时间的 datetime 对象
        timezone_str: 设备时区字符串

    Returns:
        UTC 时间的 datetime 对象
    """
    if local_dt is None:
        return None

    tz = get_device_timezone(timezone_str)

    # 如果时间没有时区信息，假设为设备本地时间
    if local_dt.tzinfo is None:
        local_dt = local_dt.replace(tzinfo=tz)

    return local_dt.astimezone(ZoneInfo("UTC"))


def is_time_in_range(
    check_time: time,
    start_time: time,
    end_time: time
) -> bool:
    """
    检查时间是否在指定范围内

    支持跨午夜的时间范围（如 23:00 - 02:00）

    Args:
        check_time: 要检查的时间
        start_time: 开始时间
        end_time: 结束时间

    Returns:
        是否在范围内
    """
    if start_time <= end_time:
        # 正常范围（如 08:00 - 18:00）
        return start_time <= check_time <= end_time
    else:
        # 跨午夜范围（如 23:00 - 02:00）
        return check_time >= start_time or check_time <= end_time


def get_device_current_time(timezone_str: Optional[str]) -> datetime:
    """
    获取设备当前本地时间

    Args:
        timezone_str: 设备时区字符串

    Returns:
        设备本地当前时间
    """
    tz = get_device_timezone(timezone_str)
    return datetime.now(tz)


def parse_time_string(time_str: str) -> Optional[time]:
    """
    解析时间字符串

    Args:
        time_str: 时间字符串（格式：HH:MM 或 HH:MM:SS）

    Returns:
        time 对象，解析失败返回 None
    """
    if not time_str:
        return None

    try:
        parts = time_str.split(":")
        if len(parts) == 2:
            return time(int(parts[0]), int(parts[1]))
        elif len(parts) == 3:
            return time(int(parts[0]), int(parts[1]), int(parts[2]))
        else:
            return None
    except (ValueError, IndexError) as e:
        logger.warning(f"Failed to parse time string '{time_str}': {e}")
        return None


def check_device_schedule(
    timezone_str: Optional[str],
    power_on_time: Optional[str],
    power_off_time: Optional[str],
    weekdays: Optional[list[int]] = None
) -> Tuple[bool, Optional[str]]:
    """
    检查设备当前是否应该处于播放状态

    Args:
        timezone_str: 设备时区字符串
        power_on_time: 开机时间字符串（HH:MM）
        power_off_time: 关机时间字符串（HH:MM）
        weekdays: 工作日列表（0=周一, 6=周日），为空则每天都工作

    Returns:
        Tuple[是否应该播放, 原因说明]
    """
    # 获取设备本地当前时间
    now = get_device_current_time(timezone_str)
    current_time = now.time()
    current_weekday = now.weekday()  # 0=周一, 6=周日

    # 检查工作日
    if weekdays is not None and len(weekdays) > 0:
        if current_weekday not in weekdays:
            return False, f"Not a working day (weekday={current_weekday})"

    # 如果没有设置开关机时间，默认应该播放
    if not power_on_time or not power_off_time:
        return True, "No schedule configured"

    # 解析时间
    on_time = parse_time_string(power_on_time)
    off_time = parse_time_string(power_off_time)

    if on_time is None or off_time is None:
        logger.warning(f"Invalid schedule time: on={power_on_time}, off={power_off_time}")
        return True, "Invalid schedule time"

    # 检查是否在播放时间范围内
    if is_time_in_range(current_time, on_time, off_time):
        return True, f"Within scheduled time ({power_on_time} - {power_off_time})"
    else:
        return False, f"Outside scheduled time (current={current_time.strftime('%H:%M')}, schedule={power_on_time} - {power_off_time})"


def get_next_scheduled_event(
    timezone_str: Optional[str],
    power_on_time: Optional[str],
    power_off_time: Optional[str],
    weekdays: Optional[list[int]] = None
) -> Tuple[Optional[datetime], str]:
    """
    获取下一个定时事件（开机或关机）

    Args:
        timezone_str: 设备时区字符串
        power_on_time: 开机时间字符串
        power_off_time: 关机时间字符串
        weekdays: 工作日列表

    Returns:
        Tuple[下次事件时间, 事件类型（'power_on' 或 'power_off'）]
    """
    if not power_on_time or not power_off_time:
        return None, "none"

    now = get_device_current_time(timezone_str)
    on_time = parse_time_string(power_on_time)
    off_time = parse_time_string(power_off_time)

    if on_time is None or off_time is None:
        return None, "none"

    # 获取今天的开关机时间
    today_on = datetime.combine(now.date(), on_time, tzinfo=now.tzinfo)
    today_off = datetime.combine(now.date(), off_time, tzinfo=now.tzinfo)

    # 判断当前是否应该在播放
    should_play, _ = check_device_schedule(
        timezone_str, power_on_time, power_off_time, weekdays
    )

    if should_play:
        # 当前应该播放，下一个事件是关机
        if today_off > now:
            return today_off, "power_off"
        else:
            # 跨午夜情况，关机时间是明天
            return today_off + timedelta(days=1), "power_off"
    else:
        # 当前不应该播放，下一个事件是开机
        if today_on > now:
            return today_on, "power_on"
        else:
            # 开机时间已过，检查下一个工作日
            next_day = now + timedelta(days=1)
            for _ in range(7):  # 最多检查 7 天
                if weekdays is None or len(weekdays) == 0 or next_day.weekday() in weekdays:
                    return datetime.combine(next_day.date(), on_time, tzinfo=now.tzinfo), "power_on"
                next_day += timedelta(days=1)
            return None, "none"
