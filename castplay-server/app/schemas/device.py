"""
Pydantic Schemas for Device API
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


# === 基础模型 ===

class DeviceBase(BaseModel):
    """设备基础模型"""
    device_name: Optional[str] = Field(
        None, max_length=128, description="设备名称")
    timezone: str = Field("Asia/Shanghai", max_length=64, description="时区")


class DeviceCreate(DeviceBase):
    """创建设备请求"""
    device_id: Optional[str] = Field(
        None, max_length=64, description="设备ID（可选，不传则自动生成）")
    hardware_id: Optional[str] = Field(
        None, max_length=128, description="硬件标识")


class DeviceUpdate(BaseModel):
    """更新设备请求"""
    device_name: Optional[str] = Field(None, max_length=128)
    timezone: Optional[str] = Field(None, max_length=64)
    status: Optional[str] = Field(None, pattern="^(online|offline)$")


class DeviceRegister(BaseModel):
    """设备注册请求"""
    device_id: Optional[str] = Field(None, max_length=64, description="已有设备ID")
    hardware_id: Optional[str] = Field(
        None, max_length=128, description="硬件标识")
    device_name: Optional[str] = Field(
        None, max_length=128, description="设备名称")
    timezone: str = Field("Asia/Shanghai", max_length=64, description="时区")


# === 响应模型 ===

class DeviceResponse(DeviceBase):
    """设备响应"""
    id: int
    device_id: str
    hardware_id: Optional[str] = None
    api_key: Optional[str] = None
    status: str
    last_online: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DeviceListResponse(BaseModel):
    """设备列表响应"""
    devices: List[DeviceResponse]
    total: int
    page: int
    per_page: int
    pages: int


class DeviceRegisterResponse(BaseModel):
    """设备注册响应"""
    message: str
    device: DeviceResponse
    is_new: bool


# === 定时配置 ===

class ScheduleBase(BaseModel):
    """定时配置基础模型"""
    power_on_time: Optional[str] = Field(
        None, pattern="^\\d{2}:\\d{2}$", description="开机时间 HH:MM")
    power_off_time: Optional[str] = Field(
        None, pattern="^\\d{2}:\\d{2}$", description="关机时间 HH:MM")
    is_enabled: bool = Field(True, description="是否启用")
    weekdays: List[int] = Field([1, 2, 3, 4, 5, 6, 7], description="生效星期 1-7")


class ScheduleCreate(ScheduleBase):
    """创建定时配置"""
    pass


class ScheduleResponse(ScheduleBase):
    """定时配置响应"""
    id: int
    device_id: int

    class Config:
        from_attributes = True
