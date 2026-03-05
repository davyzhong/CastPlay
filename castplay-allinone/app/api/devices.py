"""
设备管理 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, Request, Response
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
import hashlib
import uuid

from app.database import get_db
from app.models.device import Device, DeviceSchedule
from app.schemas.device import (
    DeviceCreate, DeviceResponse, DeviceUpdate,
    DeviceScheduleCreate, DeviceScheduleResponse
)
from app.api.auth import get_current_user
from app.models.user import User
from app.utils.logger import logger

router = APIRouter()


def generate_registration_code(mac_address: str) -> str:
    """基于 MAC 地址生成 12 位注册码"""
    clean_mac = mac_address.replace(':', '').upper()
    hash_obj = hashlib.sha256(clean_mac.encode())
    code = hash_obj.hexdigest()[:12].upper()
    return f"CP-{code[:4]}-{code[4:8]}-{code[8:12]}"


def generate_device_id_from_mac(mac_address: str) -> str:
    """基于 MAC 地址生成设备 ID"""
    clean_mac = mac_address.replace(':', '').upper()
    return f"device-{clean_mac}"


def get_client_ip(request: Request) -> str:
    """获取客户端 IP 地址"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "0.0.0.0"


@router.post("/register", response_model=DeviceResponse)
def register_device(
    device_data: DeviceCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    注册新设备

    支持两种注册方式：
    1. MAC 地址注册（推荐）：提供 mac_address，自动生成 device_id 和 registration_code
    2. 传统 device_id 注册：提供 device_id

    - **device_id**: 设备唯一标识（UUID）
    - **device_name**: 设备名称
    - **timezone**: 时区（默认 Asia/Shanghai）
    - **mac_address**: MAC 地址 (XX:XX:XX:XX:XX:XX)
    - **ip_address**: IP 地址（可选，自动从请求获取）
    - **registration_code**: 注册码（可选，MAC 注册时自动生成）

    如果设备已存在，更新在线状态
    """
    # 获取客户端 IP
    client_ip = device_data.ip_address or get_client_ip(request)

    # MAC 地址优先注册
    if device_data.mac_address:
        mac_address = device_data.mac_address.upper()
        registration_code = device_data.registration_code or generate_registration_code(mac_address)
        device_id = generate_device_id_from_mac(mac_address)

        # 检查 MAC 是否已存在
        existing = db.query(Device).filter(Device.mac_address == mac_address).first()

        if existing:
            # 更新最后在线时间和状态
            existing.last_online = datetime.utcnow()
            existing.status = "online"
            existing.ip_address = client_ip
            if device_data.device_name and device_data.device_name != "Default Device":
                existing.device_name = device_data.device_name
            if device_data.timezone and device_data.timezone != "Asia/Shanghai":
                existing.timezone = device_data.timezone

            db.commit()
            db.refresh(existing)
            response.status_code = status.HTTP_200_OK
            logger.info(f"Device updated via MAC: {existing.device_name} ({existing.mac_address})")
            return existing

        # 生成设备名称
        device_name = device_data.device_name
        if device_name == "Default Device":
            device_name = f"CastPlay-{mac_address.replace(':', '')[-6:]}"

        # 创建新设备
        new_device = Device(
            device_id=device_id,
            device_name=device_name,
            timezone=device_data.timezone,
            mac_address=mac_address,
            ip_address=client_ip,
            registration_code=registration_code,
            last_online=datetime.utcnow(),
            status="online"
        )
        db.add(new_device)
        db.commit()
        db.refresh(new_device)

        logger.info(f"New device registered via MAC: {new_device.device_name} ({new_device.mac_address})")
        response.status_code = status.HTTP_201_CREATED
        return new_device

    # 传统 device_id 注册
    if not device_data.device_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either device_id or mac_address is required"
        )

    existing = db.query(Device).filter(Device.device_id == device_data.device_id).first()

    if existing:
        existing.last_online = datetime.utcnow()
        existing.status = "online"
        existing.ip_address = client_ip
        if device_data.device_name and device_data.device_name != "Default Device":
            existing.device_name = device_data.device_name
        if device_data.timezone and device_data.timezone != "Asia/Shanghai":
            existing.timezone = device_data.timezone

        db.commit()
        db.refresh(existing)
        response.status_code = status.HTTP_200_OK
        logger.info(f"Device updated: {existing.device_name} ({existing.device_id})")
        return existing

    # 创建新设备
    new_device = Device(
        device_id=device_data.device_id,
        device_name=device_data.device_name,
        timezone=device_data.timezone,
        ip_address=client_ip,
        last_online=datetime.utcnow(),
        status="online"
    )
    db.add(new_device)
    db.commit()
    db.refresh(new_device)

    logger.info(f"New device registered: {new_device.device_name} ({new_device.device_id})")
    response.status_code = status.HTTP_201_CREATED
    return new_device


@router.put("/{device_id}/heartbeat")
def device_heartbeat(device_id: int, db: Session = Depends(get_db)):
    """
    设备心跳

    更新设备最后在线时间和状态
    """
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    device.last_online = datetime.utcnow()
    device.status = "online"
    db.commit()

    return {"message": "Heartbeat received", "device_id": device.device_id}


@router.get("/", response_model=list[DeviceResponse])
def list_devices(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, pattern="^(online|offline)$"),
    db: Session = Depends(get_db)
):
    """
    获取设备列表

    - **skip**: 跳过数量（分页）
    - **limit**: 返回数量（分页）
    - **status_filter**: 过滤状态（online/offline）
    """
    query = db.query(Device)

    if status_filter:
        query = query.filter(Device.status == status_filter)

    devices = query.order_by(Device.id).offset(skip).limit(limit).all()
    return devices


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(device_id: int, db: Session = Depends(get_db)):
    """
    获取设备详情
    """
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    return device


@router.put("/{device_id}", response_model=DeviceResponse)
def update_device(
    device_id: int,
    device_data: DeviceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新设备信息

    需要认证
    """
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    # 更新字段
    if device_data.device_name is not None:
        device.device_name = device_data.device_name
    if device_data.timezone is not None:
        device.timezone = device_data.timezone
    if device_data.status is not None:
        device.status = device_data.status
    if device_data.playback_speed is not None:
        device.playback_speed = device_data.playback_speed

    db.commit()
    db.refresh(device)

    logger.info(f"Device updated: {device.device_name}")
    return device


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除设备

    需要认证
    """
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    db.delete(device)
    db.commit()

    logger.info(f"Device deleted: {device.device_name}")
    return None


@router.post("/{device_id}/schedule", response_model=DeviceScheduleResponse)
async def set_device_schedule(
    device_id: int,
    schedule_data: DeviceScheduleCreate,
    db: Session = Depends(get_db)
):
    """
    设置设备定时配置

    需要认证
    """
    # 检查设备是否存在
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    # 查找或创建定时配置
    existing = db.query(DeviceSchedule).filter(
        DeviceSchedule.device_id == device_id
    ).first()

    if existing:
        # 更新现有配置
        existing.power_on_time = schedule_data.power_on_time
        existing.power_off_time = schedule_data.power_off_time
        existing.is_enabled = schedule_data.is_enabled
        existing.weekdays = schedule_data.weekdays
    else:
        # 创建新配置
        new_schedule = DeviceSchedule(
            device_id=device_id,
            power_on_time=schedule_data.power_on_time,
            power_off_time=schedule_data.power_off_time,
            is_enabled=schedule_data.is_enabled,
            weekdays=schedule_data.weekdays
        )
        db.add(new_schedule)
        existing = new_schedule

    db.commit()
    db.refresh(existing)

    logger.info(f"Schedule set for device {device_id}")

    # 发送 WebSocket 通知
    from app.services.notification import NotificationService
    await NotificationService.notify_schedule_update(device_id)

    return DeviceScheduleResponse(
        id=existing.id,
        device_id=existing.device_id,
        power_on_time=existing.power_on_time,
        power_off_time=existing.power_off_time,
        is_enabled=existing.is_enabled,
        weekdays=existing.get_weekdays_list(),
        created_at=existing.created_at,
        updated_at=existing.updated_at
    )


@router.get("/{device_id}/schedule", response_model=DeviceScheduleResponse)
def get_device_schedule(device_id: int, db: Session = Depends(get_db)):
    """
    获取设备定时配置
    """
    schedule = db.query(DeviceSchedule).filter(
        DeviceSchedule.device_id == device_id
    ).first()

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No schedule configured for this device"
        )

    return DeviceScheduleResponse(
        id=schedule.id,
        device_id=schedule.device_id,
        power_on_time=schedule.power_on_time,
        power_off_time=schedule.power_off_time,
        is_enabled=schedule.is_enabled,
        weekdays=schedule.get_weekdays_list(),
        created_at=schedule.created_at,
        updated_at=schedule.updated_at
    )


@router.put("/{device_id}/playback-speed", response_model=DeviceResponse)
async def set_playback_speed(
    device_id: int,
    speed: int = Body(..., embed=True, ge=1, le=8),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    设置设备播放速度

    - **speed**: 播放速度倍数 (1, 2, 4, 8)

    需要认证
    """
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    # 验证速度值
    valid_speeds = [1, 2, 4, 8]
    if speed not in valid_speeds:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid speed value. Must be one of: {valid_speeds}"
        )

    device.playback_speed = speed
    db.commit()
    db.refresh(device)

    logger.info(f"Playback speed set to {speed}x for device {device_id}")

    # 发送 WebSocket 通知
    from app.services.notification import NotificationService
    await NotificationService.notify_config_update(device_id, {"playback_speed": speed})

    return device


@router.get("/{device_id}/cached-media")
def get_cached_media(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取设备缓存的媒体列表

    需要认证
    """
    from app.models.device import CachedMedia

    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    cached = db.query(CachedMedia).filter(CachedMedia.device_id == device_id).all()

    return {
        "device_id": device_id,
        "cached_media": [
            {
                "id": item.id,
                "media_id": item.media_id,
                "local_path": item.local_path,
                "md5_hash": item.md5_hash,
                "file_size": item.file_size,
                "download_status": item.download_status,
                "created_at": item.created_at.isoformat() if item.created_at else None
            }
            for item in cached
        ]
    }
