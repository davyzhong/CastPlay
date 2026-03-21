"""
播放列表调度服务单元测试
TDD Tests: T007, T008, T010
"""
from datetime import datetime, time, timedelta
from unittest.mock import patch, MagicMock

import pytest
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.orm import Session

from app.models.schedule import PlaylistSchedule, DayOfWeek
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate
from app.services.schedule_service import ScheduleService


class TestTimeRangeValidation:
    """T007: 时间范围验证测试 (start < end)"""

    def test_create_schedule_with_valid_time_range(self, db_session: Session, test_device, test_playlist):
        """测试有效的时间范围（start < end）"""
        # Arrange: 设置设备播放列表关联
        from app.models.playlist import DevicePlaylist
        assignment = DevicePlaylist(
            device_id=test_device.id,
            playlist_id=test_playlist.id
        )
        db_session.add(assignment)
        db_session.commit()

        service = ScheduleService(db_session)
        data = ScheduleCreate(
            device_id=test_device.id,
            playlist_id=test_playlist.id,
            start_time="09:00:00",
            end_time="17:00:00",
            days_of_week=127,
            enabled=True,
            priority=0
        )

        # Act
        schedule, conflicts = service.create(data)

        # Assert
        assert schedule is not None
        assert schedule.start_time == time(9, 0, 0)
        assert schedule.end_time == time(17, 0, 0)

    def test_create_schedule_with_invalid_time_range_raises_error(
        self, db_session: Session, test_device, test_playlist
    ):
        """测试无效的时间范围（start >= end）应抛出 Pydantic 验证异常"""
        # Arrange
        from app.models.playlist import DevicePlaylist
        assignment = DevicePlaylist(
            device_id=test_device.id,
            playlist_id=test_playlist.id
        )
        db_session.add(assignment)
        db_session.commit()

        # Act & Assert - 验证在 Pydantic 层级捕获
        with pytest.raises(PydanticValidationError, match="end_time must be greater than start_time"):
            ScheduleCreate(
                device_id=test_device.id,
                playlist_id=test_playlist.id,
                start_time="17:00:00",
                end_time="09:00:00",  # end < start, should fail
                days_of_week=127,
                enabled=True,
                priority=0
            )

    def test_create_schedule_with_same_time_raises_error(
        self, db_session: Session, test_device, test_playlist
    ):
        """测试相同时间（start == end）应抛出 Pydantic 验证异常"""
        # Arrange
        from app.models.playlist import DevicePlaylist
        assignment = DevicePlaylist(
            device_id=test_device.id,
            playlist_id=test_playlist.id
        )
        db_session.add(assignment)
        db_session.commit()

        # Act & Assert - 验证在 Pydantic 层级捕获
        with pytest.raises(PydanticValidationError, match="end_time must be greater than start_time"):
            ScheduleCreate(
                device_id=test_device.id,
                playlist_id=test_playlist.id,
                start_time="12:00:00",
                end_time="12:00:00",  # same time, should fail
                days_of_week=127,
                enabled=True,
                priority=0
            )

    def test_update_schedule_with_invalid_time_range_raises_error(
        self, db_session: Session, test_device, test_playlist
    ):
        """测试更新时无效时间范围应抛出 Pydantic 验证异常"""
        # Arrange: 创建一个有效的调度
        from app.models.playlist import DevicePlaylist
        assignment = DevicePlaylist(
            device_id=test_device.id,
            playlist_id=test_playlist.id
        )
        db_session.add(assignment)
        db_session.commit()

        service = ScheduleService(db_session)
        create_data = ScheduleCreate(
            device_id=test_device.id,
            playlist_id=test_playlist.id,
            start_time="09:00:00",
            end_time="17:00:00",
            days_of_week=127,
            enabled=True,
            priority=0
        )
        schedule, _ = service.create(create_data)

        # Act & Assert - 验证在 Pydantic 层级捕获
        with pytest.raises(PydanticValidationError, match="end_time must be greater than start_time"):
            ScheduleUpdate(
                start_time="17:00:00",
                end_time="09:00:00"
            )


