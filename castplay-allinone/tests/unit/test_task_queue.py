"""
任务队列模块单元测试

测试 TaskQueueManager 的任务提交、执行和状态管理
"""
import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock


class TestTaskQueueManagerInit:
    """测试任务队列管理器初始化"""

    def test_init_default_workers(self):
        """测试默认工作线程数"""
        from app.workers.task_queue import TaskQueueManager
        manager = TaskQueueManager()
        assert manager.num_workers == 3
        assert manager.running is False
        assert len(manager.workers) == 0

    def test_init_custom_workers(self):
        """测试自定义工作线程数"""
        from app.workers.task_queue import TaskQueueManager
        manager = TaskQueueManager(num_workers=5)
        assert manager.num_workers == 5

    def test_init_empty_task_status(self):
        """测试初始化时任务状态为空"""
        from app.workers.task_queue import TaskQueueManager
        manager = TaskQueueManager()
        assert manager.task_status == {}

    def test_init_empty_handlers(self):
        """测试初始化时处理器为空"""
        from app.workers.task_queue import TaskQueueManager
        manager = TaskQueueManager()
        assert manager._handlers == {}


class TestTaskQueueManagerStartStop:
    """测试启动和停止"""

    @pytest.fixture
    def manager(self):
        """创建管理器实例"""
        from app.workers.task_queue import TaskQueueManager
        return TaskQueueManager(num_workers=2)

    def test_start_creates_workers(self, manager):
        """测试启动创建工作线程"""
        manager.start()

        assert manager.running is True
        assert len(manager.workers) == 2
        assert all(w.is_alive() for w in manager.workers)

        manager.stop()

    def test_start_idempotent(self, manager):
        """测试重复启动是幂等的"""
        manager.start()
        first_workers = len(manager.workers)

        manager.start()  # 再次启动
        assert len(manager.workers) == first_workers

        manager.stop()

    def test_stop_terminates_workers(self, manager):
        """测试停止终止工作线程"""
        manager.start()
        manager.stop()

        assert manager.running is False
        assert len(manager.workers) == 0

    def test_stop_when_not_running(self, manager):
        """测试未运行时停止不抛出异常"""
        # 没有启动就停止
        manager.stop()  # 应该不抛出异常

    def test_graceful_shutdown(self, manager):
        """测试优雅关闭"""
        results = []

        def slow_handler(task):
            time.sleep(0.1)
            results.append(task["task_id"])

        manager.register_handler("slow", slow_handler)
        manager.start()

        task_id = manager.submit_task("slow", {"data": "test"})

        # 等待任务完成
        time.sleep(0.3)

        manager.stop()

        assert task_id in results


class TestRegisterHandler:
    """测试处理器注册"""

    @pytest.fixture
    def manager(self):
        """创建管理器实例"""
        from app.workers.task_queue import TaskQueueManager
        return TaskQueueManager()

    def test_register_handler(self, manager):
        """测试注册处理器"""
        handler = Mock()
        manager.register_handler("test_type", handler)

        assert "test_type" in manager._handlers
        assert manager._handlers["test_type"] == handler

    def test_register_multiple_handlers(self, manager):
        """测试注册多个处理器"""
        handler1 = Mock()
        handler2 = Mock()

        manager.register_handler("type1", handler1)
        manager.register_handler("type2", handler2)

        assert len(manager._handlers) == 2
        assert manager._handlers["type1"] == handler1
        assert manager._handlers["type2"] == handler2

    def test_override_handler(self, manager):
        """测试覆盖已注册的处理器"""
        handler1 = Mock()
        handler2 = Mock()

        manager.register_handler("test", handler1)
        manager.register_handler("test", handler2)

        assert manager._handlers["test"] == handler2


