"""
播放列表调度管理 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.schedule import PlaylistSchedule
from app.models.playlist import Playlist
from app.schemas.schedule import (
    ScheduleCreate,
    ScheduleUpdate,
    ScheduleResponse,
    ScheduleListResponse,
    ActiveScheduleResponse,
    PlayerSchedulesResponse,
    PlayerScheduleData,
    days_to_display,
)
from app.services.schedule_service import ScheduleService
from app.api.auth import get_current_user
from app.models.user import User
from app.utils.logger import logger

router = APIRouter(
    tags=["调度"],
    responses={
        404: {"description": "调度未找到"},
    },
)


def _schedule_to_response(
    schedule: PlaylistSchedule, conflicts: list = None, db: Session = None
) -> ScheduleResponse:
    """将调度模型转换为响应模型"""
    # 获取播放列表名称
    playlist_name = None
    if db:
        playlist = db.query(Playlist).filter(Playlist.id == schedule.playlist_id).first()
        if playlist:
            playlist_name = playlist.name

    return ScheduleResponse(
        id=schedule.id,
        device_id=schedule.device_id,
        playlist_id=schedule.playlist_id,
        playlist_name=playlist_name,
        start_time=schedule.start_time.strftime("%H:%M:%S"),
        end_time=schedule.end_time.strftime("%H:%M:%S"),
        days_of_week=schedule.days_of_week,
        days_display=days_to_display(schedule.days_of_week),
        enabled=schedule.enabled,
        priority=schedule.priority,
        conflicts=conflicts or [],
        created_at=schedule.created_at,
        updated_at=schedule.updated_at,
    )


@router.post(
    "/",
    response_model=ScheduleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建调度规则",
    description="""
创建新的播放列表调度规则。

**请求体：**
- `device_id` (必需): 目标设备 ID
- `playlist_id` (必需): 要激活的播放列表 ID
- `start_time` (必需): 开始时间 (HH:MM:SS)
- `end_time` (必需): 结束时间 (HH:MM:SS)，必须大于 start_time
- `days_of_week`: 星期位掩码 (1-127)，默认 127 (每天)
- `enabled`: 是否启用，默认 true
- `priority`: 优先级，默认 0

**注意：** 播放列表必须已分配给设备才能创建调度。
""",
)
def create_schedule(
    schedule_data: ScheduleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ScheduleService(db)
    try:
        schedule, conflicts = service.create(schedule_data)
        logger.info(f"Schedule created: {schedule.id} for device {schedule.device_id}")
        return _schedule_to_response(schedule, conflicts, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/",
    response_model=ScheduleListResponse,
    summary="获取调度列表",
    description="""
获取指定设备的所有调度规则。

**查询参数：**
- `device_id` (必需): 设备 ID

**返回：**
- 调度列表（按开始时间排序）
- 总数
""",
)
def list_schedules(
    device_id: int = Query(..., description="设备 ID"),
    db: Session = Depends(get_db),
):
    service = ScheduleService(db)
    schedules = service.get_by_device(device_id)

    items = [_schedule_to_response(s, db=db) for s in schedules]
    return ScheduleListResponse(schedules=items, total=len(items))


@router.get(
    "/active",
    response_model=ActiveScheduleResponse,
    summary="获取当前激活的调度",
    description="""
获取设备当前应该激活的调度。

**查询参数：**
- `device_id` (必需): 设备 ID

**返回：**
- 当前激活的播放列表 ID
- 调度 ID
- 调度名称

如果没有匹配的调度，返回 null 值。
""",
)
def get_active_schedule(
    device_id: int = Query(..., description="设备 ID"),
    db: Session = Depends(get_db),
):
    service = ScheduleService(db)
    schedule = service.get_active_schedule(device_id)

    if not schedule:
        return ActiveScheduleResponse()

    playlist = db.query(Playlist).filter(Playlist.id == schedule.playlist_id).first()
    playlist_name = playlist.name if playlist else None

    return ActiveScheduleResponse(
        active_playlist_id=schedule.playlist_id,
        schedule_id=schedule.id,
        schedule_name=playlist_name,
    )


@router.get(
    "/{schedule_id}",
    response_model=ScheduleResponse,
    summary="获取调度详情",
    description="根据 ID 获取单个调度规则的详细信息。",
)
def get_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
):
    service = ScheduleService(db)
    schedule = service.get_by_id(schedule_id)

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="schedule not found"
        )

    return _schedule_to_response(schedule, db=db)


@router.put(
    "/{schedule_id}",
    response_model=ScheduleResponse,
    summary="更新调度规则",
    description="""
更新现有的调度规则。

**请求体：** 所有字段可选，只更新提供的字段。

**注意：**
- `end_time` 必须大于 `start_time`
- 播放列表必须已分配给设备
""",
)
def update_schedule(
    schedule_id: int,
    schedule_data: ScheduleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ScheduleService(db)
    try:
        schedule, conflicts = service.update(schedule_id, schedule_data)
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="schedule not found"
            )
        logger.info(f"Schedule updated: {schedule_id}")
        return _schedule_to_response(schedule, conflicts, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{schedule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除调度规则",
    description="删除指定的调度规则。",
)
def delete_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ScheduleService(db)
    if not service.delete(schedule_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="schedule not found"
        )
    logger.info(f"Schedule deleted: {schedule_id}")
    return None
