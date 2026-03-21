"""
播放列表调度 API 单元测试

测试 app/api/schedules.py 中的调度 API 端点
使用 mock 隔离测试 API 层，不依赖实际数据库操作
"""
import pytest
from datetime import datetime, time
from unittest.mock import Mock, MagicMock, patch
from pydantic import ValidationError

from app.schemas.schedule import (
    ScheduleCreate,
    ScheduleUpdate,
    ScheduleResponse,
    ScheduleListResponse,
    ActiveScheduleResponse,
    ScheduleConflict,
)


class TestScheduleSchemas:
    """测试调度相关的 Pydantic schemas"""

    def test_schedule_create_valid(self):
        """测试有效的 ScheduleCreate"""
        schedule = ScheduleCreate(
            device_id=1,
            playlist_id=1,
            start_time="09:00:00",
            end_time="17:00:00",
            days_of_week=127,
            enabled=True,
            priority=0,
        )
        assert schedule.device_id == 1
        assert schedule.start_time == "09:00:00"

    def test_schedule_create_invalid_time_order(self):
        """测试无效的时间顺序"""
        with pytest.raises(ValidationError):
            ScheduleCreate(
                device_id=1,
                playlist_id=1,
                start_time="17:00:00",
                end_time="09:00:00",
                days_of_week=127,
            )

    def test_schedule_create_same_time(self):
        """测试相同时间（应该失败）"""
        with pytest.raises(ValidationError):
            ScheduleCreate(
                device_id=1,
                playlist_id=1,
                start_time="12:00:00",
                end_time="12:00:00",
                days_of_week=127,
            )

    def test_schedule_update_partial(self):
        """测试部分更新的 ScheduleUpdate"""
        update = ScheduleUpdate(priority=10)
        assert update.priority == 10
        assert update.start_time is None
        assert update.end_time is None

    def test_schedule_update_invalid_time(self):
        """测试更新时无效时间"""
        with pytest.raises(ValidationError):
            ScheduleUpdate(
                start_time="17:00:00",
                end_time="09:00:00",
            )

    def test_schedule_update_with_time(self):
        """测试更新时提供时间"""
        update = ScheduleUpdate(
            start_time="09:00:00",
            end_time="17:00:00",
        )
        assert update.start_time == "09:00:00"
        assert update.end_time == "17:00:00"

    def test_days_to_display_function(self):
        """测试 days_to_display 辅助函数"""
        from app.schemas.schedule import days_to_display

        # 全周
        assert set(days_to_display(127)) == {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}

        # 仅工作日
        assert set(days_to_display(31)) == {"Mon", "Tue", "Wed", "Thu", "Fri"}

        # 仅周末
        assert set(days_to_display(96)) == {"Sat", "Sun"}

        # 周一
        assert days_to_display(1) == ["Mon"]

        # 周三和周五
        assert set(days_to_display(20)) == {"Wed", "Fri"}


class TestScheduleResponseModels:
    """测试响应模型"""

    def test_schedule_response_model(self):
        """测试 ScheduleResponse 模型"""
        now = datetime.now()
        response = ScheduleResponse(
            id=1,
            device_id=1,
            playlist_id=1,
            playlist_name="Test Playlist",
            start_time="09:00:00",
            end_time="17:00:00",
            days_of_week=127,
            days_display=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            enabled=True,
            priority=0,
            conflicts=[],
            created_at=now,
            updated_at=now,
        )
        assert response.id == 1
        assert response.playlist_name == "Test Playlist"
        assert len(response.conflicts) == 0

    def test_schedule_response_with_conflicts(self):
        """测试带冲突的响应"""
        now = datetime.now()
        conflict = ScheduleConflict(
            schedule_id=2,
            playlist_name="Conflicting Playlist",
            overlap="09:00-12:00 on Mon,Tue",
        )
        response = ScheduleResponse(
            id=1,
            device_id=1,
            playlist_id=1,
            playlist_name="Test Playlist",
            start_time="09:00:00",
            end_time="17:00:00",
            days_of_week=127,
            days_display=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            enabled=True,
            priority=0,
            conflicts=[conflict],
            created_at=now,
            updated_at=now,
        )
        assert len(response.conflicts) == 1
        assert response.conflicts[0].schedule_id == 2

    def test_active_schedule_response_empty(self):
        """测试空的活跃调度响应"""
        response = ActiveScheduleResponse()
        assert response.active_playlist_id is None
        assert response.schedule_id is None
        assert response.schedule_name is None

    def test_active_schedule_response_with_data(self):
        """测试带数据的活跃调度响应"""
        response = ActiveScheduleResponse(
            active_playlist_id=5,
            schedule_id=10,
            schedule_name="Morning Playlist",
        )
        assert response.active_playlist_id == 5
        assert response.schedule_id == 10
        assert response.schedule_name == "Morning Playlist"

    def test_schedule_list_response(self):
        """测试调度列表响应"""
        now = datetime.now()
        schedule = ScheduleResponse(
            id=1,
            device_id=1,
            playlist_id=1,
            playlist_name="Test",
            start_time="09:00:00",
            end_time="17:00:00",
            days_of_week=127,
            days_display=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            enabled=True,
            priority=0,
            conflicts=[],
            created_at=now,
            updated_at=now,
        )
        response = ScheduleListResponse(
            schedules=[schedule],
            total=1,
        )
        assert len(response.schedules) == 1
        assert response.total == 1


