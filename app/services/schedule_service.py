"""
播放列表调度服务
提供调度规则的 CRUD 操作、冲突检测和评估功能
"""
from datetime import datetime, time, date
from typing import List, Optional, Tuple
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.schedule import PlaylistSchedule, DayOfWeek
from app.models.playlist import DevicePlaylist, Playlist
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate, ScheduleConflict


class ScheduleService:
    """播放列表调度服务"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== CRUD 操作 ====================

    def create(self, data: ScheduleCreate) -> Tuple[PlaylistSchedule, List[ScheduleConflict]]:
        """
        创建调度规则

        Args:
            data: 调度创建数据

        Returns:
            (创建的调度对象, 冲突列表)

        Raises:
            ValueError: 验证失败
        """
        # 验证设备-播放列表关联
        if not self._validate_device_playlist(data.device_id, data.playlist_id):
            raise ValueError("playlist not assigned to device")

        # 验证时间范围
        start_time = datetime.strptime(data.start_time, "%H:%M:%S").time()
        end_time = datetime.strptime(data.end_time, "%H:%M:%S").time()
        if end_time <= start_time:
            raise ValueError("start_time must be before end_time")

        # 检测冲突
        conflicts = self.check_conflicts(
            device_id=data.device_id,
            start_time=data.start_time,
            end_time=data.end_time,
            days_of_week=data.days_of_week,
            exclude_id=None,
        )

        # 创建调度
        schedule = PlaylistSchedule(
            device_id=data.device_id,
            playlist_id=data.playlist_id,
            start_time=start_time,
            end_time=end_time,
            days_of_week=data.days_of_week,
            enabled=data.enabled,
            priority=data.priority,
        )

        self.db.add(schedule)
        self.db.commit()
        self.db.refresh(schedule)

        logger.info(f"Created schedule {schedule.id} for device {data.device_id}")
        return schedule, conflicts

    def get_by_id(self, schedule_id: int) -> Optional[PlaylistSchedule]:
        """根据 ID 获取调度"""
        return self.db.query(PlaylistSchedule).filter(PlaylistSchedule.id == schedule_id).first()

    def get_by_device(self, device_id: int, enabled_only: bool = False) -> List[PlaylistSchedule]:
        """
        获取设备的所有调度

        Args:
            device_id: 设备 ID
            enabled_only: 仅返回启用的调度

        Returns:
            调度列表（按开始时间排序）
        """
        query = self.db.query(PlaylistSchedule).filter(PlaylistSchedule.device_id == device_id)

        if enabled_only:
            query = query.filter(PlaylistSchedule.enabled == True)

        return query.order_by(PlaylistSchedule.start_time).all()

    def update(
        self, schedule_id: int, data: ScheduleUpdate
    ) -> Tuple[Optional[PlaylistSchedule], List[ScheduleConflict]]:
        """
        更新调度规则

        Args:
            schedule_id: 调度 ID
            data: 更新数据

        Returns:
            (更新后的调度对象, 冲突列表)
        """
        schedule = self.get_by_id(schedule_id)
        if not schedule:
            return None, []

        # 更新字段
        update_data = data.model_dump(exclude_unset=True)

        # 验证设备-播放列表关联
        device_id = update_data.get("device_id", schedule.device_id)
        playlist_id = update_data.get("playlist_id", schedule.playlist_id)
        if not self._validate_device_playlist(device_id, playlist_id):
            raise ValueError("playlist not assigned to device")

        # 处理时间字段
        if "start_time" in update_data:
            update_data["start_time"] = datetime.strptime(
                update_data["start_time"], "%H:%M:%S"
            ).time()
        if "end_time" in update_data:
            update_data["end_time"] = datetime.strptime(
                update_data["end_time"], "%H:%M:%S"
            ).time()

        # 验证时间范围
        start_time = update_data.get("start_time", schedule.start_time)
        end_time = update_data.get("end_time", schedule.end_time)
        if end_time <= start_time:
            raise ValueError("start_time must be before end_time")

        # 检测冲突
        days_of_week = update_data.get("days_of_week", schedule.days_of_week)
        conflicts = self.check_conflicts(
            device_id=device_id,
            start_time=start_time.strftime("%H:%M:%S") if isinstance(start_time, time) else str(start_time),
            end_time=end_time.strftime("%H:%M:%S") if isinstance(end_time, time) else str(end_time),
            days_of_week=days_of_week,
            exclude_id=schedule_id,
        )

        # 应用更新
        for key, value in update_data.items():
            setattr(schedule, key, value)

        self.db.commit()
        self.db.refresh(schedule)

        logger.info(f"Updated schedule {schedule_id}")
        return schedule, conflicts

    def delete(self, schedule_id: int) -> bool:
        """
        删除调度规则

        Args:
            schedule_id: 调度 ID

        Returns:
            是否删除成功
        """
        schedule = self.get_by_id(schedule_id)
        if not schedule:
            return False

        self.db.delete(schedule)
        self.db.commit()

        logger.info(f"Deleted schedule {schedule_id}")
        return True

    # ==================== 冲突检测 ====================

    def check_conflicts(
        self,
        device_id: int,
        start_time: str,
        end_time: str,
        days_of_week: int,
        exclude_id: Optional[int] = None,
    ) -> List[ScheduleConflict]:
        """
        检测时间冲突

        Args:
            device_id: 设备 ID
            start_time: 开始时间 (HH:MM:SS)
            end_time: 结束时间 (HH:MM:SS)
            days_of_week: 星期位掩码
            exclude_id: 排除的调度 ID（用于更新时排除自身）

        Returns:
            冲突列表
        """
        conflicts = []

        # 获取同一设备的所有启用的调度
        query = self.db.query(PlaylistSchedule).filter(
            PlaylistSchedule.device_id == device_id,
            PlaylistSchedule.enabled == True,
        )
        if exclude_id:
            query = query.filter(PlaylistSchedule.id != exclude_id)

        existing_schedules = query.all()

        # 转换时间字符串为 time 对象
        new_start = datetime.strptime(start_time, "%H:%M:%S").time()
        new_end = datetime.strptime(end_time, "%H:%M:%S").time()

        for existing in existing_schedules:
            # 检查时间重叠
            if self._times_overlap(new_start, new_end, existing.start_time, existing.end_time):
                # 检查星期重叠
                if self._days_overlap(days_of_week, existing.days_of_week):
                    # 获取播放列表名称
                    playlist = (
                        self.db.query(Playlist)
                        .filter(Playlist.id == existing.playlist_id)
                        .first()
                    )
                    playlist_name = playlist.name if playlist else f"Playlist {existing.playlist_id}"

                    # 生成重叠描述
                    overlap_desc = self._describe_overlap(
                        new_start, new_end, existing.start_time, existing.end_time, days_of_week
                    )

                    conflicts.append(
                        ScheduleConflict(
                            schedule_id=existing.id,
                            playlist_name=playlist_name,
                            overlap=overlap_desc,
                        )
                    )

        return conflicts

    def _times_overlap(self, start1: time, end1: time, start2: time, end2: time) -> bool:
        """检查两个时间范围是否重叠"""
        return start1 < end2 and start2 < end1

    def _days_overlap(self, days1: int, days2: int) -> bool:
        """检查两个星期位掩码是否有交集"""
        return (days1 & days2) != 0

    def _describe_overlap(
        self, new_start: time, new_end: time, exist_start: time, exist_end: time, days: int
    ) -> str:
        """生成重叠描述"""
        overlap_start = max(new_start, exist_start)
        overlap_end = min(new_end, exist_end)
        days_display = self._days_to_display(days)
        return f"{overlap_start.strftime('%H:%M')}-{overlap_end.strftime('%H:%M')} on {','.join(days_display)}"

    def _days_to_display(self, days_of_week: int) -> List[str]:
        """将星期位掩码转换为显示列表"""
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        return [day_names[i] for i in range(7) if days_of_week & (1 << i)]

    # ==================== 调度评估 ====================

    def get_active_schedule(self, device_id: int) -> Optional[PlaylistSchedule]:
        """
        获取设备当前应该激活的调度

        Args:
            device_id: 设备 ID

        Returns:
            当前激活的调度，如果没有则返回 None
        """
        now = datetime.now()
        current_time = now.time()
        current_day = now.weekday()  # 0=Monday, 6=Sunday
        day_bit = 1 << current_day

        # 查询当前时间匹配且启用的调度
        schedules = (
            self.db.query(PlaylistSchedule)
            .filter(
                PlaylistSchedule.device_id == device_id,
                PlaylistSchedule.enabled == True,
                PlaylistSchedule.start_time <= current_time,
                PlaylistSchedule.end_time > current_time,
            )
            .all()
        )

        # 过滤匹配当前星期的调度
        matching = [s for s in schedules if s.days_of_week & day_bit]

        if not matching:
            return None

        # 按优先级排序（高优先级优先），同优先级按创建时间（最新优先）
        matching.sort(key=lambda s: (s.priority, s.created_at), reverse=True)
        return matching[0]

    def get_default_playlist_id(self, device_id: int) -> Optional[int]:
        """
        获取设备的默认播放列表 ID

        默认播放列表 = 最早分配的播放列表（device_playlists.id 最小）

        Args:
            device_id: 设备 ID

        Returns:
            默认播放列表 ID，如果没有则返回 None
        """
        first_assignment = (
            self.db.query(DevicePlaylist)
            .filter(DevicePlaylist.device_id == device_id)
            .order_by(DevicePlaylist.id)
            .first()
        )
        return first_assignment.playlist_id if first_assignment else None

    # ==================== 辅助方法 ====================

    def _validate_device_playlist(self, device_id: int, playlist_id: int) -> bool:
        """验证播放列表是否已分配给设备"""
        exists = (
            self.db.query(DevicePlaylist)
            .filter(
                DevicePlaylist.device_id == device_id,
                DevicePlaylist.playlist_id == playlist_id,
            )
            .first()
        )
        return exists is not None

    # ==================== 星期位掩码辅助函数 ====================

    @staticmethod
    def days_to_bitmask(days: List[int]) -> int:
        """
        将星期列表转换为位掩码

        Args:
            days: 星期列表 (0=Monday, ..., 6=Sunday)

        Returns:
            位掩码值
        """
        bitmask = 0
        for day in days:
            if 0 <= day <= 6:
                bitmask |= 1 << day
        return bitmask

    @staticmethod
    def bitmask_to_days(bitmask: int) -> List[int]:
        """
        将位掩码转换为星期列表

        Args:
            bitmask: 位掩码值

        Returns:
            星期列表 (0=Monday, ..., 6=Sunday)
        """
        return [i for i in range(7) if bitmask & (1 << i)]

    @staticmethod
    def is_day_in_bitmask(day: int, bitmask: int) -> bool:
        """
        检查指定星期是否在位掩码中

        Args:
            day: 星期几 (0=Monday, ..., 6=Sunday)
            bitmask: 位掩码值

        Returns:
            是否包含该天
        """
        return bool(bitmask & (1 << day))
