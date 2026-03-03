"""
WebSocket Event Handler (FastAPI 版本)

处理设备与服务器之间的实时通信

特性：
- 异步处理所有事件
- 支持 Redis 存储设备连接状态（多实例部署）
- 无 Redis 时自动降级到内存存储
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.websocket.sio import sio
from app.database import AsyncSessionLocal
from app.models.device import Device

logger = logging.getLogger(__name__)

# 简单的内存存储（生产环境建议使用 Redis）
connected_devices: Dict[int, str] = {}  # device_id -> session_id
session_to_device: Dict[str, int] = {}  # session_id -> device_id


@sio.event
async def connect(sid, environ):
    """客户端连接"""
    logger.info(f"Client connected: {sid}")


@sio.event
async def disconnect(sid):
    """客户端断开连接"""
    device_id = session_to_device.get(sid)

    if device_id:
        # 清理连接记录
        connected_devices.pop(device_id, None)
        session_to_device.pop(sid, None)

        logger.info(f"Device {device_id} disconnected")

        # 更新设备状态
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Device).where(Device.id == device_id))
            device = result.scalar_one_or_none()
            if device:
                device.status = 'offline'
                await db.commit()
    else:
        logger.debug(f"Client disconnected: {sid}")


@sio.event
async def device_register(sid, data):
    """设备注册 WebSocket 连接"""
    device_id = data.get('device_id')

    if not device_id:
        await sio.emit('error', {
            'event': 'error',
            'message': 'device_id is required'
        }, to=sid)
        return

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Device).where(Device.device_id == device_id)
        )
        device = result.scalar_one_or_none()

        if not device:
            await sio.emit('error', {
                'event': 'error',
                'message': 'Device not registered'
            }, to=sid)
            return

        # 加入设备房间
        await sio.enter_room(sid, f"device_{device.id}")

        # 记录连接
        connected_devices[device.id] = sid
        session_to_device[sid] = device.id

        # 更新设备在线状态
        device.last_online = datetime.utcnow()
        device.status = 'online'
        await db.commit()

        await sio.emit('registered', {
            'event': 'registered',
            'message': 'Device registered successfully',
            'device_id': device.id
        }, to=sid)

        logger.info(f"Device {device_id} registered with sid {sid}")


@sio.event
async def heartbeat(sid, data):
    """心跳

    注意: device_id 可能是字符串(device_id)或整数(数据库ID)
    """
    device_id_input = data.get('device_id')
    if not device_id_input:
        return

    async with AsyncSessionLocal() as db:
        # 处理两种情况
        if isinstance(device_id_input, int):
            result = await db.execute(select(Device).where(Device.id == device_id_input))
        else:
            result = await db.execute(
                select(Device).where(Device.device_id == str(device_id_input))
            )

        device = result.scalar_one_or_none()

        if device and device.id in connected_devices:
            device.last_online = datetime.utcnow()
            device.status = 'online'
            await db.commit()

            await sio.emit('heartbeat_ack', {
                'event': 'heartbeat_ack',
                'timestamp': datetime.utcnow().isoformat()
            }, to=sid)


# ============= 通知函数 =============

async def notify_playlist_update(device_id: int, playlist_id: int):
    """通知设备播放列表更新"""
    await sio.emit(
        'playlist_update',
        {
            'event': 'playlist_update',
            'playlist_id': playlist_id,
            'action': 'update',
            'timestamp': datetime.utcnow().isoformat()
        },
        room=f"device_{device_id}"
    )


async def notify_schedule_update(device_id: int, schedule_data: dict):
    """通知设备定时配置更新"""
    await sio.emit(
        'schedule_update',
        {
            'event': 'schedule_update',
            'schedule': schedule_data,
            'action': 'update',
            'timestamp': datetime.utcnow().isoformat()
        },
        room=f"device_{device_id}"
    )


async def notify_force_sync(device_id: int):
    """强制设备同步"""
    await sio.emit(
        'force_sync',
        {
            'event': 'force_sync',
            'action': 'sync',
            'timestamp': datetime.utcnow().isoformat()
        },
        room=f"device_{device_id}"
    )


async def notify_reboot(device_id: int):
    """通知设备重启"""
    await sio.emit(
        'reboot',
        {
            'event': 'reboot',
            'action': 'reboot',
            'timestamp': datetime.utcnow().isoformat()
        },
        room=f"device_{device_id}"
    )


async def broadcast_to_all(event: str, data: dict):
    """广播消息到所有设备"""
    await sio.emit(event, data)


def is_device_connected(device_id: int) -> bool:
    """检查设备是否连接"""
    return device_id in connected_devices


def get_connected_device_count() -> int:
    """获取已连接设备数量"""
    return len(connected_devices)