class TestSubmitTask:
    """测试任务提交"""

    @pytest.fixture
    def manager(self):
        """创建管理器实例"""
        from app.workers.task_queue import TaskQueueManager
        return TaskQueueManager()

    def test_submit_task_returns_task_id(self, manager):
        """测试提交任务返回任务 ID"""
        task_id = manager.submit_task("test_type", {"data": "test"})

        assert task_id is not None
        assert isinstance(task_id, str)
        assert len(task_id) == 36  # UUID 格式

    def test_submit_task_creates_queued_status(self, manager):
        """测试提交任务创建排队状态"""
        task_id = manager.submit_task("test_type", {"data": "test"})

        status = manager.get_task_status(task_id)
        assert status is not None
        assert status["status"] == "queued"

    def test_submit_multiple_tasks(self, manager):
        """测试提交多个任务"""
        task_ids = []
        for i in range(5):
            task_id = manager.submit_task("test", {"index": i})
            task_ids.append(task_id)

        assert len(task_ids) == 5
        assert len(set(task_ids)) == 5  # 所有 ID 应该唯一


class TestTaskExecution:
    """测试任务执行"""

    @pytest.fixture
    def manager(self):
        """创建管理器实例"""
        from app.workers.task_queue import TaskQueueManager
        manager = TaskQueueManager(num_workers=2)
        yield manager
        if manager.running:
            manager.stop()

    def test_task_execution_success(self, manager):
        """测试任务执行成功"""
        executed = []

        def handler(task):
            executed.append(task["data"])

        manager.register_handler("test", handler)
        manager.start()

        manager.submit_task("test", {"data": "hello"})
        time.sleep(0.3)  # 等待执行

        assert "hello" in executed

    def test_task_status_updates_to_processing(self, manager):
        """测试任务状态更新为处理中"""
        processing_times = []

        def handler(task):
            processing_times.append(time.time())
            time.sleep(0.1)

        manager.register_handler("test", handler)
        manager.start()

        task_id = manager.submit_task("test", {"data": "test"})
        time.sleep(0.05)  # 等待开始处理

        status = manager.get_task_status(task_id)
        assert status["status"] in ["processing", "completed"]

    def test_task_status_updates_to_completed(self, manager):
        """测试任务状态更新为完成"""
        def handler(task):
            pass

        manager.register_handler("test", handler)
        manager.start()

        task_id = manager.submit_task("test", {"data": "test"})
        time.sleep(0.3)  # 等待完成

        status = manager.get_task_status(task_id)
        assert status["status"] == "completed"
        assert "completed_at" in status

    def test_task_execution_failure(self, manager):
        """测试任务执行失败"""
        def failing_handler(task):
            raise ValueError("Test error")

        manager.register_handler("test", failing_handler)
        manager.start()

        task_id = manager.submit_task("test", {"data": "test"})
        time.sleep(0.3)  # 等待执行

        status = manager.get_task_status(task_id)
        assert status["status"] == "failed"
        assert "Test error" in status["error"]

    def test_no_handler_error(self, manager):
        """测试没有处理器时的错误"""
        manager.start()

        task_id = manager.submit_task("unknown_type", {"data": "test"})
        time.sleep(0.3)

        status = manager.get_task_status(task_id)
        assert status["status"] == "failed"
        assert "No handler" in status["error"]


class TestTaskStatus:
    """测试任务状态"""

    @pytest.fixture
    def manager(self):
        """创建管理器实例"""
        from app.workers.task_queue import TaskQueueManager
        return TaskQueueManager()

    def test_get_task_status_nonexistent(self, manager):
        """测试获取不存在的任务状态"""
        status = manager.get_task_status("nonexistent-id")
        assert status is None

    def test_get_all_tasks(self, manager):
        """测试获取所有任务"""
        manager.submit_task("type1", {"data": "1"})
        manager.submit_task("type2", {"data": "2"})

        all_tasks = manager.get_all_tasks()
        assert len(all_tasks) == 2

    def test_clear_completed_tasks(self, manager):
        """测试清除已完成任务"""
        from app.workers.task_queue import TaskQueueManager

        manager = TaskQueueManager(num_workers=1)
        manager.register_handler("test", lambda t: None)
        manager.start()

        task_id = manager.submit_task("test", {"data": "test"})
        time.sleep(0.3)

        manager.clear_completed_tasks()

        # 已完成的任务应该被清除
        status = manager.get_task_status(task_id)
        assert status is None

        manager.stop()


