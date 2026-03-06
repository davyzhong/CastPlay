"""
设备管理 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, Request, Response
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
import hashlib
import uuid
import random
import string

from app.database import get_db
from app.models.device import Device, DeviceSchedule
from app.models.playlist import PlaylistItem
from app.schemas.device import (
    DeviceCreate, DeviceResponse, DeviceUpdate,
    DeviceScheduleCreate, DeviceScheduleResponse
)
from app.api.auth import get_current_user
from app.models.user import User
from app.utils.logger import logger

router = APIRouter()


def generate_friendly_code(length: int = 4) -> str:
    """生成易读的字母数字组合（排除易混淆字符）"""
    chars = string.ascii_uppercase + string.digits
    # 排除易混淆字符: 0, O, 1, I, L
    chars = chars.replace('0', '').replace('O', '').replace('1', '').replace('I', '').replace('L', '')
    return ''.join(random.choices(chars, k=length))


def generate_registration_code(device_id: str = None) -> str:
    """
    生成友好的注册码（格式: CP-XXXX-XXXX-XXXX）
    基于设备 ID 生成确定性注册码
    """
    if device_id:
        # 使用哈希确保同一设备始终生成相同注册码
        hash_obj = hashlib.sha256(device_id.encode())
        # 使用哈希的前 12 个字符作为基础
        hex_digest = hash_obj.hexdigest()[:12].upper()
        # 转换为易读格式
        code = f"{hex_digest[:4]}-{hex_digest[4:8]}-{hex_digest[8:12]}"
    else:
        # 生成随机注册码
        code = f"{generate_friendly_code()}-{generate_friendly_code()}-{generate_friendly_code()}"

    return f"CP-{code}"


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

    注册方式：
    1. 优先使用客户端提供的 device_id（真正的 UUID）
    2. 如果没有 device_id，服务端生成 UUID 作为 device_id
    3. MAC 地址仅作为辅助信息，不用于生成 ID

    - **device_id**: 设备唯一标识（UUID，可选，不提供则自动生成）
    - **device_name**: 设备名称
    - **timezone**: 时区（默认 Asia/Shanghai）
    - **mac_address**: MAC 地址（可选，仅作为辅助标识）
    - **ip_address**: IP 地址（可选，自动从请求获取）

    如果设备已存在，更新在线状态
    """
    # 获取客户端 IP
    client_ip = device_data.ip_address or get_client_ip(request)

    # 处理 MAC 地址（仅作为辅助信息）
    mac_address = None
    if device_data.mac_address:
        mac_address = device_data.mac_address.upper()

    # 确定设备 ID（UUID 优先）
    if device_data.device_id:
        device_id = device_data.device_id
    else:
        # 服务端生成 UUID
        device_id = str(uuid.uuid4())

    # 检查设备是否已存在（优先按 device_id 查找）
    existing = db.query(Device).filter(Device.device_id == device_id).first()

    # 如果 device_id 不存在但有 MAC 地址，尝试按 MAC 查找
    if not existing and mac_address:
        existing = db.query(Device).filter(Device.mac_address == mac_address).first()
        if existing:
            # 更新设备的 device_id（以最新的为准）
            existing.device_id = device_id

    if existing:
        # 更新最后在线时间和状态
        existing.last_online = datetime.utcnow()
        existing.status = "online"
        existing.ip_address = client_ip
        if mac_address:
            existing.mac_address = mac_address
        if device_data.device_name and device_data.device_name != "Default Device":
            existing.device_name = device_data.device_name
        if device_data.timezone and device_data.timezone != "Asia/Shanghai":
            existing.timezone = device_data.timezone

        db.commit()
        db.refresh(existing)
        response.status_code = status.HTTP_200_OK
        logger.info(f"Device updated: {existing.device_name} (ID: {existing.device_id})")
        return existing

    # 生成注册码（基于 device_id）
    registration_code = generate_registration_code(device_id=device_id)

    # 生成设备名称
    device_name = device_data.device_name
    if device_name == "Default Device":
        # 使用 device_id 的前 8 位作为名称后缀
        device_name = f"CastPlay-{device_id[:8].upper()}"

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

    logger.info(f"New device registered: {new_device.device_name} (ID: {device_id}, 注册码: {registration_code})")
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


@router.get("/")
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

    total = query.count()
    devices = query.order_by(Device.id.desc()).offset(skip).limit(limit).all()

    return {
        "items": devices,
        "total": total
    }


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

    db.commit()
    db.refresh(device)

    logger.info(f"Device updated: {device.device_name}")
    return device


@router.put("/{device_id}/disable", response_model=DeviceResponse)
async def toggle_device_disable(
    device_id: int,
    is_disabled: bool = Body(..., embed=True, description="是否禁用"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    启用/禁用设备

    禁用后的设备只能播放默认播放列表内容，不会接收播放列表更新

    需要认证
    """
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    device.is_disabled = is_disabled
    db.commit()
    db.refresh(device)

    status_text = "禁用" if is_disabled else "启用"
    logger.info(f"Device {status_text}: {device.device_name}")

    # 发送 WebSocket 通知
    from app.services.notification import NotificationService
    if is_disabled:
        # 通知设备已被禁用
        await NotificationService.notify_config_update(device_id, {"is_disabled": True})
    else:
        # 通知设备已启用，需要重新同步
        await NotificationService.notify_playlist_update(device_id)

    return device


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


@router.get("/{device_id}/playlists")
def get_device_playlists(
    device_id: int,
    db: Session = Depends(get_db)
):
    """
    获取设备关联的播放列表

    返回该设备所有已分配的播放列表及其状态
    """
    from app.models.playlist import DevicePlaylist, Playlist
    from sqlalchemy import func

    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    # 查询设备关联的播放列表
    assignments = (
        db.query(DevicePlaylist, Playlist)
        .join(Playlist, DevicePlaylist.playlist_id == Playlist.id)
        .filter(DevicePlaylist.device_id == device_id)
        .all()
    )

    # 获取每个播放列表的媒体数量
    playlist_ids = [dp.playlist_id for dp, p in assignments]
    item_counts = dict(
        db.query(PlaylistItem.playlist_id, func.count(PlaylistItem.id))
        .filter(PlaylistItem.playlist_id.in_(playlist_ids))
        .group_by(PlaylistItem.playlist_id)
        .all()
    ) if playlist_ids else {}

    return {
        "device_id": device_id,
        "playlists": [
            {
                "assignment_id": dp.id,
                "playlist_id": p.id,
                "playlist_name": p.name,
                "is_active": bool(dp.is_active),
                "item_count": item_counts.get(p.id, 0),
                "assigned_at": dp.created_at.isoformat() if dp.created_at else None
            }
            for dp, p in assignments
        ]
    }
