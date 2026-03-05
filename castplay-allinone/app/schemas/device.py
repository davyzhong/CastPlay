"""
设备相关 Schemas
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
import re


class DeviceCreate(BaseModel):
    """设备注册/创建请求"""
    device_id: Optional[str] = Field(None, min_length=1, max_length=50, description="设备唯一标识（可选，MAC 注册时自动生成）")
    device_name: str = Field(default="Default Device", max_length=100, description="设备名称")
    timezone: str = Field(default="Asia/Shanghai", description="时区")
    # 新增字段
    mac_address: Optional[str] = Field(None, min_length=17, max_length=17, description="MAC 地址 (XX:XX:XX:XX:XX:XX)")
    ip_address: Optional[str] = Field(None, max_length=45, description="IP 地址")
    registration_code: Optional[str] = Field(None, min_length=1, max_length=20, description="注册码")

    @field_validator('mac_address')
    @classmethod
    def validate_mac_address(cls, v):
        if v is not None:
            # 验证 MAC 地址格式
            pattern = r'^([0-9A-Fa-f]{2}[:]){5}([0-9A-Fa-f]{2})$'
            if not re.match(pattern, v):
                raise ValueError('Invalid MAC address format. Expected XX:XX:XX:XX:XX:XX')
            # 转换为大写
            return v.upper()
        return v


class DeviceUpdate(BaseModel):
    """更新设备请求"""
    device_name: Optional[str] = Field(None, max_length=100)
    timezone: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(online|offline)$")
    playback_speed: Optional[int] = Field(None, ge=1, le=8, description="播放速度 (1, 2, 4, 8)")


class DeviceResponse(BaseModel):
    """设备响应"""
    id: int
    device_id: str
    device_name: str
    timezone: str
    # 新增字段
    mac_address: Optional[str] = None
    ip_address: Optional[str] = None
    registration_code: Optional[str] = None
    playback_speed: int = 1
    # 原有字段
    last_online: Optional[datetime] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DeviceScheduleCreate(BaseModel):
    """定时配置请求"""
    power_on_time: str = Field(..., description="开机时间 HH:MM", pattern=r"^[0-2][0-9]:[0-5][0-9]$")
    power_off_time: str = Field(..., description="关机时间 HH:MM", pattern=r"^[0-2][0-9]:[0-5][0-9]$")
    is_enabled: bool = Field(default=True, description="是否启用")
    weekdays: List[int] = Field(
        default=[1, 2, 3, 4, 5],
        description="工作日: 1=周一, 7=周日",
        min_items=1,
        max_items=7
    )


class DeviceScheduleResponse(BaseModel):
    """定时配置响应"""
    id: int
    device_id: int
    power_on_time: str
    power_off_time: str
    is_enabled: bool
    weekdays: List[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