class TestConcurrency:
    """测试并发"""

    def test_concurrent_task_execution(self):
        """测试并发任务执行"""
        from app.workers.task_queue import TaskQueueManager

        manager = TaskQueueManager(num_workers=3)
        execution_order = []
        lock = threading.Lock()

        def handler(task):
            with lock:
                execution_order.append(task["index"])
            time.sleep(0.1)

        manager.register_handler("test", handler)
        manager.start()

        for i in range(5):
            manager.submit_task("test", {"index": i})

        time.sleep(0.5)

        # 所有任务应该被执行
        assert len(execution_order) == 5

        manager.stop()

    def test_queue_order_preserved(self):
        """测试队列顺序保持"""
        from app.workers.task_queue import TaskQueueManager

        manager = TaskQueueManager(num_workers=1)  # 单线程保证顺序
        execution_order = []

        def handler(task):
            execution_order.append(task["order"])

        manager.register_handler("test", handler)
        manager.start()

        for i in range(5):
            manager.submit_task("test", {"order": i})

        time.sleep(0.5)

        # 队列顺序应该保持
        assert execution_order == [0, 1, 2, 3, 4]

        manager.stop()


class TestWorkerLifecycle:
    """测试工作线程生命周期"""

    def test_worker_daemon_threads(self):
        """测试工作线程是守护线程"""
        from app.workers.task_queue import TaskQueueManager

        manager = TaskQueueManager()
        manager.start()

        for worker in manager.workers:
            assert worker.daemon is True

        manager.stop()

    def test_worker_names(self):
        """测试工作线程命名"""
        from app.workers.task_queue import TaskQueueManager

        manager = TaskQueueManager(num_workers=3)
        manager.start()

        for i, worker in enumerate(manager.workers):
            assert f"TaskWorker-{i}" in worker.name

        manager.stop()


class TestHelperMethods:
    """测试辅助方法"""

    @pytest.fixture
    def manager(self):
        """创建管理器实例"""
        from app.workers.task_queue import TaskQueueManager
        return TaskQueueManager()

    def test_now_returns_iso_format(self, manager):
        """测试 _now 返回 ISO 格式时间"""
        from datetime import datetime

        timestamp = manager._now()

        # 应该可以解析为 datetime
        parsed = datetime.fromisoformat(timestamp)
        assert isinstance(parsed, datetime)

    def test_get_all_tasks_returns_copy(self, manager):
        """测试 get_all_tasks 返回副本"""
        manager.submit_task("test", {"data": "test"})

        all_tasks = manager.get_all_tasks()
        all_tasks["new_key"] = "new_value"

        # 原始数据不应被修改
        assert "new_key" not in manager.task_status


class TestIntegration:
    """集成测试"""

    def test_full_task_lifecycle(self):
        """测试完整任务生命周期"""
        from app.workers.task_queue import TaskQueueManager

        results = []

        def handler(task):
            results.append({
                "task_id": task["task_id"],
                "processed": True,
                "data": task.get("data")
            })

        manager = TaskQueueManager(num_workers=1)
        manager.register_handler("process", handler)
        manager.start()

        # 提交任务
        task_id = manager.submit_task("process", {"data": "test_data"})

        # 等待处理
        time.sleep(0.3)

        # 检查状态
        status = manager.get_task_status(task_id)
        assert status["status"] == "completed"

        # 检查结果
        assert len(results) == 1
        assert results[0]["task_id"] == task_id
        assert results[0]["processed"] is True
        assert results[0]["data"] == "test_data"

        manager.stop()
