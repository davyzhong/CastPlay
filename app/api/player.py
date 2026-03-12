"""
播放端 API 路由
供 Android 播放端使用的专用 API
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import logging
import os
import time
import threading
from collections import defaultdict

from app.database import get_db
from app.models.device import Device, DeviceSchedule
from app.models.playlist import Playlist, PlaylistItem, DevicePlaylist
from app.models.media import MediaFile
from app.models.device_enhancement import DeviceNotificationLog, PlaylistDownloadTask, PlaylistCleanupSchedule
from app.api.devices import generate_registration_code

logger = logging.getLogger(__name__)

# 常量定义
DEVICE_ONLINE_THRESHOLD_HOURS = 3  # 设备在线阈值（小时），配合 2 小时心跳间隔
HEARTBEAT_TIMEOUT_SECONDS = 5000  # 心跳超时（毫秒）
HEARTBEAT_RATE_LIMIT_PER_MINUTE = 10  # 每分钟最多允许的心跳次数
RATE_LIMIT_MAX_CLIENTS = 10000  # P0-4 修复：最大客户端数量限制
RATE_LIMIT_CLEANUP_INTERVAL = 300  # P0-4 修复：5 分钟清理一次


# P0-4 修复：使用有界的速率限制缓存
class BoundedRateLimitCache:
    """有界的速率限制缓存，支持 LRU 淘汰"""

    def __init__(self, max_clients: int = 10000, cleanup_interval: int = 300):
        self.max_clients = max_clients
        self.cleanup_interval = cleanup_interval
        self._cache: dict[str, list[float]] = {}
        self._last_cleanup = time.time()
        self._lock = threading.Lock()

    def check_and_add(self, key: str, limit_per_minute: int) -> bool:
        """
        检查速率限制并添加新记录

        Returns:
            True 如果未超限，False 如果已超限
        """
        current_time = time.time()
        window_start = current_time - 60

        with self._lock:
            # 定期清理
            if current_time - self._last_cleanup > self.cleanup_interval:
                self._cleanup(current_time)

            # 清理当前 key 的过期记录
            if key in self._cache:
                self._cache[key] = [t for t in self._cache[key] if t > window_start]

            # 检查是否超限
            if key in self._cache and len(self._cache[key]) >= limit_per_minute:
                return False

            # 添加新记录
            if key not in self._cache:
                self._cache[key] = []
            self._cache[key].append(current_time)

            # LRU 淘汰
            while len(self._cache) > self.max_clients:
                # 移除最旧的 key
                oldest_key = min(self._cache.keys(), key=lambda k: min(self._cache[k]) if self._cache[k] else 0)
                del self._cache[oldest_key]

            return True

    def _cleanup(self, current_time: float) -> None:
        """清理过期记录"""
        window_start = current_time - 60
        expired_keys = []
        for key, timestamps in self._cache.items():
            valid = [t for t in timestamps if t > window_start]
            if valid:
                self._cache[key] = valid
            else:
                expired_keys.append(key)
        for key in expired_keys:
            del self._cache[key]
        self._last_cleanup = current_time


# P0-4 修复：使用有界的速率限制缓存
_rate_limit_cache = BoundedRateLimitCache(
    max_clients=RATE_LIMIT_MAX_CLIENTS,
    cleanup_interval=RATE_LIMIT_CLEANUP_INTERVAL
)

# P1-3 修复：心跳推送缓存（减少数据库查询）
_playlist_update_cache: dict[str, tuple[dict, float]] = {}
_PLAYLIST_UPDATE_CACHE_TTL = 300  # 5 分钟缓存有效期


def check_rate_limit(device_id: str, limit_per_minute: int = HEARTBEAT_RATE_LIMIT_PER_MINUTE) -> bool:
    """
    检查设备请求频率

    Args:
        device_id: 设备 ID
        limit_per_minute: 每分钟限制次数

    Returns:
        bool: True 表示未超限，False 表示已超限
    """
    # P0-4 修复：使用有界的缓存
    return _rate_limit_cache.check_and_add(device_id, limit_per_minute)


router = APIRouter(
    tags=["播放端"],
    responses={
        404: {"description": "设备或资源未找到"},
        429: {"description": "请求过于频繁，触发速率限制"}
    }
)


@router.post(
    "/init",
    summary="播放端初始化",
    description="""
播放端设备初始化接口，返回设备信息、激活的播放列表和定时配置。