class TestDaysOfWeekBitmaskValidation:
    """T008: 星期位掩码验证测试"""

    def test_valid_bitmask_all_week(self, db_session: Session, test_device, test_playlist):
        """测试有效位掩码：全周 (127)"""
        from app.models.playlist import DevicePlaylist
        assignment = DevicePlaylist(
            device_id=test_device.id,
            playlist_id=test_playlist.id
        )
        db_session.add(assignment)
        db_session.commit()

        service = ScheduleService(db_session)
        data = ScheduleCreate(
            device_id=test_device.id,
            playlist_id=test_playlist.id,
            start_time="09:00:00",
            end_time="17:00:00",
            days_of_week=127,  # All week
            enabled=True,
            priority=0
        )

        schedule, _ = service.create(data)
        assert schedule.days_of_week == 127

    def test_valid_bitmask_weekdays_only(self, db_session: Session, test_device, test_playlist):
        """测试有效位掩码：仅工作日 (31 = Mon-Fri)"""
        from app.models.playlist import DevicePlaylist
        assignment = DevicePlaylist(
            device_id=test_device.id,
            playlist_id=test_playlist.id
        )
        db_session.add(assignment)
        db_session.commit()

        service = ScheduleService(db_session)
        data = ScheduleCreate(
            device_id=test_device.id,
            playlist_id=test_playlist.id,
            start_time="09:00:00",
            end_time="17:00:00",
            days_of_week=DayOfWeek.WEEKDAYS,  # 31 = Mon-Fri
            enabled=True,
            priority=0
        )

        schedule, _ = service.create(data)
        assert schedule.days_of_week == 31
        assert schedule.is_active_on_day(0)  # Monday
        assert schedule.is_active_on_day(4)  # Friday
        assert not schedule.is_active_on_day(5)  # Saturday
        assert not schedule.is_active_on_day(6)  # Sunday

    def test_valid_bitmask_weekends_only(self, db_session: Session, test_device, test_playlist):
        """测试有效位掩码：仅周末 (96 = Sat-Sun)"""
        from app.models.playlist import DevicePlaylist
        assignment = DevicePlaylist(
            device_id=test_device.id,
            playlist_id=test_playlist.id
        )
        db_session.add(assignment)
        db_session.commit()

        service = ScheduleService(db_session)
        data = ScheduleCreate(
            device_id=test_device.id,
            playlist_id=test_playlist.id,
            start_time="09:00:00",
            end_time="17:00:00",
            days_of_week=DayOfWeek.WEEKENDS,  # 96 = Sat-Sun
            enabled=True,
            priority=0
        )

        schedule, _ = service.create(data)
        assert schedule.days_of_week == 96
        assert not schedule.is_active_on_day(0)  # Monday
        assert schedule.is_active_on_day(5)  # Saturday
        assert schedule.is_active_on_day(6)  # Sunday

    def test_valid_bitmask_single_day(self, db_session: Session, test_device, test_playlist):
        """测试有效位掩码：单天"""
        from app.models.playlist import DevicePlaylist
        assignment = DevicePlaylist(
            device_id=test_device.id,
            playlist_id=test_playlist.id
        )
        db_session.add(assignment)
        db_session.commit()

        service = ScheduleService(db_session)
        data = ScheduleCreate(
            device_id=test_device.id,
            playlist_id=test_playlist.id,
            start_time="09:00:00",
            end_time="17:00:00",
            days_of_week=DayOfWeek.MONDAY,  # 1 = Monday only
            enabled=True,
            priority=0
        )

        schedule, _ = service.create(data)
        assert schedule.days_of_week == 1
        assert schedule.is_active_on_day(0)  # Monday
        assert not schedule.is_active_on_day(1)  # Tuesday

    def test_bitmask_helper_methods(self):
        """测试位掩码辅助方法"""
        # Test days_to_bitmask
        assert ScheduleService.days_to_bitmask([0, 1, 2, 3, 4]) == 31  # Mon-Fri
        assert ScheduleService.days_to_bitmask([5, 6]) == 96  # Sat-Sun
        assert ScheduleService.days_to_bitmask([0, 2, 4, 6]) == 85  # Mon, Wed, Fri, Sun

        # Test bitmask_to_days
        assert ScheduleService.bitmask_to_days(31) == [0, 1, 2, 3, 4]
        assert ScheduleService.bitmask_to_days(96) == [5, 6]
        assert ScheduleService.bitmask_to_days(127) == [0, 1, 2, 3, 4, 5, 6]

        # Test is_day_in_bitmask
        assert ScheduleService.is_day_in_bitmask(0, DayOfWeek.MONDAY) is True
        assert ScheduleService.is_day_in_bitmask(1, DayOfWeek.MONDAY) is False


