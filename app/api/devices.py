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
from app.utils.internal_auth import verify_internal_api_key  # P0-5 修复：导入内部认证

router = APIRouter(
    tags=["设备"],
    responses={
        404: {"description": "设备未找到"},
    }
)


def generate_friendly_code(length: int = 6) -> str:
    """生成易读的字母数字组合（排除易混淆字符）"""
    chars = string.ascii_uppercase + string.digits
    # 排除易混淆字符: 0, O, 1, I, L
    chars = chars.replace('0', '').replace('O', '').replace('1', '').replace('I', '').replace('L', '')
    return ''.join(random.choices(chars, k=length))


def generate_registration_code(device_id: str = None) -> str:
    """
    生成友好的注册码（6位字母数字）
    基于设备 ID 生成确定性注册码
    """
    if device_id:
        # 使用哈希确保同一设备始终生成相同注册码
        hash_obj = hashlib.sha256(device_id.encode())
        # 使用哈希生成 6 位注册码
        hex_digest = hash_obj.hexdigest().upper()
        # 映射到可用字符集
        chars = string.ascii_uppercase + string.digits
        chars = chars.replace('0', '').replace('O', '').replace('1', '').replace('I', '').replace('L', '')
        code = ''.join(chars[int(hex_digest[i:i+2], 16) % len(chars)] for i in range(0, 12, 2))
        return code
    else:
        # 生成随机 6 位注册码
        return generate_friendly_code()


def get_client_ip(request: Request) -> str:
    """获取客户端 IP 地址"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "0.0.0.0"


@router.post(
    "/register",
    response_model=DeviceResponse,
    summary="注册新设备",
    description="""
注册或更新播放设备。

**注册方式：**
1. 优先使用客户端提供的 device_id（UUID 格式）
2. 如果没有 device_id，服务端自动生成 UUID
3. MAC 地址仅作为辅助标识

**请求体：**
- `device_id` (可选): 设备唯一标识（UUID），不提供则自动生成
- `device_name` (可选): 设备名称，默认为 CastPlay-XXXXXXXX
- `timezone` (可选): 时区，默认 Asia/Shanghai
- `mac_address` (可选): MAC 地址，仅作为辅助标识
- `ip_address` (可选): IP 地址，默认从请求获取

**行为：**
- 如果设备已存在，更新在线状态并返回 200
- 如果是新设备，创建记录并返回 201
""",
    responses={
        200: {"description": "设备已存在，更新状态"},
        201: {"description": "新设备注册成功"}
    }
)
def register_device(
    device_data: DeviceCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
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
        elif device_data.device_name == "Default Device":
            # 客户端发送 "Default Device" 时，根据 device_type 生成正确的名称
            device_type = (device_data.device_type or "web_browser").lower()
            is_android = device_type.startswith("android")
            prefix = "Android" if is_android else "Web"
            # 如果当前名称前缀与设备类型不匹配，则更新
            if (is_android and not existing.device_name.startswith("Android-")) or \
               (not is_android and not existing.device_name.startswith("Web-")):
                existing.device_name = f"{prefix}-{existing.registration_code}"
                logger.info(f"Device name updated: {existing.device_name} (ID: {existing.device_id}, type: {device_data.device_type})")
        # 更新设备类型（如果提供了且与当前不同）
        if device_data.device_type and existing.device_type != device_data.device_type:
            existing.device_type = device_data.device_type
            logger.info(f"Device type updated: {existing.device_type} (ID: {existing.device_id})")
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
        # 根据设备类型生成名称：Web-XXXXXX 或 Android-XXXXXX
        # device_type 可能是: android_tv, web_browser, android, web 等
        device_type = (device_data.device_type or "web_browser").lower()
        is_android = device_type.startswith("android")
        prefix = "Android" if is_android else "Web"
        device_name = f"{prefix}-{registration_code}"

    # 查找 Default 播放列表（如果没有则创建）
    from app.models.playlist import Playlist
    default_playlist = db.query(Playlist).filter(Playlist.name == "Default").first()
    if not default_playlist:
        # 创建默认播放列表
        default_playlist = Playlist(
            name="Default",
            description="默认播放列表 - 所有新设备自动关联到此播放列表",
            is_system=False
        )
        db.add(default_playlist)
        db.commit()
        logger.info("Created Default playlist for new devices")

    # 创建新设备
    new_device = Device(
        device_id=device_id,
        device_name=device_name,
        timezone=device_data.timezone,
        device_type=device_data.device_type or "web_browser",
        mac_address=mac_address,
        ip_address=client_ip,
        registration_code=registration_code,
        last_online=datetime.utcnow(),
        status="online",
        current_playlist_id=default_playlist.id  # 关联到 Default 播放列表
    )
    db.add(new_device)
    db.commit()
    db.refresh(new_device)

    # 在 device_playlists 表中创建关联记录（用于 /api/player/init 接口查询）
    from app.models.playlist import DevicePlaylist
    device_playlist = DevicePlaylist(
        device_id=new_device.id,
        playlist_id=default_playlist.id,
        is_active=True
    )
    db.add(device_playlist)
    db.commit()

    logger.info(f"New device registered: {new_device.device_name} (ID: {device_id}, 注册码：{registration_code}, playlist: {default_playlist.name})")
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


@router.get(
    "/by-code/{registration_code}",
    response_model=DeviceResponse,
    summary="通过注册码获取设备",
    description="""
