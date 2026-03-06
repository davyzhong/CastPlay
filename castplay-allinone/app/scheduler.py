"""
后台任务调度器 - 使用 APScheduler 替代自研 TaskQueue

适用于小规模场景的轻量级任务调度
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from app.config import settings
from app.utils.logger import logger


# 创建调度器（3 个 Worker 线程）
scheduler = BackgroundScheduler(
    executors={'default': ThreadPoolExecutor(settings.NUM_WORKERS)},
    timezone='Asia/Shanghai'
)


def submit_ppt_conversion(media_id: int, file_path: str) -> str:
    """
    提交 PPT 转换任务

    Args:
        media_id: 媒体文件 ID
        file_path: PPT 文件路径

    Returns:
        任务 ID
    """
    logger.info(
        f"Scheduling PPT conversion: media_id={media_id}, file={file_path}")

    job = scheduler.add_job(
        _convert_ppt_task,
        args=[media_id, file_path],
        max_instances=1,  # 同一任务只允许 1 个实例
        misfire_grace_time=60,  # 容忍 60 秒延迟
        replace_existing=True,  # 替换同名任务
        id=f"ppt_convert_{media_id}"
    )

    logger.info(f"Task scheduled with job_id: {job.id}")
    return job.id


def _convert_ppt_task(media_id: int, file_path: str):
    """
    实际执行的 PPT 转换逻辑

    Args:
        media_id: 媒体文件 ID
        file_path: PPT 文件路径
    """
    from app.services.converter import PPTConverter

    try:
        logger.info(f"Starting PPT conversion: media_id={media_id}")
        converter = PPTConverter()
        result = converter.convert(file_path)
        logger.info(f"PPT conversion completed: {result}")
    except Exception as e:
        logger.error(f"PPT conversion failed: {e}", exc_info=True)
        raise


def start():
    """启动调度器"""
    scheduler.start()
    logger.info("APScheduler started")


def stop():
    """停止调度器"""
    scheduler.shutdown(wait=True)
    logger.info("APScheduler stopped")
