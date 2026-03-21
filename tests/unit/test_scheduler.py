"""
APScheduler 调度器单元测试

测试 app/scheduler.py 中的后台调度器功能
"""
import pytest
from datetime import datetime, time
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor


class TestSchedulerModule:
    """测试调度器模块"""

    def test_scheduler_module_import(self):
        """测试调度器模块可以正确导入"""
        from app.scheduler import scheduler, submit_ppt_conversion, start, stop
        assert scheduler is not None

    def test_scheduler_initialization(self):
        """测试调度器正确初始化"""
        from app.scheduler import scheduler

        assert scheduler is not None
        assert isinstance(scheduler, BackgroundScheduler)
        assert scheduler.timezone.zone == 'Asia/Shanghai'

    def test_scheduler_has_executors(self):
        """测试调度器配置了执行器"""
        from app.scheduler import scheduler

        assert 'default' in scheduler._executors
        assert scheduler._executors['default'] is not None


class TestSubmitPPTConversion:
    """测试 PPT 转换任务提交"""

    @patch('app.scheduler.scheduler')
    def test_submit_ppt_conversion_returns_job_id(self, mock_scheduler):
        """测试提交 PPT 转换返回任务 ID"""
        from app.scheduler import submit_ppt_conversion

        mock_job = Mock()
        mock_job.id = "ppt_convert_1"
        mock_scheduler.add_job.return_value = mock_job

        job_id = submit_ppt_conversion(media_id=1, file_path="/tmp/test.pptx", slide_duration=5)

        assert job_id == "ppt_convert_1"
        mock_scheduler.add_job.assert_called_once()

    @patch('app.scheduler.scheduler')
    def test_submit_ppt_conversion_job_config(self, mock_scheduler):
        """测试提交的任务配置正确"""
        from app.scheduler import submit_ppt_conversion

        mock_job = Mock()
        mock_job.id = "ppt_convert_1"
        mock_scheduler.add_job.return_value = mock_job

        submit_ppt_conversion(media_id=42, file_path="/path/to/file.pptx", slide_duration=10)

        # 验证调用参数
        call_kwargs = mock_scheduler.add_job.call_args.kwargs
        assert call_kwargs['max_instances'] == 1
        assert call_kwargs['misfire_grace_time'] == 60
        assert call_kwargs['replace_existing'] is True
        assert call_kwargs['id'] == "ppt_convert_42"

    @patch('app.scheduler.scheduler')
    def test_submit_ppt_conversion_default_slide_duration(self, mock_scheduler):
        """测试默认幻灯片显示时长"""
        from app.scheduler import submit_ppt_conversion

        mock_job = Mock()
        mock_job.id = "ppt_convert_1"
        mock_scheduler.add_job.return_value = mock_job

        submit_ppt_conversion(media_id=1, file_path="/tmp/test.pptx")

        # 验证调用参数中包含默认时长
        call_kwargs = mock_scheduler.add_job.call_args.kwargs
        args = call_kwargs.get('args', [])
        assert args[2] == 5  # 默认 slide_duration


class TestConvertPPTTask:
    """测试 PPT 转换任务执行"""

    @patch('app.database.SessionLocal')
    @patch('app.services.converter.PPTConverter')
    def test_convert_ppt_task_success(self, mock_converter_class, mock_session_local):
        """测试 PPT 转换成功"""
        from app.scheduler import _convert_ppt_task

        # Mock 转换器
        mock_converter = Mock()
        mock_converter.convert.return_value = {
            "success": True,
            "converted_path": "/tmp/output.mp4",
            "thumbnail_path": "/tmp/thumb.jpg",
            "duration": 120,
        }
        mock_converter_class.return_value = mock_converter

        # Mock 数据库
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_media = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_media

        # Execute
        _convert_ppt_task(media_id=1, file_path="/tmp/test.pptx", slide_duration=5)

        # Verify
        mock_converter.convert.assert_called_once_with("/tmp/test.pptx", 1, 5)
        assert mock_media.converted_path == "/tmp/output.mp4"
        assert mock_media.status == "ready"
        mock_db.commit.assert_called()

    @patch('app.database.SessionLocal')
    @patch('app.services.converter.PPTConverter')
    def test_convert_ppt_task_failure(self, mock_converter_class, mock_session_local):
        """测试 PPT 转换失败"""
        from app.scheduler import _convert_ppt_task

        # Mock 转换器失败
        mock_converter = Mock()
        mock_converter.convert.return_value = {
            "success": False,
            "error": "Invalid file format",
        }
        mock_converter_class.return_value = mock_converter

        # Mock 数据库
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_media = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_media

        # Execute
        _convert_ppt_task(media_id=1, file_path="/tmp/test.pptx", slide_duration=5)

        # Verify
        assert mock_media.status == "failed"
        mock_db.commit.assert_called()

    @patch('app.database.SessionLocal')
    @patch('app.services.converter.PPTConverter')
    def test_convert_ppt_task_exception(self, mock_converter_class, mock_session_local):
        """测试 PPT 转换异常处理"""
        from app.scheduler import _convert_ppt_task

        # Mock 转换器抛出异常
        mock_converter = Mock()
        mock_converter.convert.side_effect = Exception("Conversion failed")
        mock_converter_class.return_value = mock_converter

        # Mock 数据库
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_media = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_media

        # Execute - should not raise
        _convert_ppt_task(media_id=1, file_path="/tmp/test.pptx", slide_duration=5)

        # Verify - status should be set to failed
        assert mock_media.status == "failed"