class TestScheduleEvaluationLogic:
    """T010: 调度评估逻辑测试"""

    def _setup_device_with_playlists(
        self, db_session: Session, test_device, num_playlists: int = 2
    ):
        """辅助方法：为设备设置多个播放列表"""
        from app.models.playlist import Playlist, DevicePlaylist

        playlists = []
        for i in range(num_playlists):
            playlist = Playlist(name=f"Test Playlist {i}")
            db_session.add(playlist)
            db_session.flush()
            playlists.append(playlist)

            assignment = DevicePlaylist(
                device_id=test_device.id,
                playlist_id=playlist.id
            )
            db_session.add(assignment)

        db_session.commit()
        return playlists

    def test_get_active_schedule_no_schedules(self, db_session: Session, test_device):
        """测试无调度时返回 None"""
        service = ScheduleService(db_session)
        result = service.get_active_schedule(test_device.id)
        assert result is None

    def test_get_active_schedule_matching_time_and_day(self, db_session: Session, test_device):
        """测试当前时间和星期匹配时返回调度"""
        playlists = self._setup_device_with_playlists(db_session, test_device)

        service = ScheduleService(db_session)
        # Create a schedule that should match current time
        now = datetime.now()
        current_hour = now.hour

        # Create schedule that covers current hour
        start_hour = (current_hour - 1) % 24
        end_hour = (current_hour + 1) % 24

        # Handle overnight case by setting valid time range
        if end_hour <= start_hour:
            # Skip overnight test, use daytime hours
            start_hour = 9
            end_hour = 17

        data = ScheduleCreate(
            device_id=test_device.id,
            playlist_id=playlists[0].id,
            start_time=f"{start_hour:02d}:00:00",
            end_time=f"{end_hour:02d}:00:00",
            days_of_week=127,
            enabled=True,
            priority=0
        )
        service.create(data)

        # Mock datetime.now() to be within schedule
        with patch('app.services.schedule_service.datetime') as mock_dt:
            mock_dt.now.return_value = now
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs) if args else now

            result = service.get_active_schedule(test_device.id)

            # Only assert if current time is within schedule
            current_time = now.time()
            if time(start_hour, 0) <= current_time < time(end_hour, 0):
                assert result is not None
                assert result.playlist_id == playlists[0].id

    def test_get_active_schedule_disabled_schedule_ignored(self, db_session: Session, test_device):
        """测试禁用的调度被忽略"""
        playlists = self._setup_device_with_playlists(db_session, test_device)

        service = ScheduleService(db_session)
        data = ScheduleCreate(
            device_id=test_device.id,
            playlist_id=playlists[0].id,
            start_time="00:00:00",
            end_time="23:59:59",
            days_of_week=127,
            enabled=False,  # Disabled
            priority=0
        )
        service.create(data)

        result = service.get_active_schedule(test_device.id)
        assert result is None

    def test_get_active_schedule_priority_resolution(self, db_session: Session, test_device):
        """测试优先级解决：高优先级调度胜出"""
        playlists = self._setup_device_with_playlists(db_session, test_device, 2)

        service = ScheduleService(db_session)

        # Create lower priority schedule
        service.create(ScheduleCreate(
            device_id=test_device.id,
            playlist_id=playlists[0].id,
            start_time="00:00:00",
            end_time="23:59:59",
            days_of_week=127,
            enabled=True,
            priority=1
        ))

        # Create higher priority schedule
        service.create(ScheduleCreate(
            device_id=test_device.id,
            playlist_id=playlists[1].id,
            start_time="00:00:00",
            end_time="23:59:59",
            days_of_week=127,
            enabled=True,
            priority=10  # Higher priority
        ))

        result = service.get_active_schedule(test_device.id)
        assert result is not None
        assert result.playlist_id == playlists[1].id
        assert result.priority == 10

    def test_get_active_schedule_day_of_week_filtering(self, db_session: Session, test_device):
        """测试星期过滤：仅匹配当前星期"""
        playlists = self._setup_device_with_playlists(db_session, test_device)

        service = ScheduleService(db_session)

        # Get current weekday (0=Monday, 6=Sunday)
        now = datetime.now()
        current_weekday = now.weekday()
        other_day = (current_weekday + 1) % 7

        # Create schedule for different day
        service.create(ScheduleCreate(
            device_id=test_device.id,
            playlist_id=playlists[0].id,
            start_time="00:00:00",
            end_time="23:59:59",
            days_of_week=1 << other_day,  # Only on other day
            enabled=True,
            priority=0
        ))

        result = service.get_active_schedule(test_device.id)
        # Should return None since schedule is for a different day
        assert result is None

    def test_get_default_playlist_first_assignment(self, db_session: Session, test_device):
        """测试默认播放列表：返回最早分配的播放列表"""
        playlists = self._setup_device_with_playlists(db_session, test_device, 3)

        service = ScheduleService(db_session)
        result = service.get_default_playlist_id(test_device.id)

        # Should return first assigned playlist (lowest device_playlists.id)
        assert result == playlists[0].id