class TestScheduleServiceIntegration:
    """测试调度服务与 API 层的集成（使用现有 conftest fixtures）"""

    def test_create_schedule_via_service(
        self,
        db_session,
        test_device,
        test_playlist,
    ):
        """测试通过服务创建调度"""
        from app.models.playlist import DevicePlaylist
        from app.services.schedule_service import ScheduleService
        from app.schemas.schedule import ScheduleCreate

        # 创建设备-播放列表关联
        assignment = DevicePlaylist(
            device_id=test_device.id,
            playlist_id=test_playlist.id,
        )
        db_session.add(assignment)
        db_session.commit()

        # 创建调度
        service = ScheduleService(db_session)
        data = ScheduleCreate(
            device_id=test_device.id,
            playlist_id=test_playlist.id,
            start_time="09:00:00",
            end_time="17:00:00",
            days_of_week=127,
            enabled=True,
            priority=0,
        )

        schedule, conflicts = service.create(data)

        assert schedule.id is not None
        assert schedule.device_id == test_device.id
        assert schedule.playlist_id == test_playlist.id
        assert schedule.start_time == time(9, 0, 0)
        assert schedule.end_time == time(17, 0, 0)
        assert schedule.enabled is True
        assert schedule.priority == 0

    def test_list_schedules_via_service(
        self,
        db_session,
        test_device,
        test_playlist,
    ):
        """测试通过服务获取调度列表"""
        from app.models.playlist import DevicePlaylist
        from app.services.schedule_service import ScheduleService
        from app.schemas.schedule import ScheduleCreate

        # 创建设备-播放列表关联
        assignment = DevicePlaylist(
            device_id=test_device.id,
            playlist_id=test_playlist.id,
        )
        db_session.add(assignment)
        db_session.commit()

        # 创建多个调度
        service = ScheduleService(db_session)
        data1 = ScheduleCreate(
            device_id=test_device.id,
            playlist_id=test_playlist.id,
            start_time="09:00:00",
            end_time="12:00:00",
            days_of_week=127,
            enabled=True,
            priority=0,
        )
        data2 = ScheduleCreate(
            device_id=test_device.id,
            playlist_id=test_playlist.id,
            start_time="13:00:00",
            end_time="17:00:00",
            days_of_week=127,
            enabled=True,
            priority=0,
        )

        service.create(data1)
        service.create(data2)

        # 获取列表
        schedules = service.get_by_device(test_device.id)

        assert len(schedules) == 2
        # 按开始时间排序
        assert schedules[0].start_time == time(9, 0, 0)
        assert schedules[1].start_time == time(13, 0, 0)

    def test_update_schedule_via_service(
        self,
        db_session,
        test_device,
        test_playlist,
    ):
        """测试通过服务更新调度"""
        from app.models.playlist import DevicePlaylist
        from app.services.schedule_service import ScheduleService
        from app.schemas.schedule import ScheduleCreate, ScheduleUpdate

        # 创建设备-播放列表关联
        assignment = DevicePlaylist(
            device_id=test_device.id,
            playlist_id=test_playlist.id,
        )
        db_session.add(assignment)
        db_session.commit()

        # 创建调度
        service = ScheduleService(db_session)
        data = ScheduleCreate(
            device_id=test_device.id,
            playlist_id=test_playlist.id,
            start_time="09:00:00",
            end_time="17:00:00",
            days_of_week=127,
            enabled=True,
            priority=0,
        )
        schedule, _ = service.create(data)

        # 更新调度
        update_data = ScheduleUpdate(
            priority=10,
            enabled=False,
        )
        updated, _ = service.update(schedule.id, update_data)

        assert updated.priority == 10
        assert updated.enabled is False
        assert updated.start_time == time(9, 0, 0)  # 未更新的字段保持不变

    def test_delete_schedule_via_service(
        self,
        db_session,
        test_device,
        test_playlist,
    ):
        """测试通过服务删除调度"""
        from app.models.playlist import DevicePlaylist
        from app.services.schedule_service import ScheduleService
        from app.schemas.schedule import ScheduleCreate

        # 创建设备-播放列表关联
        assignment = DevicePlaylist(
            device_id=test_device.id,
            playlist_id=test_playlist.id,
        )
        db_session.add(assignment)
        db_session.commit()

        # 创建调度
        service = ScheduleService(db_session)
        data = ScheduleCreate(
            device_id=test_device.id,
            playlist_id=test_playlist.id,
            start_time="09:00:00",
            end_time="17:00:00",
            days_of_week=127,
            enabled=True,
            priority=0,
        )
        schedule, _ = service.create(data)
        schedule_id = schedule.id

        # 删除调度
        result = service.delete(schedule_id)
        assert result is True

        # 验证已删除
        deleted = service.get_by_id(schedule_id)
        assert deleted is None

    def test_get_active_schedule_via_service(
        self,
        db_session,
        test_device,
        test_playlist,
    ):
        """测试通过服务获取活跃调度"""
        from app.models.playlist import DevicePlaylist
        from app.services.schedule_service import ScheduleService
        from app.schemas.schedule import ScheduleCreate
        from datetime import datetime

        # 创建设备-播放列表关联
        assignment = DevicePlaylist(
            device_id=test_device.id,
            playlist_id=test_playlist.id,
        )
        db_session.add(assignment)
        db_session.commit()

        # 创建全天调度
        service = ScheduleService(db_session)
        data = ScheduleCreate(
            device_id=test_device.id,
            playlist_id=test_playlist.id,
            start_time="00:00:00",
            end_time="23:59:59",
            days_of_week=127,
            enabled=True,
            priority=0,
        )
        schedule, _ = service.create(data)

        # 获取活跃调度
        now = datetime.now()
        current_time = now.time()
        current_weekday = now.weekday()

        # Mock 当前时间来测试
        with patch('app.services.schedule_service.datetime') as mock_dt:
            mock_dt.now.return_value = now
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs) if args else now

            active = service.get_active_schedule(test_device.id)

            assert active is not None
            assert active.id == schedule.id

    def test_check_conflicts_via_service(
        self,
        db_session,
        test_device,
        test_playlist,
    ):
        """测试冲突检测"""
        from app.models.playlist import DevicePlaylist, Playlist
        from app.services.schedule_service import ScheduleService
        from app.schemas.schedule import ScheduleCreate

        # 创建设备-播放列表关联
        assignment = DevicePlaylist(
            device_id=test_device.id,
            playlist_id=test_playlist.id,
        )
        db_session.add(assignment)

        # 创建第二个播放列表
        playlist2 = Playlist(name="Second Playlist")
        db_session.add(playlist2)
        db_session.flush()

        assignment2 = DevicePlaylist(
            device_id=test_device.id,
            playlist_id=playlist2.id,
        )
        db_session.add(assignment2)
        db_session.commit()

        # 创建第一个调度
        service = ScheduleService(db_session)
        data1 = ScheduleCreate(
            device_id=test_device.id,
            playlist_id=test_playlist.id,
            start_time="09:00:00",
            end_time="17:00:00",
            days_of_week=127,
            enabled=True,
            priority=0,
        )
        service.create(data1)

        # 检查重叠时间
        conflicts = service.check_conflicts(
            device_id=test_device.id,
            start_time="10:00:00",
            end_time="15:00:00",
            days_of_week=127,
        )

        assert len(conflicts) == 1
        assert conflicts[0].playlist_name == "Test Playlist"

    def test_playlist_not_assigned_error(
        self,
        db_session,
        test_device,
        test_playlist,
    ):
        """测试播放列表未分配错误"""
        from app.services.schedule_service import ScheduleService
        from app.schemas.schedule import ScheduleCreate

        # 不创建 DevicePlaylist 关联

        service = ScheduleService(db_session)
        data = ScheduleCreate(
            device_id=test_device.id,
            playlist_id=test_playlist.id,
            start_time="09:00:00",
            end_time="17:00:00",
            days_of_week=127,
            enabled=True,
            priority=0,
        )

        with pytest.raises(ValueError, match="playlist not assigned"):
            service.create(data)


class TestScheduleHelperFunctions:
    """测试调度辅助函数"""

    def test_days_to_display_weekdays(self):
        """测试工作日显示"""
        from app.schemas.schedule import days_to_display

        # Mon-Fri = 1+2+4+8+16 = 31
        result = days_to_display(31)
        assert set(result) == {"Mon", "Tue", "Wed", "Thu", "Fri"}
        assert len(result) == 5

    def test_days_to_display_weekends(self):
        """测试周末显示"""
        from app.schemas.schedule import days_to_display

        # Sat+Sun = 32+64 = 96
        result = days_to_display(96)
        assert set(result) == {"Sat", "Sun"}

    def test_days_to_display_single_day(self):
        """测试单天显示"""
        from app.schemas.schedule import days_to_display

        # Monday only = 1
        result = days_to_display(1)
        assert result == ["Mon"]

        # Friday only = 16
        result = days_to_display(16)
        assert result == ["Fri"]

    def test_days_to_display_all(self):
        """测试全周显示"""
        from app.schemas.schedule import days_to_display

        # All days = 127
        result = days_to_display(127)
        assert set(result) == {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}
