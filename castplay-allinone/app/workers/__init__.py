"""
后台任务模块
"""
from app.workers.task_queue import TaskQueueManager

# 全局任务队列管理器实例
task_manager = TaskQueueManager(num_workers=3)

__all__ = ["task_manager"]
