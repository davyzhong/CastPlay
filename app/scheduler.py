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


# 调度评估状态跟踪（避免重复通知）
_last_schedule_states: dict[int, int] = {}  # device_id -> active_schedule_id


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


def _evaluate_schedules_task():
    """
    调度评估任务：检查所有设备的调度规则，触发播放列表切换

    每分钟执行一次：
    1. 遍历所有在线设备
    2. 评估每个设备的活跃调度
    3. 如果活跃调度变化，通过 WebSocket 通知设备
    """
    from app.database import SessionLocal
    from app.models.device import Device
    from app.services.schedule_service import ScheduleService

    db = None
    try:
        db = SessionLocal()
        service = ScheduleService(db)

        # 获取所有设备
        devices = db.query(Device).filter(Device.status == "online").all()

        for device in devices:
            try:
                # 获取当前激活的调度
                active_schedule = service.get_active_schedule(device.id)

                # 确定当前应该播放的播放列表
                active_playlist_id = None
                active_schedule_id = None
                schedule_name = None

                if active_schedule:
                    active_playlist_id = active_schedule.playlist_id
                    active_schedule_id = active_schedule.id
                    # 获取播放列表名称
                    from app.models.playlist import Playlist
                    playlist = db.query(Playlist).filter(
                        Playlist.id == active_playlist_id
                    ).first()
                    schedule_name = playlist.name if playlist else None
                else:
                    # 没有匹配的调度，使用默认播放列表
                    active_playlist_id = service.get_default_playlist_id(device.id)

                # 检查是否需要通知（状态变化）
                last_schedule_id = _last_schedule_states.get(device.id)
                if active_schedule_id != last_schedule_id and active_playlist_id:
                    # 状态变化，需要通知
                    _notify_device_schedule_change(
                        device.device_id,
                        active_playlist_id,
                        active_schedule_id,
                        schedule_name
                    )
                    _last_schedule_states[device.id] = active_schedule_id

                    logger.info(
                        f"Schedule change for device {device.device_id}: "
                        f"schedule_id={active_schedule_id}, playlist_id={active_playlist_id}"
                    )

            except Exception as device_error:
                logger.error(
                    f"Error evaluating schedule for device {device.id}: {device_error}"
                )
                continue

    except Exception as e:
        logger.error(f"Schedule evaluation task failed: {e}", exc_info=True)
    finally:
        if db:
            db.close()


def _notify_device_schedule_change(
    device_id: str,
    playlist_id: int,
    schedule_id: int | None,
    schedule_name: str | None
):
    """
    通知设备调度变化

    通过 WebSocket 发送 schedule_update 消息
    """
    try:
        from app.websocket.handler import manager

        # 发送 WebSocket 消息
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                manager.notify_schedule_trigger(
                    device_id,
                    playlist_id,
                    schedule_id,
                    schedule_name
                )
            )
        finally:
            loop.close()

    except Exception as e:
        logger.warning(f"Failed to notify device {device_id}: {e}")


def start():
    """启动调度器"""
    # 添加调度评估任务（每分钟执行）
    scheduler.add_job(
        _evaluate_schedules_task,
        'interval',
        minutes=1,
        id='schedule_evaluation',
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=30
    )
    logger.info("Schedule evaluation job scheduled (every 1 minute)")

    scheduler.start()
    logger.info("APScheduler started")


def stop():
    """停止调度器"""
    scheduler.shutdown(wait=True)
    logger.info("APScheduler stopped")