class TestConflictDetection:
    """调度冲突检测测试"""

    def _setup_device_with_playlists(
        self, db_session: Session, test_device, num_playlists: int = 2
    ):
        """辅助方法：为设备设置多个播放列表"""
        from app.models.playlist import Playlist, DevicePlaylist

        playlists = []
        for i in range(num_playlists):
            playlist = Playlist(name=f"Test Playlist {i}")
            db_session.add(playlist)
            db_session.flush()
            playlists.append(playlist)

            assignment = DevicePlaylist(
                device_id=test_device.id,
                playlist_id=playlist.id
            )
            db_session.add(assignment)

        db_session.commit()
        return playlists

    def test_no_conflict_different_days(self, db_session: Session, test_device):
        """测试不同星期无冲突"""
        playlists = self._setup_device_with_playlists(db_session, test_device)

        service = ScheduleService(db_session)

        # Monday schedule
        service.create(ScheduleCreate(
            device_id=test_device.id,
            playlist_id=playlists[0].id,
            start_time="09:00:00",
            end_time="17:00:00",
            days_of_week=DayOfWeek.MONDAY,
            enabled=True,
            priority=0
        ))

        # Check Tuesday schedule for conflicts
        conflicts = service.check_conflicts(
            device_id=test_device.id,
            start_time="09:00:00",
            end_time="17:00:00",
            days_of_week=DayOfWeek.TUESDAY,
            exclude_id=None
        )

        assert len(conflicts) == 0

    def test_conflict_same_time_same_day(self, db_session: Session, test_device):
        """测试相同时间和星期产生冲突"""
        playlists = self._setup_device_with_playlists(db_session, test_device)

        service = ScheduleService(db_session)

        # Create first schedule
        service.create(ScheduleCreate(
            device_id=test_device.id,
            playlist_id=playlists[0].id,
            start_time="09:00:00",
            end_time="17:00:00",
            days_of_week=127,
            enabled=True,
            priority=0
        ))

        # Check overlapping schedule
        conflicts = service.check_conflicts(
            device_id=test_device.id,
            start_time="10:00:00",
            end_time="16:00:00",
            days_of_week=127,
            exclude_id=None
        )

        assert len(conflicts) == 1
        assert conflicts[0].schedule_id is not None

    def test_no_conflict_disabled_schedule(self, db_session: Session, test_device):
        """测试禁用的调度不产生冲突"""
        playlists = self._setup_device_with_playlists(db_session, test_device)

        service = ScheduleService(db_session)

        # Create disabled schedule
        service.create(ScheduleCreate(
            device_id=test_device.id,
            playlist_id=playlists[0].id,
            start_time="09:00:00",
            end_time="17:00:00",
            days_of_week=127,
            enabled=False,  # Disabled
            priority=0
        ))

        # Check overlapping schedule
        conflicts = service.check_conflicts(
            device_id=test_device.id,
            start_time="10:00:00",
            end_time="16:00:00",
            days_of_week=127,
            exclude_id=None
        )

        assert len(conflicts) == 0

    def test_partial_time_overlap_creates_conflict(self, db_session: Session, test_device):
        """测试部分时间重叠产生冲突"""
        playlists = self._setup_device_with_playlists(db_session, test_device)

        service = ScheduleService(db_session)

        # Create 9-17 schedule
        service.create(ScheduleCreate(
            device_id=test_device.id,
            playlist_id=playlists[0].id,
            start_time="09:00:00",
            end_time="17:00:00",
            days_of_week=127,
            enabled=True,
            priority=0
        ))

        # Check 14-20 schedule (overlaps 14-17)
        conflicts = service.check_conflicts(
            device_id=test_device.id,
            start_time="14:00:00",
            end_time="20:00:00",
            days_of_week=127,
            exclude_id=None
        )

        assert len(conflicts) == 1

    def test_no_conflict_excluding_self(self, db_session: Session, test_device):
        """测试更新时排除自身不产生冲突"""
        playlists = self._setup_device_with_playlists(db_session, test_device)

        service = ScheduleService(db_session)

        # Create schedule
        schedule, _ = service.create(ScheduleCreate(
            device_id=test_device.id,
            playlist_id=playlists[0].id,
            start_time="09:00:00",
            end_time="17:00:00",
            days_of_week=127,
            enabled=True,
            priority=0
        ))

        # Check same schedule excluding itself
        conflicts = service.check_conflicts(
            device_id=test_device.id,
            start_time="09:00:00",
            end_time="17:00:00",
            days_of_week=127,
            exclude_id=schedule.id
        )

        assert len(conflicts) == 0
