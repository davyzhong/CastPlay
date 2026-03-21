"""
播放控制 API 路由
提供 HTTP 接口发送控制指令到设备
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body, Path
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.device import Device
from app.api.auth import get_current_user
from app.models.user import User
from app.utils.logger import logger

router = APIRouter(
    tags=["控制"],
    responses={
        404: {"description": "设备未找到"},
        400: {"description": "设备不在线"}
    }
)


class VolumeRequest(BaseModel):
    """音量调节请求"""
    volume: int = Field(..., ge=0, le=100, description="音量（0-100）")


class SwitchPlaylistRequest(BaseModel):
    """切换播放列表请求"""
    playlist_id: int = Field(..., description="目标播放列表 ID")


@router.post(
    "/{device_id}/pause",
    summary="暂停播放",
    description="""
暂停指定设备的播放。

**需要认证**
"""
)
async def pause_device(
    device_id: int = Path(..., description="设备数据库 ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """暂停设备播放"""
    device = _get_device_or_404(db, device_id)
    await _send_control_command(device, "pause")
    return {"success": True, "message": f"暂停指令已发送到设备 {device.device_name}"}


@router.post(
    "/{device_id}/resume",
    summary="恢复播放",
    description="""
恢复指定设备的播放。

**需要认证**
"""
)
async def resume_device(
    device_id: int = Path(..., description="设备数据库 ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """恢复设备播放"""
    device = _get_device_or_404(db, device_id)
    await _send_control_command(device, "resume")
    return {"success": True, "message": f"恢复播放指令已发送到设备 {device.device_name}"}


@router.post(
    "/{device_id}/volume",
    summary="调节音量",
    description="""
调节指定设备的音量。

**请求体：**
- `volume`: 音量值（0-100）

**需要认证**
"""
)
async def set_device_volume(
    device_id: int = Path(..., description="设备数据库 ID"),
    request: VolumeRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """调节设备音量"""
    device = _get_device_or_404(db, device_id)
    await _send_control_command(device, "volume", volume=request.volume)
    return {"success": True, "message": f"音量调节指令已发送到设备 {device.device_name}", "volume": request.volume}


@router.post(
    "/{device_id}/reload",
    summary="重新加载",
    description="""
通知设备重新加载播放列表。

**需要认证**
"""
)
async def reload_device(
    device_id: int = Path(..., description="设备数据库 ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """重新加载设备"""
    device = _get_device_or_404(db, device_id)
    await _send_control_command(device, "reload")
    return {"success": True, "message": f"重新加载指令已发送到设备 {device.device_name}"}


@router.post(
    "/{device_id}/next",
    summary="下一个媒体",
    description="""
切换到下一个媒体项。

**需要认证**
"""
)
async def next_media(
    device_id: int = Path(..., description="设备数据库 ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """下一个媒体"""
    device = _get_device_or_404(db, device_id)
    await _send_control_command(device, "next")
    return {"success": True, "message": f"下一个指令已发送到设备 {device.device_name}"}


@router.post(
    "/{device_id}/prev",
    summary="上一个媒体",
    description="""
切换到上一个媒体项。

**需要认证**
"""
)
async def prev_media(
    device_id: int = Path(..., description="设备数据库 ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上一个媒体"""
    device = _get_device_or_404(db, device_id)
    await _send_control_command(device, "prev")
    return {"success": True, "message": f"上一个指令已发送到设备 {device.device_name}"}


@router.post(
    "/{device_id}/switch",
    summary="切换播放列表",
    description="""
切换设备当前播放的播放列表。

**请求体：**
- `playlist_id`: 目标播放列表 ID

**需要认证**
"""
)
async def switch_playlist(
    device_id: int = Path(..., description="设备数据库 ID"),
    request: SwitchPlaylistRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """切换播放列表"""
    device = _get_device_or_404(db, device_id)
    await _send_control_command(device, "switch_playlist", playlist_id=request.playlist_id)
    return {"success": True, "message": f"切换播放列表指令已发送到设备 {device.device_name}", "playlist_id": request.playlist_id}


@router.post(
    "/{device_id}/reboot",
    summary="重启设备",
    description="""
通知设备重启（如果设备支持）。

**需要认证**
"""
)
async def reboot_device(
    device_id: int = Path(..., description="设备数据库 ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """重启设备"""
    device = _get_device_or_404(db, device_id)
    await _send_control_command(device, "reboot")
    return {"success": True, "message": f"重启指令已发送到设备 {device.device_name}"}


def _get_device_or_404(db: Session, device_id: int) -> Device:
    """获取设备或返回 404"""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device not found: {device_id}"
        )
    return device


async def _send_control_command(device: Device, action: str, **kwargs):
    """
    发送控制指令到设备

    Args:
        device: 设备对象
        action: 操作类型
        **kwargs: 额外参数
    """
    from app.services.notification import NotificationService

    # 检查设备是否在线（WebSocket 连接）
    if not NotificationService.is_device_online(device.device_id):
        # 设备不在线，只记录日志，仍然尝试发送
        logger.warning(f"Device {device.device_id} may not be connected via WebSocket")

    # 根据 action 类型发送相应的指令
    if action == "pause":
        await NotificationService.send_pause(device.device_id)
    elif action == "resume":
        await NotificationService.send_resume(device.device_id)
    elif action == "volume":
        await NotificationService.send_volume(device.device_id, kwargs.get("volume", 50))
    elif action == "reload":
        await NotificationService.send_reload(device.device_id)
    elif action == "next":
        await NotificationService.send_next(device.device_id)
    elif action == "prev":
        await NotificationService.send_prev(device.device_id)
    elif action == "switch_playlist":
        await NotificationService.send_switch_playlist(device.device_id, kwargs.get("playlist_id"))
    elif action == "reboot":
        await NotificationService.notify_reboot(device.device_id)
    else:
        raise ValueError(f"Unknown control action: {action}")

    logger.info(f"Control command '{action}' sent to device {device.device_id}")