通过注册码查询设备信息，用于设备身份恢复。

当客户端清除缓存后，可以通过输入注册码找回原有设备身份。
"""
)
def get_device_by_code(registration_code: str, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.registration_code == registration_code.upper()).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="注册码无效，未找到对应设备"
        )
    return device


@router.get(
    "/",
    summary="获取设备列表",
    description="""
获取所有注册设备的列表，支持分页和状态过滤。

**查询参数：**
- `skip`: 跳过数量（用于分页），默认 0
- `limit`: 返回数量，默认 20，最大 100
- `status_filter`: 按状态过滤，可选值：online、offline
"""
)
def list_devices(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, pattern="^(online|offline)$"),
    db: Session = Depends(get_db)
):
    query = db.query(Device)

    if status_filter:
        query = query.filter(Device.status == status_filter)

    total = query.count()
    devices = query.order_by(Device.id.desc()).offset(skip).limit(limit).all()

    return {
        "items": devices,
        "total": total
    }


@router.post("/cleanup", summary="清理无效设备")
def cleanup_invalid_devices(
    db: Session = Depends(get_db),
    _: str = Depends(verify_internal_api_key)  # P0-5 修复：添加内部认证
):
    """
    清理无效的测试设备和废弃设备

    清理条件：
    1. 名称包含 "test" 或 "测试" 且没有关联播放列表（排除固定测试设备）
    2. 超过 7 天未上线且没有关联播放列表且没有注册码
    3. Web 播放端测试设备（名称为 Web-XXXXXX 格式）且没有关联播放列表

    固定测试设备（不会被清理）：
    - web-player-test-01 (Player-Test01)
    - web-player-sim-01 (Player-Sim01)
    """
    from datetime import timedelta
    from sqlalchemy import or_
    from app.models.playlist import DevicePlaylist
    import re

    # 固定测试设备的 device_id（不会被清理）
    FIXED_TEST_DEVICE_IDS = {
        'web-player-test-01',  # PlayerCore 测试端
        'web-player-sim-01',   # WebPlayerSimulator 测试端
    }

    # 计算 7 天前的时间
    threshold = datetime.utcnow() - timedelta(days=7)

    # 获取所有有关联播放列表的设备 ID（这些设备不应被清理）
    devices_with_playlists = db.query(DevicePlaylist.device_id).distinct().all()
    protected_device_ids = {dp[0] for dp in devices_with_playlists}

    # Web 设备名称正则：Web-XXXXXX（6位大写字母数字）
    web_device_pattern = re.compile(r'^Web-[A-Z0-9]{6}$')

    # 查找需要清理的设备
    all_devices = db.query(Device).all()
    devices_to_delete = []

    for device in all_devices:
        # 跳过有播放列表关联的设备
        if device.id in protected_device_ids:
            continue

        # 跳过固定测试设备
        if device.device_id in FIXED_TEST_DEVICE_IDS:
            continue

        # 条件 1: 名称包含 test 或 测试（但排除固定设备）
        is_test_device = (
            'test' in device.device_name.lower() or
            '测试' in device.device_name
        )

        # 条件 2: 超过 7 天未上线且没有注册码
        is_abandoned = (
            (device.last_online is None or device.last_online < threshold) and
            not device.registration_code
        )

        # 条件 3: Web 播放端测试设备（Web-XXXXXX 格式，无播放列表关联）
        is_web_test_device = (
            web_device_pattern.match(device.device_name) and
            (device.device_type == 'web_browser' or device.device_type is None)
        )

        if is_test_device or is_abandoned or is_web_test_device:
            devices_to_delete.append(device)

    deleted_count = len(devices_to_delete)

    for device in devices_to_delete:
        db.delete(device)

    db.commit()

    logger.info(f"Cleaned up {deleted_count} invalid/abandoned devices")

    return {
        "deleted_count": deleted_count,
        "message": f"已清理 {deleted_count} 个无效/废弃设备"
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
                "item_count": item_counts.get(p.id, 0),
                "assigned_at": dp.created_at.isoformat() if dp.created_at else None
            }
            for dp, p in assignments
        ]
    }
