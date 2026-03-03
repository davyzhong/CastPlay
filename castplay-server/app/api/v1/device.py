"""
Device API Routes (FastAPI 版本)
"""
import logging
import uuid
import random
import string
from datetime import datetime, time
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from app.database import get_db
from app.api.deps import get_current_user
from app.models.device import Device, DeviceSchedule
from app.models.playlist import DevicePlaylist

logger = logging.getLogger(__name__)
router = APIRouter()

DEFAULT_PAGE_SIZE = 20


# ============= Pydantic 模型 =============

class DeviceCreate(BaseModel):
    device_id: Optional[str] = None
    device_name: Optional[str] = None
    timezone: str = "Asia/Shanghai"


class DeviceRegister(BaseModel):
    device_id: Optional[str] = None
    hardware_id: Optional[str] = None
    device_name: Optional[str] = None
    timezone: str = "Asia/Shanghai"


class DeviceUpdate(BaseModel):
    device_name: Optional[str] = None
    timezone: Optional[str] = None
    status: Optional[str] = None


class ScheduleCreate(BaseModel):
    power_on_time: Optional[str] = None
    power_off_time: Optional[str] = None
    is_enabled: bool = True
    weekdays: List[int] = [1, 2, 3, 4, 5, 6, 7]


class DeviceResponse(BaseModel):
    id: int
    device_id: str
    device_name: Optional[str]
    hardware_id: Optional[str]
    timezone: str
    status: str
    last_online: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaginatedDeviceResponse(BaseModel):
    devices: List[dict]
    total: int
    page: int
    per_page: int
    pages: int


# ============= 辅助函数 =============

async def _generate_unique_device_id(db: AsyncSession) -> str:
    """生成唯一的设备 ID

    格式: CAS-XXXX (4位大写字母数字)
    如果冲突则增加长度直到唯一
    """
    chars = string.ascii_uppercase + string.digits

    for length in range(4, 8):
        for _ in range(10):
            suffix = ''.join(random.choices(chars, k=length))
            candidate = f'CAS-{suffix}'

            result = await db.execute(
                select(Device).where(Device.device_id == candidate)
            )
            if not result.scalar_one_or_none():
                return candidate

    # 极端情况：使用 UUID 前 8 位
    return f'CAS-{str(uuid.uuid4())[:8].upper()}'