**请求体：**
```json
{
    "device_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**响应包含：**
- `device`: 设备信息（名称、时区、注册码等）
- `playlists`: 分配给该设备的播放列表数组
- `schedule`: 定时配置（开关机时间、工作日）
- `websocket_url`: WebSocket 连接地址
- `is_disabled`: 设备是否被禁用

**注意：** 被禁用的设备只能获取系统默认播放列表。
""",
    responses={
        200: {
            "description": "初始化成功",
            "content": {
                "application/json": {
                    "example": {
                        "device": {"id": 1, "device_id": "xxx", "device_name": "CastPlay-XXX"},
                        "playlists": [{"id": 1, "name": "默认播放列表", "items": []}],
                        "schedule": {"power_on_time": "08:00", "power_off_time": "18:00"},
                        "websocket_url": "ws://xxx",
                        "is_disabled": False
                    }
                }
            }
        }
    }
)
def player_init(
    device_id: str = Body(..., embed=True, description="设备唯一标识（UUID）"),
    db: Session = Depends(get_db)
):
    # 查找设备
    device = db.query(Device).filter(Device.device_id == device_id).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not registered. Please register first."
        )

    # 更新最后在线时间
    device.last_online = datetime.utcnow()
    device.status = "online"
    db.commit()

    # 获取定时配置
    schedule = db.query(DeviceSchedule).filter(
        DeviceSchedule.device_id == device.id
    ).first()

    schedule_data = None
    if schedule:
        schedule_data = {
            "power_on_time": schedule.power_on_time,
            "power_off_time": schedule.power_off_time,
            "is_enabled": schedule.is_enabled,
            "weekdays": schedule.get_weekdays_list(),
            "timezone": device.timezone
        }

    # 检查设备是否被禁用
    is_disabled = getattr(device, 'is_disabled', False)

    playlists_data = []

    if is_disabled:
        # 禁用设备只能获取默认播放列表
        logger.info(
            f"Device {device_id} is disabled, returning default playlist only")
        default_playlist = db.query(Playlist).filter(
            Playlist.is_system == True).first()
        if default_playlist:
            # 获取播放列表项
            items_query = (
                db.query(
                    PlaylistItem.id,
                    PlaylistItem.media_id,
                    MediaFile.file_name,
                    MediaFile.file_type,
                    MediaFile.file_path,
                    MediaFile.converted_path,
                    MediaFile.file_size,
                    MediaFile.md5_hash,
                    PlaylistItem.display_order,
                    PlaylistItem.display_duration
                )
                .join(MediaFile, PlaylistItem.media_id == MediaFile.id)
                .filter(PlaylistItem.playlist_id == default_playlist.id)
                .order_by(PlaylistItem.display_order)
                .all()
            )

            items = [
                {
                    "id": item.id,
                    "media_id": item.media_id,
                    "file_name": item.file_name,
                    "file_type": item.file_type,
                    "file_url": f"/api/player/media/{item.media_id}/download",
                    "display_order": item.display_order,
                    "display_duration": item.display_duration,
                    "file_size": item.file_size,
                    "md5_hash": item.md5_hash
                }
                for item in items_query
            ]

            playlists_data.append({
                "id": default_playlist.id,
                "name": f"[默认] {default_playlist.name}",
                "version": default_playlist.updated_at.isoformat(),
                "is_system": True,
                "items": items
            })
    else:
        # 正常设备获取激活的播放列表
        playlist_assignments = db.query(DevicePlaylist).filter(
            DevicePlaylist.device_id == device.id,
            DevicePlaylist.is_active == True
        ).all()

        # 如果没有分配播放列表，使用系统默认播放列表
        if not playlist_assignments:
            default_playlist = db.query(Playlist).filter(
                Playlist.is_system == True).first()
            if default_playlist:
                class DefaultPlaylistAssignment:
                    def __init__(self, playlist_id):
                        self.playlist_id = playlist_id
                        self.is_active = True
                playlist_assignments = [
                    DefaultPlaylistAssignment(default_playlist.id)]

        for assignment in playlist_assignments:
            playlist = db.query(Playlist).filter(
                Playlist.id == assignment.playlist_id).first()
            if not playlist:
                continue

            # 获取播放列表项
            items_query = (
                db.query(
                    PlaylistItem.id,
                    PlaylistItem.media_id,
                    MediaFile.file_name,
                    MediaFile.file_type,
                    MediaFile.file_path,
                    MediaFile.converted_path,
                    MediaFile.file_size,
                    MediaFile.md5_hash,
                    PlaylistItem.display_order,
                    PlaylistItem.display_duration
                )
                .join(MediaFile, PlaylistItem.media_id == MediaFile.id)
                .filter(PlaylistItem.playlist_id == playlist.id)
                .order_by(PlaylistItem.display_order)
                .all()
            )

            items = [
                {
                    "id": item.id,
                    "media_id": item.media_id,
                    "file_name": item.file_name,
                    "file_type": item.file_type,
                    "file_url": f"/api/player/media/{item.media_id}/download",
                    "display_order": item.display_order,
                    "display_duration": item.display_duration,
                    "file_size": item.file_size,
                    "md5_hash": item.md5_hash
                }
                for item in items_query
            ]

            playlists_data.append({
                "id": playlist.id,
                "name": playlist.name,
                "version": playlist.updated_at.isoformat(),
                "is_system": playlist.is_system,
                "items": items
            })

    logger.info(
        f"Player initialized for device {device_id} ({device.device_name}), disabled={is_disabled}")

    return {
        "device": {
            "id": device.id,
            "device_id": device.device_id,
            "device_name": device.device_name,
            "timezone": device.timezone,
            "mac_address": device.mac_address,
            "ip_address": device.ip_address,
            "registration_code": device.registration_code,
        },
        "playlists": playlists_data,
        "schedule": schedule_data,
        "websocket_url": f"ws://{device.device_id}",
        "is_disabled": is_disabled
    }


@router.post("/playlist/{playlist_id}/check")
def check_playlist_version(
    playlist_id: int,
    version: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """
    检查播放列表版本

    用于判断是否需要更新

    请求：
    {
        "version": "2026-01-29T10:00:00"
    }

    响应：
    {
        "needs_update": true,
        "server_version": "2026-01-29T11:00:00",
        "local_version": "2026-01-29T10:00:00"
    }
    """
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )

    server_version = playlist.updated_at.isoformat()
    needs_update = server_version > version

    return {
        "needs_update": needs_update,
        "server_version": server_version,
        "local_version": version
    }


@router.get("/media/{media_id}/download")
def download_media(media_id: int, db: Session = Depends(get_db)):
    """
    下载媒体文件（用于播放端）

    如果是 PPT 且已转换，返回转换后的视频
    否则返回原始文件
    """
    from fastapi.responses import FileResponse
    import os

    media = db.query(MediaFile).filter(MediaFile.id == media_id).first()
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media file not found"
        )

    # 返回转换后的文件（如果存在）
    file_path = media.converted_path if media.converted_path else media.file_path

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    return FileResponse(
        file_path,
        filename=media.file_name,
        media_type="application/octet-stream"
    )


@router.get("/media/{media_id}/converted")
def download_converted_media(media_id: int, db: Session = Depends(get_db)):
    """
    下载转换后的文件（仅用于 PPT）

    返回 PPT 转换后的视频文件
    """
    from fastapi.responses import FileResponse
    import os

    media = db.query(MediaFile).filter(MediaFile.id == media_id).first()
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media file not found"
        )

    if not media.converted_path or not os.path.exists(media.converted_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Converted file not found"
        )

    return FileResponse(
        media.converted_path,
        filename=f"{os.path.splitext(media.file_name)[0]}.mp4",
        media_type="video/mp4"
    )


@router.post("/status")
def report_player_status(
    device_id: str = Body(..., embed=True),
    player_status: str = Body("playing", embed=True),
    db: Session = Depends(get_db)
):
    """
    上报播放状态

    用于播放端定期上报当前播放状态

    请求：
    {
        "device_id": "550e8400-e29b-41d4-a716-446655440000",
        "status": "playing"
    }
    """
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    # 更新最后在线时间
    device.last_online = datetime.utcnow()
    device.status = "online"
    db.commit()

    return {"message": "Status reported successfully"}


# ============== 新增简化版 API ==============

class PlayerInitRequest(BaseModel):
    """播放端初始化请求"""
    device_id: str = Field(..., description="设备唯一标识")
    device_type: Optional[str] = Field(
        "web_browser", description="设备类型：android_tv | web_browser")


class HeartbeatRequest(BaseModel):
    """心跳上报请求"""
    device_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="设备唯一标识（UUID 格式，建议仅使用字母、数字、连字符）"
    )
    device_type: Optional[str] = Field(
        "web_browser", description="设备类型：android_tv | web_browser")
    current_playlist_id: Optional[int] = Field(None, description="当前播放列表 ID")
    last_media_id: Optional[int] = Field(None, description="最后播放的媒体 ID")
    status: str = Field(default="playing",
                        description="播放状态：playing | idle | paused")


class VersionCheckRequest(BaseModel):
    """版本检查请求"""
    version: str = Field(..., description="当前版本号（ISO 8601 格式）")


class PlaylistAvailableResponse(BaseModel):
    """可用播放列表响应"""
    id: int
    name: str
    media_count: int
    total_size_mb: float


class DeviceNotificationCreate(BaseModel):
    """设备通知创建请求"""
    device_id: str = Field(..., description="设备唯一标识")
    type: str = Field(..., description="通知类型：download_success/download_failed/insufficient_storage/switch_failed")
    playlist_id: Optional[int] = Field(None, description="关联的播放列表 ID")
    error_message: Optional[str] = Field(None, description="错误消息或详细信息")


@router.post("/devices/notifications")
async def receive_device_notification(
    notification: DeviceNotificationCreate,
    db: Session = Depends(get_db)
):
    """
    接收设备通知（新增）

    接收播放端推送的通知，记录到数据库并触发告警

    支持的通知类型：
    - download_success: 下载成功
    - download_failed: 下载失败（3 次重试后）
    - insufficient_storage: 存储空间不足
    - switch_failed: 切换失败

    响应：
    {
        "acknowledged": true
    }
    """
    # 记录到数据库
    log = DeviceNotificationLog(
        device_id=notification.device_id,
        notification_type=notification.type,
        message=notification.error_message,
        playlist_id=notification.playlist_id
    )
    db.add(log)

    # 告警（如果是错误类型）
    if notification.type in ['download_failed', 'insufficient_storage', 'switch_failed']:
        logger.warning(
            f"Device alert received: {notification.type}",
            extra={
                "device_id": notification.device_id,
                "playlist_id": notification.playlist_id,
                "error": notification.error_message,
                "event": "device_alert"
            }
        )

    db.commit()

    return {"acknowledged": True}


@router.get("/playlists/available")
async def get_available_playlists(db: Session = Depends(get_db)):
    """
    获取可用播放列表列表（简化版）

    返回所有激活的播放列表，供首次安装时选择

    响应：
    {
        "playlists": [
            {
                "id": 1,
                "name": "企业宣传片",
                "media_count": 5,
                "total_size_mb": 1250
            }
        ]
    }
    """
    # 查询所有激活的播放列表
    playlists = db.query(Playlist).filter(
        Playlist.is_system == True  # 或者添加 is_active 字段
    ).all()

    result = []
    for playlist in playlists:
        # 统计媒体数量和总大小
        items = db.query(PlaylistItem).join(MediaFile).filter(
            PlaylistItem.playlist_id == playlist.id
        ).all()

        media_count = len(items)
        total_size_mb = sum(
            item.media_file.file_size or 0
            for item in items
        ) / (1024 * 1024)

        result.append({
            "id": playlist.id,
            "name": playlist.name,
            "media_count": media_count,
            "total_size_mb": round(total_size_mb, 2)
        })

    return {"playlists": result}


@router.post(
    "/heartbeat",
    summary="播放端心跳上报",
    description="""
播放端定期上报心跳，用于保持在线状态和检查更新。

**请求体：**
```json
{
    "device_id": "550e8400-e29b-41d4-a716-446655440000",
    "device_type": "android_tv",
    "current_playlist_id": 123,
    "last_media_id": 456,
    "status": "playing"
}
```

**响应：**
- `acknowledged`: 确认接收
- `server_time`: 服务器时间
- `playlist_update`: 播放列表更新信息（如有）

**速率限制：** 每设备每分钟最多 10 次请求
""",
    responses={
        200: {"description": "心跳接收成功"},
        429: {"description": "请求过于频繁"}
    }
)
async def player_heartbeat(
    request: HeartbeatRequest,
    db: Session = Depends(get_db)
):
    # 速率限制检查
    if not check_rate_limit(request.device_id):
        logger.warning(f"Rate limit exceeded for device: {request.device_id}")
        raise HTTPException(
            status_code=429,
            detail=f"Too many requests. Maximum {HEARTBEAT_RATE_LIMIT_PER_MINUTE} per minute."
        )

    try:
        # 查找设备
        device = db.query(Device).filter(
            Device.device_id == request.device_id).first()

        if not device:
            # 设备未注册，先注册
            # 生成注册码
            registration_code = generate_registration_code(device_id=request.device_id)

            # 根据设备类型生成名称：Web-XXXXXX 或 Android-XXXXXX
            # device_type 可能是: android_tv, web_browser, android, web 等
            device_type = (request.device_type or "web_browser").lower()
            is_android = device_type.startswith("android")
            prefix = "Android" if is_android else "Web"
            device_name = f"{prefix}-{registration_code}"

            device = Device(
                device_id=request.device_id,
                device_name=device_name,
                registration_code=registration_code,
                device_type=request.device_type,
                status="online",
                last_online=datetime.utcnow(),
                current_playlist_id=request.current_playlist_id,
                last_media_id=request.last_media_id
            )
            db.add(device)
            logger.info(
                f"New device registered via heartbeat: {request.device_id}",
                extra={
                    "device_id": request.device_id,
                    "device_type": request.device_type,
                    "event": "device_registered"
                }
            )
            db.commit()
        else:
            # 更新设备状态
            device.status = "online"
            device.last_online = datetime.utcnow()

            # 更新播放状态（如果有）
            if request.current_playlist_id is not None:
                device.current_playlist_id = request.current_playlist_id

            if request.last_media_id is not None:
                device.last_media_id = request.last_media_id

            # 更新设备类型（如果变化）
            if request.device_type and device.device_type != request.device_type:
                device.device_type = request.device_type

            db.commit()
            logger.debug(
                f"Heartbeat received from device: {request.device_id}",
                extra={
                    "device_id": request.device_id,
                    "playlist_id": request.current_playlist_id,
                    "media_id": request.last_media_id,
                    "status": request.status,
                    "event": "heartbeat_received"
                }
            )

        # 检查是否有播放列表更新需要推送
        playlist_update = await check_playlist_update(db, request.device_id, request.current_playlist_id)

        return {
            "acknowledged": True,
            "server_time": datetime.utcnow().isoformat() + "Z",
            "playlist_update": playlist_update
        }
    except Exception as e:
        db.rollback()
        logger.error(
            f"Heartbeat processing error: {str(e)}",
            extra={
                "device_id": request.device_id,
                "error": str(e),
                "event": "heartbeat_error"
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))


async def check_playlist_update(
    db: Session,
    device_id: str,
    current_playlist_id: Optional[int]
) -> Optional[dict]:
    """
    检查是否有播放列表更新需要推送（P1-3 修复：添加缓存）

    查询是否有该设备的下载任务，如果有且状态为 completed，则返回更新信息
    使用内存缓存减少数据库查询频率（5 分钟有效期）
    """
    import time

    # P1-3 修复：检查缓存
    if device_id in _playlist_update_cache:
        cached_result, cache_time = _playlist_update_cache[device_id]
        if time.time() - cache_time < _PLAYLIST_UPDATE_CACHE_TTL:
            logger.debug(f"Cache hit for device {device_id}")
            return cached_result

    # 缓存未命中，查询数据库
    logger.debug(f"Cache miss for device {device_id}, querying database")

    # 查询已完成的下载任务
    task = db.query(PlaylistDownloadTask).filter(
        PlaylistDownloadTask.device_id == device_id,
        PlaylistDownloadTask.status == 'completed'
    ).first()

    if not task:
        # 缓存空结果，避免频繁查询
        result = None
        _playlist_update_cache[device_id] = (result, time.time())
        return None

    # 获取播放列表信息
    playlist = db.query(Playlist).filter(
        Playlist.id == task.playlist_id).first()
    if not playlist:
        result = None
        _playlist_update_cache[device_id] = (result, time.time())
        return None

    # 统计媒体数量
    items = db.query(PlaylistItem).filter(
        PlaylistItem.playlist_id == playlist.id
    ).all()

    result = {
        "has_update": True,
        "playlist_id": playlist.id,
        "version": playlist.updated_at.isoformat() + "Z" if playlist.updated_at else None,
        "media_count": len(items),
        "name": playlist.name
    }

    # 更新缓存
    _playlist_update_cache[device_id] = (result, time.time())

    return result


@router.get(
    "/playlist/{playlist_id}/detail",
    summary="获取播放列表详情（播放端专用）",
    description="""
获取指定播放列表的完整详情，包含所有媒体项信息。

**响应：**
- `playlist`: 播放列表基本信息
- `items`: 媒体项列表，包含下载 URL 和文件信息
"""
)
def get_player_playlist_detail(
    playlist_id: int,
    db: Session = Depends(get_db)
):
    """
    获取播放列表详情（供播放端下载媒体时使用）

    返回播放列表及其所有媒体项的详细信息
    """
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )

    # 获取播放列表项及媒体信息
    items_query = (
        db.query(
            PlaylistItem.id,
            PlaylistItem.media_id,
            PlaylistItem.display_order,
            PlaylistItem.display_duration,
            MediaFile.file_name,
            MediaFile.file_type,
            MediaFile.file_path,
            MediaFile.converted_path,
            MediaFile.file_size,
            MediaFile.md5_hash
        )
        .join(MediaFile, PlaylistItem.media_id == MediaFile.id)
        .filter(PlaylistItem.playlist_id == playlist_id)
        .order_by(PlaylistItem.display_order)
        .all()
    )

    items = [
        {
            "id": item.id,
            "media_id": item.media_id,
            "display_order": item.display_order,
            "display_duration": item.display_duration,
            "media": {
                "id": item.media_id,
                "file_name": item.file_name,
                "file_type": item.file_type,
                "file_url": f"/api/player/media/{item.media_id}/download",
                "file_size": item.file_size,
                "md5_hash": item.md5_hash
            }
        }
        for item in items_query
    ]

    return {
        "playlist": {
            "id": playlist.id,
            "name": playlist.name,
            "description": playlist.description,
            "version": playlist.updated_at.isoformat() if playlist.updated_at else "1.0.0",
            "is_system": playlist.is_system,
            "item_count": len(items)
        },
        "items": items
    }


@router.get("/status")
async def get_device_status(
    status_filter: Optional[str] = Query(
        None, description="过滤条件：online|offline"),
    db: Session = Depends(get_db)
):
    """
    获取设备状态列表

    查询参数：
    - status_filter: online | offline | None（全部）

    返回：
    [
        {
            "device_id": "xxx",
            "device_name": "Player-xxx",
            "status": "online",
            "last_online": "2026-03-06T10:30:00Z",
            "current_playlist": {
                "id": 123,
                "name": "会议室播放列表"
            },
            "last_media": {
                "id": 456,
                "file_name": "企业宣传片.mp4"
            }
        }
    ]
    """
    query = db.query(Device)

    if status_filter:
        if status_filter == "online":
            # 3 小时内有心跳视为在线（配合 2 小时心跳间隔）
            threshold = datetime.utcnow() - timedelta(hours=DEVICE_ONLINE_THRESHOLD_HOURS)
            query = query.filter(Device.last_online > threshold)
        elif status_filter == "offline":
            threshold = datetime.utcnow() - timedelta(hours=DEVICE_ONLINE_THRESHOLD_HOURS)
            query = query.filter(Device.last_online <= threshold)

    devices = query.all()

    result = []
    for device in devices:
        # 判断是否在线
        time_diff = datetime.utcnow() - device.last_online
        is_online = time_diff.total_seconds() < (DEVICE_ONLINE_THRESHOLD_HOURS * 3600)

        # 获取播放列表信息
        playlist_info = None
        if device.current_playlist_id:
            playlist = db.query(Playlist).filter(
                Playlist.id == device.current_playlist_id
            ).first()
            if playlist:
                playlist_info = {
                    "id": playlist.id,
                    "name": playlist.name
                }

        # 获取媒体信息
        media_info = None
        if device.last_media_id:
            media = db.query(MediaFile).filter(
                MediaFile.id == device.last_media_id
            ).first()
            if media:
                media_info = {
                    "id": media.id,
                    "file_name": media.file_name,
                    "file_type": media.file_type
                }

        result.append({
            "device_id": device.device_id,
            "device_name": device.device_name,
            "device_type": device.device_type,
            "status": "online" if is_online else "offline",
            "last_online": device.last_online.isoformat() + "Z",
            "current_playlist": playlist_info,
            "last_media": media_info
        })

    return result


@router.post("/playlist/{playlist_id}/check")
async def check_playlist_version(
    playlist_id: int,
    request: VersionCheckRequest,
    db: Session = Depends(get_db)
):
    """
    检查播放列表版本

    请求：
    {
        "version": "2026-03-06T10:00:00Z"
    }

    响应：
    {
        "needs_update": true,
        "current_version": "2026-03-06T12:00:00Z"
    }
    """
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    needs_update = playlist.updated_at.isoformat() != request.version

    return {
        "needs_update": needs_update,
        "current_version": playlist.updated_at.isoformat() + "Z"
    }
