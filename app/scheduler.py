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


def submit_ppt_conversion(media_id: int, file_path: str, slide_duration: int = 5) -> str:
    """
    提交 PPT 转换任务

    Args:
        media_id: 媒体文件 ID
        file_path: PPT 文件路径
        slide_duration: 每张幻灯片的显示时长（秒），默认 5 秒

    Returns:
        任务 ID
    """
    logger.info(
        f"Scheduling PPT conversion: media_id={media_id}, file={file_path}, slide_duration={slide_duration}")

    job = scheduler.add_job(
        _convert_ppt_task,
        args=[media_id, file_path, slide_duration],
        max_instances=1,  # 同一任务只允许 1 个实例
        misfire_grace_time=60,  # 容忍 60 秒延迟
        replace_existing=True,  # 替换同名任务
        id=f"ppt_convert_{media_id}"
    )

    logger.info(f"Task scheduled with job_id: {job.id}")
    return job.id


def _convert_ppt_task(media_id: int, file_path: str, slide_duration: int = 5):
    """
    实际执行的 PPT 转换逻辑

    Args:
        media_id: 媒体文件 ID
        file_path: PPT 文件路径
        slide_duration: 每张幻灯片的显示时长（秒），默认 5 秒
    """
    from app.services.converter import PPTConverter
    from app.database import SessionLocal
    from app.models.media import MediaFile

    db = None
    try:
        logger.info(f"Starting PPT conversion: media_id={media_id}, slide_duration={slide_duration}")
        converter = PPTConverter()
        result = converter.convert(file_path, media_id, slide_duration)

        # 更新数据库中的媒体文件记录
        if result.get("success"):
            db = SessionLocal()
            media = db.query(MediaFile).filter(MediaFile.id == media_id).first()
            if media:
                media.converted_path = result.get("converted_path")
                media.thumbnail_path = result.get("thumbnail_path")
                media.duration = result.get("duration")
                media.status = "ready"
                db.commit()
                logger.info(f"Media record updated: media_id={media_id}")
        else:
            # 转换失败，更新状态
            db = SessionLocal()
            media = db.query(MediaFile).filter(MediaFile.id == media_id).first()
            if media:
                media.status = "failed"
                db.commit()
            logger.error(f"PPT conversion failed: {result.get('error')}")

        logger.info(f"PPT conversion completed: {result}")
    except Exception as e:
        logger.error(f"PPT conversion failed: {e}", exc_info=True)
        # 更新失败状态
        try:
            if db is None:
                db = SessionLocal()
            media = db.query(MediaFile).filter(MediaFile.id == media_id).first()
            if media:
                media.status = "failed"
                db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update media status: {db_error}")
    finally:
        if db:
            db.close()


def start():
    """启动调度器"""
    scheduler.start()
    logger.info("APScheduler started")


def stop():
    """停止调度器"""
    scheduler.shutdown(wait=True)
    logger.info("APScheduler stopped")
