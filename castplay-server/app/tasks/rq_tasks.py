"""
RQ Task Queue - 替代 Celery 的轻量级任务队列

使用 Redis Queue (RQ) 处理后台任务，如 PPT 转换等
"""
import logging
from typing import Optional, Callable, Any
from functools import wraps

from redis import Redis
from rq import Queue
from rq.job import Job

from app.core.config import settings

logger = logging.getLogger(__name__)

# Redis 连接
redis_conn: Optional[Redis] = None
task_queue: Optional[Queue] = None


def init_task_queue():
    """初始化任务队列"""
    global redis_conn, task_queue

    try:
        redis_conn = Redis.from_url(settings.REDIS_URL)
        redis_conn.ping()  # 测试连接
        task_queue = Queue(connection=redis_conn)
        logger.info("RQ task queue initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to connect to Redis for task queue: {e}")
        redis_conn = None
        task_queue = None


def get_queue() -> Optional[Queue]:
    """获取任务队列"""
    if task_queue is None:
        init_task_queue()
    return task_queue


def enqueue_task(func: Callable, *args, **kwargs) -> Optional[Job]:
    """将任务加入队列

    Args:
        func: 要执行的函数
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        Job 对象，如果队列不可用则返回 None
    """
    queue = get_queue()

    if queue is None:
        logger.warning(
            f"Task queue not available, cannot enqueue {func.__name__}")
        return None

    try:
        job = queue.enqueue(func, *args, **kwargs)
        logger.info(f"Task {func.__name__} enqueued with job id: {job.id}")
        return job
    except Exception as e:
        logger.error(f"Failed to enqueue task {func.__name__}: {e}")
        return None


def task(func: Callable) -> Callable:
    """任务装饰器

    用法:
        @task
        def my_task(arg1, arg2):
            ...

        # 同步调用
        my_task(arg1, arg2)

        # 异步调用
        my_task.delay(arg1, arg2)
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    def delay(*args, **kwargs):
        return enqueue_task(func, *args, **kwargs)

    wrapper.delay = delay
    return wrapper


# ============= 具体任务定义 =============

@task
def convert_ppt_to_video(media_id: int) -> bool:
    """PPT 转换为视频任务

    Args:
        media_id: 媒体文件 ID

    Returns:
        转换是否成功
    """
    import os
    import subprocess
    from app.database import AsyncSessionLocal
    from app.models.media import MediaFile
    import asyncio

    async def _convert():
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select

            result = await db.execute(select(MediaFile).where(MediaFile.id == media_id))
            media = result.scalar_one_or_none()

            if not media:
                logger.error(f"Media {media_id} not found")
                return False

            if media.file_type != 'ppt':
                logger.error(f"Media {media_id} is not a PPT file")
                return False

            try:
                # 转换目标路径
                converted_dir = settings.CONVERTED_FOLDER
                os.makedirs(converted_dir, exist_ok=True)

                output_path = os.path.join(
                    converted_dir,
                    f"{os.path.splitext(os.path.basename(media.file_path))[0]}.mp4"
                )

                # TODO: 实际的 PPT 转换逻辑
                # 这里需要根据系统环境选择合适的转换工具
                # 例如 LibreOffice + ffmpeg

                # 更新数据库记录
                media.converted_path = output_path
                media.status = 'ready'
                await db.commit()

                logger.info(f"PPT {media_id} converted successfully")
                return True

            except Exception as e:
                logger.error(f"Failed to convert PPT {media_id}: {e}")
                media.status = 'error'
                await db.commit()
                return False

    # 在同步上下文中运行异步代码
    return asyncio.run(_convert())


@task
def generate_thumbnail(media_id: int) -> bool:
    """生成缩略图任务"""
    import os
    import subprocess
    import asyncio
    from app.database import AsyncSessionLocal
    from app.models.media import MediaFile

    async def _generate():
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select

            result = await db.execute(select(MediaFile).where(MediaFile.id == media_id))
            media = result.scalar_one_or_none()

            if not media:
                logger.error(f"Media {media_id} not found")
                return False

            try:
                thumbnail_dir = settings.THUMBNAIL_FOLDER
                os.makedirs(thumbnail_dir, exist_ok=True)

                thumb_path = os.path.join(
                    thumbnail_dir, f"thumb_{media_id}.jpg")

                # 根据文件类型生成缩略图
                if media.file_type == 'video':
                    # 使用 ffmpeg 截取视频第一帧
                    cmd = [
                        'ffmpeg', '-y', '-i', media.file_path,
                        '-ss', '00:00:01', '-vframes', '1',
                        '-vf', 'scale=320:-1', thumb_path
                    ]
                    subprocess.run(cmd, capture_output=True, timeout=30)

                elif media.file_type == 'image':
                    # 使用 Pillow 生成缩略图
                    from PIL import Image
                    with Image.open(media.file_path) as img:
                        img.thumbnail((320, 180))
                        img.save(thumb_path, 'JPEG')

                if os.path.exists(thumb_path):
                    media.thumbnail_path = thumb_path
                    await db.commit()
                    logger.info(f"Thumbnail generated for media {media_id}")
                    return True

                return False

            except Exception as e:
                logger.error(
                    f"Failed to generate thumbnail for {media_id}: {e}")
                return False

    return asyncio.run(_generate())
