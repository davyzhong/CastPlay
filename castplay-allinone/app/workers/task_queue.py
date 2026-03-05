"""
后台任务队列管理器
使用 Python threading 实现简单的后台任务队列
适用于 PPT 转换等耗时任务
"""
import queue
import threading
import uuid
from typing import Dict, Any, Optional
from loguru import logger

from app.config import settings


class TaskQueueManager:
    """
    后台任务队列管理器

    使用线程池处理后台任务，避免阻塞主线程
    """

    def __init__(self, num_workers: int = 3):
        """
        初始化任务队列管理器

        Args:
            num_workers: Worker 线程数量
        """
        self.task_queue = queue.Queue()
        self.num_workers = num_workers
        self.workers: list[threading.Thread] = []
        self.running = False
        self.task_status: Dict[str, Dict[str, Any]] = {}
        self._handlers: Dict[str, Any] = {}

    def start(self):
        """启动所有 Worker 线程"""
        if self.running:
            logger.warning("Task queue manager is already running")
            return

        self.running = True
        for i in range(self.num_workers):
            worker = threading.Thread(
                target=self._worker,
                name=f"TaskWorker-{i}",
                daemon=True
            )
            worker.start()
            self.workers.append(worker)

        logger.info(f"Started {self.num_workers} task workers")

    def stop(self):
        """停止所有 Worker 线程"""
        if not self.running:
            return

        logger.info("Stopping task workers...")
        self.running = False

        # 发送停止信号（None）
        for _ in range(self.num_workers):
            self.task_queue.put(None)

        # 等待所有 worker 结束
        for worker in self.workers:
            worker.join(timeout=5)

        self.workers.clear()
        logger.info("Task workers stopped")

    def register_handler(self, task_type: str, handler):
        """
        注册任务处理器

        Args:
            task_type: 任务类型
            handler: 处理函数，接收 task 参数
        """
        self._handlers[task_type] = handler
        logger.info(f"Registered handler for task type: {task_type}")

    def submit_task(self, task_type: str, task_data: Dict[str, Any]) -> str:
        """
        提交新任务

        Args:
            task_type: 任务类型
            task_data: 任务数据

        Returns:
            任务 ID
        """
        task_id = str(uuid.uuid4())
        task = {
            "task_id": task_id,
            "type": task_type,
            **task_data
        }
        self.task_queue.put(task)
        self.task_status[task_id] = {"status": "queued"}
        logger.info(f"Task {task_id} ({task_type}) queued")
        return task_id

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态

        Args:
            task_id: 任务 ID

        Returns:
            任务状态字典，不存在则返回 None
        """
        return self.task_status.get(task_id)

    def _worker(self):
        """Worker 线程的主循环"""
        thread_name = threading.current_thread().name
        logger.info(f"{thread_name} started")

        while self.running:
            try:
                # 从队列获取任务（带超时）
                task = self.task_queue.get(timeout=1)

                if task is None:  # 停止信号
                    break

                self._process_task(task)

            except queue.Empty:
                # 队列为空，继续等待
                continue
            except Exception as e:
                logger.error(f"{thread_name} error: {e}")

        logger.info(f"{thread_name} stopped")

    def _process_task(self, task: Dict[str, Any]):
        """
        处理单个任务

        Args:
            task: 任务字典
        """
        task_id = task.get("task_id")
        task_type = task.get("type")

        try:
            # 更新状态为处理中
            self.task_status[task_id] = {
                "status": "processing",
                "type": task_type,
                "started_at": self._now()
            }
            logger.info(f"Processing task {task_id} ({task_type})")

            # 获取并执行处理器
            handler = self._handlers.get(task_type)
            if not handler:
                raise ValueError(f"No handler for task type: {task_type}")

            handler(task)

            # 更新状态为完成
            self.task_status[task_id] = {
                "status": "completed",
                "type": task_type,
                "started_at": self.task_status[task_id]["started_at"],
                "completed_at": self._now()
            }
            logger.info(f"Task {task_id} completed")

        except Exception as e:
            # 更新状态为失败
            self.task_status[task_id] = {
                "status": "failed",
                "type": task_type,
                "error": str(e),
                "started_at": self.task_status[task_id].get("started_at"),
                "failed_at": self._now()
            }
            logger.error(f"Task {task_id} failed: {e}")
        finally:
            self.task_queue.task_done()

    def _now(self) -> str:
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.utcnow().isoformat()

    def get_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有任务状态

        Returns:
            所有任务状态的字典
        """
        return self.task_status.copy()

    def clear_completed_tasks(self):
        """清除已完成/失败的任务状态"""
        to_remove = [
            task_id for task_id, status in self.task_status.items()
            if status.get("status") in ["completed", "failed"]
        ]
        for task_id in to_remove:
            del self.task_status[task_id]
        logger.info(f"Cleared {len(to_remove)} completed/failed tasks")
