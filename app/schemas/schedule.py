"""
播放列表调度相关 Schemas
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime, time


class ScheduleCreate(BaseModel):
    """创建播放列表调度请求"""

    device_id: int = Field(..., description="目标设备 ID")
    playlist_id: int = Field(..., description="要激活的播放列表 ID")
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}:\d{2}$", description="开始时间 (HH:MM:SS)")
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}:\d{2}$", description="结束时间 (HH:MM:SS)")
    days_of_week: int = Field(default=127, ge=1, le=127, description="星期位掩码 (1-127)")
    enabled: bool = Field(default=True, description="是否启用")
    priority: int = Field(default=0, ge=0, le=1000, description="优先级")

    @field_validator("end_time")
    @classmethod
    def end_time_after_start_time(cls, v: str, info) -> str:
        """验证结束时间必须大于开始时间"""
        if "start_time" in info.data:
            start = info.data["start_time"]
            if v <= start:
                raise ValueError("end_time must be greater than start_time")
        return v


class ScheduleUpdate(BaseModel):
    """更新播放列表调度请求"""

    device_id: Optional[int] = Field(None, description="目标设备 ID")
    playlist_id: Optional[int] = Field(None, description="要激活的播放列表 ID")
    start_time: Optional[str] = Field(
        None, pattern=r"^\d{2}:\d{2}:\d{2}$", description="开始时间 (HH:MM:SS)"
    )
    end_time: Optional[str] = Field(
        None, pattern=r"^\d{2}:\d{2}:\d{2}$", description="结束时间 (HH:MM:SS)"
    )
    days_of_week: Optional[int] = Field(None, ge=1, le=127, description="星期位掩码 (1-127)")
    enabled: Optional[bool] = Field(None, description="是否启用")
    priority: Optional[int] = Field(None, ge=0, le=1000, description="优先级")

    @field_validator("end_time")
    @classmethod
    def end_time_after_start_time(cls, v: Optional[str], info) -> Optional[str]:
        """验证结束时间必须大于开始时间"""
        if v is not None and "start_time" in info.data and info.data["start_time"] is not None:
            start = info.data["start_time"]
            if v <= start:
                raise ValueError("end_time must be greater than start_time")
        return v


class ScheduleConflict(BaseModel):
    """调度冲突信息"""

    schedule_id: int = Field(..., description="冲突的调度 ID")
    playlist_name: str = Field(..., description="播放列表名称")
    overlap: str = Field(..., description="重叠描述")


class ScheduleResponse(BaseModel):
    """播放列表调度响应"""

    id: int
    device_id: int
    playlist_id: int
    playlist_name: Optional[str] = None
    start_time: str
    end_time: str
    days_of_week: int
    days_display: List[str] = []
    enabled: bool
    priority: int
    conflicts: List[ScheduleConflict] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScheduleListResponse(BaseModel):
    """播放列表调度列表响应"""

    schedules: List[ScheduleResponse]
    total: int


class ActiveScheduleResponse(BaseModel):
    """当前激活的调度响应"""

    active_playlist_id: Optional[int] = None
    schedule_id: Optional[int] = None
    schedule_name: Optional[str] = None


class PlayerScheduleData(BaseModel):
    """播放器调度数据（用于设备端）"""

    id: int
    playlist_id: int
    start_time: str
    end_time: str
    days_of_week: int
    enabled: bool
    priority: int


class PlayerSchedulesResponse(BaseModel):
    """播放器调度列表响应（用于设备端离线评估）"""

    schedules: List[PlayerScheduleData]
    default_playlist_id: Optional[int] = None
    server_time: datetime
    timezone: str = "Asia/Shanghai"


def days_to_display(days_of_week: int) -> List[str]:
    """
    将星期位掩码转换为显示列表

    Args:
        days_of_week: 星期位掩码 (1-127)

    Returns:
        星期缩写列表
    """
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    return [day_names[i] for i in range(7) if days_of_week & (1 << i)]