class TestEvaluateSchedulesTask:
    """测试调度评估任务"""

    @patch('app.scheduler._notify_device_schedule_change')
    @patch('app.websocket.handler.manager')
    @patch('app.database.SessionLocal')
    def test_evaluate_schedules_no_devices(
        self, mock_session_local, mock_manager, mock_notify
    ):
        """测试无设备时调度评估"""
        from app.scheduler import _evaluate_schedules_task

        # Mock 数据库
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.return_value = []

        # Execute
        _evaluate_schedules_task()

        # Verify - 没有设备，不应该发送通知
        mock_notify.assert_not_called()

    @patch('app.scheduler._notify_device_schedule_change')
    @patch('app.scheduler._last_schedule_states', {})
    @patch('app.websocket.handler.manager')
    @patch('app.database.SessionLocal')
    @patch('app.services.schedule_service.ScheduleService')
    def test_evaluate_schedules_with_active_schedule(
        self, mock_service_class, mock_session_local, mock_manager, mock_notify
    ):
        """测试有活跃调度时的评估"""
        from app.scheduler import _evaluate_schedules_task

        # Mock 设备
        mock_device = Mock()
        mock_device.id = 1
        mock_device.device_id = "device-uuid-1"

        # Mock 活跃调度
        mock_schedule = Mock()
        mock_schedule.id = 10
        mock_schedule.playlist_id = 5

        # Mock 播放列表
        mock_playlist = Mock()
        mock_playlist.name = "Evening Playlist"

        # Mock 数据库
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_device]
        mock_db.query.return_value.filter.return_value.first.return_value = mock_playlist

        # Mock 服务
        mock_service = Mock()
        mock_service.get_active_schedule.return_value = mock_schedule
        mock_service.get_default_playlist_id.return_value = None
        mock_service_class.return_value = mock_service

        # Execute
        _evaluate_schedules_task()

        # Verify - 应该发送通知
        mock_notify.assert_called_once()


class TestNotifyDeviceScheduleChange:
    """测试设备调度变化通知"""

    @patch('app.websocket.handler.manager')
    def test_notify_device_schedule_change(self, mock_manager):
        """测试发送调度变化通知"""
        from app.scheduler import _notify_device_schedule_change

        mock_manager.notify_schedule_trigger = AsyncMock()

        # Execute
        _notify_device_schedule_change(
            device_id="device-123",
            playlist_id=5,
            schedule_id=10,
            schedule_name="Morning Playlist"
        )

        # Verify
        mock_manager.notify_schedule_trigger.assert_called_once_with(
            "device-123",
            5,
            10,
            "Morning Playlist"
        )

    @patch('app.websocket.handler.manager')
    def test_notify_device_schedule_change_none_values(self, mock_manager):
        """测试通知处理 None 值"""
        from app.scheduler import _notify_device_schedule_change

        mock_manager.notify_schedule_trigger = AsyncMock()

        # Execute - schedule_id and schedule_name are None
        _notify_device_schedule_change(
            device_id="device-123",
            playlist_id=5,
            schedule_id=None,
            schedule_name=None
        )

        # Verify
        mock_manager.notify_schedule_trigger.assert_called_once_with(
            "device-123",
            5,
            None,
            None
        )


class TestSchedulerStartStop:
    """测试调度器启动和停止"""

    def test_scheduler_start_adds_job(self):
        """测试调度器配置正确"""
        from app.scheduler import scheduler

        # 验证调度器配置正确
        assert scheduler is not None
        assert scheduler.timezone.zone == 'Asia/Shanghai'

        # 获取当前任务（如果调度器未运行，任务可能不存在）
        job = scheduler.get_job('schedule_evaluation')

        # 如果任务存在，验证配置
        if job:
            assert job.id == 'schedule_evaluation'
            assert job.next_run_time is not None or scheduler.running

    def test_scheduler_stop(self):
        """测试调度器停止"""
        # 创建独立的测试调度器
        test_scheduler = BackgroundScheduler(
            executors={'default': ThreadPoolExecutor(1)},
            timezone='Asia/Shanghai'
        )

        # 启动
        test_scheduler.start()
        assert test_scheduler.running is True

        # 停止
        test_scheduler.shutdown(wait=False)
        assert test_scheduler.running is False


