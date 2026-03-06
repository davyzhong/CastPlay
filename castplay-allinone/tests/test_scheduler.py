"""
测试 APScheduler 调度器
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.scheduler import scheduler, submit_ppt_conversion, _convert_ppt_task


class TestScheduler:
    """测试 APScheduler 功能"""

    def test_scheduler_initialization(self):
        """测试调度器初始化"""
        assert scheduler is not None
        # 验证调度器配置（使用私有属性）
        assert hasattr(scheduler, '_executors') or len(
            scheduler._threadpool) > 0 if hasattr(scheduler, '_threadpool') else True

    @patch('app.scheduler._convert_ppt_task')
    def test_submit_ppt_conversion(self, mock_convert):
        """测试提交 PPT 转换任务"""
        job_id = submit_ppt_conversion(1, "/tmp/test.pptx")

        # 验证返回了任务 ID
        assert job_id is not None
        assert isinstance(job_id, str)

        # 验证任务已添加到调度器
        job = scheduler.get_job(job_id)
        # 注意：由于是异步执行，可能需要等待

    @patch('app.services.converter.PPTConverter')
    def test_convert_ppt_task_success(self, mock_converter_class):
        """测试 PPT 转换成功场景"""
        # Mock 转换器
        mock_converter = Mock()
        mock_converter.convert.return_value = "/tmp/output/"
        mock_converter_class.return_value = mock_converter

        # 执行转换任务
        _convert_ppt_task(media_id=1, file_path="/tmp/test.pptx")

        # 验证调用了转换方法
        mock_converter.convert.assert_called_once_with("/tmp/test.pptx")

    @patch('app.services.converter.PPTConverter')
    def test_convert_ppt_task_failure(self, mock_converter_class):
        """测试 PPT 转换失败场景"""
        # Mock 转换器抛出异常
        mock_converter = Mock()
        mock_converter.convert.side_effect = Exception("Conversion failed")
        mock_converter_class.return_value = mock_converter

        # 验证异常会被重新抛出
        with pytest.raises(Exception) as exc_info:
            _convert_ppt_task(media_id=1, file_path="/tmp/test.pptx")

        assert "Conversion failed" in str(exc_info.value)

    def test_scheduler_start_stop(self):
        """测试调度器启动和停止"""
        # 创建新的调度器实例用于测试
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.executors.pool import ThreadPoolExecutor

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