# ============= API 端点 =============

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_device(
    device_data: DeviceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """创建新设备"""
    # 生成唯一设备ID
    device_id = device_data.device_id or str(
        uuid.uuid4())[:12].upper().replace('-', '')
    device_name = device_data.device_name or f'Device-{device_id[:8]}'

    # 检查设备ID是否已存在
    result = await db.execute(
        select(Device).where(Device.device_id == device_id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="设备ID已存在"
        )

    device = Device(
        device_id=device_id,
        device_name=device_name,
        timezone=device_data.timezone,
        status='offline'
    )
    db.add(device)
    await db.commit()
    await db.refresh(device)

    return {
        "message": "Device created successfully",
        "device": device.to_dict()
    }


@router.post("/register")
async def register_device(
    device_data: DeviceRegister,
    db: AsyncSession = Depends(get_db)
):
    """设备注册

    支持两种模式：
    1. 首次注册：不传 device_id，后台自动生成唯一 ID
    2. 重新注册：传入已有 device_id，更新设备信息
    """
    is_new = False
    device = None

    # 1. 尝试通过 device_id 查找已有设备
    if device_data.device_id:
        result = await db.execute(
            select(Device).where(Device.device_id == device_data.device_id)
        )
        device = result.scalar_one_or_none()

    # 2. 如果没找到且有 hardware_id，尝试通过 hardware_id 查找
    if not device and device_data.hardware_id:
        result = await db.execute(
            select(Device).where(Device.hardware_id == device_data.hardware_id)
        )
        device = result.scalar_one_or_none()

    if device:
        # 更新已有设备信息
        if device_data.device_name:
            device.device_name = device_data.device_name
        device.timezone = device_data.timezone
        device.last_online = datetime.utcnow()
        device.status = 'online'
        if device_data.hardware_id and not device.hardware_id:
            device.hardware_id = device_data.hardware_id
    else:
        # 创建新设备
        is_new = True
        new_device_id = await _generate_unique_device_id(db)
        device_name = device_data.device_name or f'设备-{new_device_id}'

        device = Device(
            device_id=new_device_id,
            device_name=device_name,
            hardware_id=device_data.hardware_id,
            timezone=device_data.timezone,
            last_online=datetime.utcnow(),
            status='online'
        )
        db.add(device)

    await db.commit()
    await db.refresh(device)

    logger.info(f"Device registered: {device.device_id} (new={is_new})")

    return {
        "message": "Device registered successfully",
        "device": device.to_dict(),
        "is_new": is_new
    }


@router.put("/{device_id}/heartbeat")
async def heartbeat(
    device_id: int,
    db: AsyncSession = Depends(get_db)
):
    """心跳上报"""
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    device.last_online = datetime.utcnow()
    device.status = 'online'
    await db.commit()

    return {
        "message": "Heartbeat received",
        "device": device.to_dict()
    }


@router.get("", response_model=PaginatedDeviceResponse)
async def list_devices(
    page: int = Query(1, ge=1),
    per_page: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """设备列表"""
    # 构建查询
    query = select(Device)
    count_query = select(func.count(Device.id))

    if status_filter:
        query = query.where(Device.status == status_filter)
        count_query = count_query.where(Device.status == status_filter)

    # 获取总数
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # 分页查询
    query = query.order_by(Device.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    devices = result.scalars().all()

    pages = (total + per_page - 1) // per_page

    return PaginatedDeviceResponse(
        devices=[d.to_dict() for d in devices],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages
    )


@router.get("/{device_id}")
async def get_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """获取设备详情"""
    # 预加载关联数据
    query = select(Device).options(
        selectinload(Device.schedule),
        selectinload(Device.playlists).selectinload(DevicePlaylist.playlist)
    ).where(Device.id == device_id)

    result = await db.execute(query)
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    device_dict = device.to_dict()

    # 包含定时配置
    if device.schedule:
        device_dict['schedule'] = device.schedule.to_dict()

    # 包含播放列表
    device_dict['playlists'] = [
        {
            'id': dp.playlist_id,
            'name': dp.playlist.name if dp.playlist else None,
            'is_active': dp.is_active
        }
        for dp in device.playlists
    ]

    return device_dict


@router.put("/{device_id}")
async def update_device(
    device_id: int,
    device_data: DeviceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """更新设备信息"""
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    if device_data.device_name is not None:
        device.device_name = device_data.device_name
    if device_data.timezone is not None:
        device.timezone = device_data.timezone
    if device_data.status is not None:
        device.status = device_data.status

    device.updated_at = datetime.utcnow()
    await db.commit()

    return {
        "message": "Device updated successfully",
        "device": device.to_dict()
    }


@router.delete("/{device_id}")
async def delete_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """删除设备"""
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    await db.delete(device)
    await db.commit()

    return {"message": "Device deleted successfully"}


@router.post("/{device_id}/schedule")
@router.put("/{device_id}/schedule")
async def set_schedule(
    device_id: int,
    schedule_data: ScheduleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """设置定时配置"""
    result = await db.execute(
        select(Device).options(selectinload(Device.schedule))
        .where(Device.id == device_id)
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    power_on_time = None
    power_off_time = None

    if schedule_data.power_on_time:
        h, m = map(int, schedule_data.power_on_time.split(':'))
        power_on_time = time(h, m)

    if schedule_data.power_off_time:
        h, m = map(int, schedule_data.power_off_time.split(':'))
        power_off_time = time(h, m)

    if device.schedule:
        # 更新现有配置
        device.schedule.power_on_time = power_on_time
        device.schedule.power_off_time = power_off_time
        device.schedule.is_enabled = schedule_data.is_enabled
        device.schedule.weekdays = ','.join(map(str, schedule_data.weekdays))
        schedule = device.schedule
    else:
        # 创建新配置
        schedule = DeviceSchedule(
            device_id=device.id,
            power_on_time=power_on_time,
            power_off_time=power_off_time,
            is_enabled=schedule_data.is_enabled,
            weekdays=','.join(map(str, schedule_data.weekdays))
        )
        db.add(schedule)

    await db.commit()
    await db.refresh(schedule)

    # TODO: 触发定时配置更新通知 (WebSocket)

    return {
        "message": "Schedule set successfully",
        "schedule": schedule.to_dict()
    }


@router.get("/{device_id}/schedule")
async def get_schedule(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """查询定时配置"""
    result = await db.execute(
        select(Device).options(selectinload(Device.schedule))
        .where(Device.id == device_id)
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    if not device.schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No schedule configured"
        )

    return device.schedule.to_dict()