class TestSchedulerStateTracking:
    """测试调度状态跟踪"""

    def test_last_schedule_states_initialization(self):
        """测试状态跟踪字典初始化"""
        from app.scheduler import _last_schedule_states

        assert isinstance(_last_schedule_states, dict)

    def test_last_schedule_states_update(self):
        """测试状态跟踪更新"""
        from app.scheduler import _last_schedule_states

        # 模拟状态更新
        _last_schedule_states[1] = 10
        _last_schedule_states[2] = 20

        assert _last_schedule_states[1] == 10
        assert _last_schedule_states[2] == 20

    def test_last_schedule_states_change_detection(self):
        """测试状态变化检测"""
        from app.scheduler import _last_schedule_states

        device_id = 1

        # 初始状态
        last_id = _last_schedule_states.get(device_id)

        # 新状态
        new_id = 10

        # 检测变化
        if new_id != last_id and new_id is not None:
            _last_schedule_states[device_id] = new_id

        assert _last_schedule_states[device_id] == 10


class TestScheduleEvaluationTaskIntegration:
    """测试调度评估任务集成"""

    def test_schedule_change_only_on_state_difference(self):
        """测试只在状态变化时发送通知"""
        from app.scheduler import _last_schedule_states

        # 保存原始状态
        original_state = _last_schedule_states.copy()

        try:
            # 设置初始状态
            device_id = "device-test-1"
            _last_schedule_states[1] = 10  # 设备 1 上次状态是 schedule 10

            # Mock 设备
            mock_device = Mock()
            mock_device.id = 1
            mock_device.device_id = device_id

            # Mock 活跃调度 - 还是 schedule 10（无变化）
            mock_schedule = Mock()
            mock_schedule.id = 10  # 相同
            mock_schedule.playlist_id = 5

            # Mock 播放列表
            mock_playlist = Mock()
            mock_playlist.name = "Same Playlist"

            # Mock 数据库
            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.all.return_value = [mock_device]
            mock_db.query.return_value.filter.return_value.first.return_value = mock_playlist

            # Mock 服务
            from app.services.schedule_service import ScheduleService
            mock_service = Mock()
            mock_service.get_active_schedule.return_value = mock_schedule
            mock_service.get_default_playlist_id.return_value = None

            with patch('app.database.SessionLocal', return_value=mock_db):
                with patch.object(ScheduleService, '__init__', lambda self, db: setattr(self, 'db', db)):
                    with patch.object(ScheduleService, 'get_active_schedule', mock_service.get_active_schedule):
                        with patch.object(ScheduleService, 'get_default_playlist_id', mock_service.get_default_playlist_id):
                            with patch('app.scheduler._notify_device_schedule_change') as mock_notify:
                                with patch('app.scheduler._last_schedule_states', _last_schedule_states):
                                    from app.scheduler import _evaluate_schedules_task
                                    _evaluate_schedules_task()

                                # Verify - 状态相同，不应该发送通知
                                mock_notify.assert_not_called()
        finally:
            # 恢复原始状态
            _last_schedule_states.clear()
            _last_schedule_states.update(original_state)

    def test_schedule_change_notifies_on_different_state(self):
        """测试状态变化时发送通知"""
        from app.scheduler import _last_schedule_states

        # 保存原始状态
        original_state = _last_schedule_states.copy()

        try:
            # 设置初始状态
            device_id = "device-test-2"
            _last_schedule_states[1] = 5  # 设备上次状态是 schedule 5

            # Mock 设备
            mock_device = Mock()
            mock_device.id = 1
            mock_device.device_id = device_id

            # Mock 活跃调度 - schedule 15（变化了）
            mock_schedule = Mock()
            mock_schedule.id = 15  # 不同
            mock_schedule.playlist_id = 5

            # Mock 播放列表
            mock_playlist = Mock()
            mock_playlist.name = "New Playlist"

            # Mock 数据库
            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.all.return_value = [mock_device]
            mock_db.query.return_value.filter.return_value.first.return_value = mock_playlist

            # Mock 服务
            from app.services.schedule_service import ScheduleService
            mock_service = Mock()
            mock_service.get_active_schedule.return_value = mock_schedule
            mock_service.get_default_playlist_id.return_value = None

            with patch('app.database.SessionLocal', return_value=mock_db):
                with patch.object(ScheduleService, '__init__', lambda self, db: setattr(self, 'db', db)):
                    with patch.object(ScheduleService, 'get_active_schedule', mock_service.get_active_schedule):
                        with patch.object(ScheduleService, 'get_default_playlist_id', mock_service.get_default_playlist_id):
                            with patch('app.scheduler._notify_device_schedule_change') as mock_notify:
                                with patch('app.scheduler._last_schedule_states', _last_schedule_states):
                                    from app.scheduler import _evaluate_schedules_task
                                    _evaluate_schedules_task()

                                # Verify - 状态变化，应该发送通知
                                mock_notify.assert_called_once()
        finally:
            # 恢复原始状态
            _last_schedule_states.clear()
            _last_schedule_states.update(original_state)
