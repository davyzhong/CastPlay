"""
播放列表调度模型
"""
from sqlalchemy import Column, Integer, Boolean, Time, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin


class PlaylistSchedule(Base, TimestampMixin):
    """
    播放列表调度表
    表示一个时间规则，用于自动切换设备上的播放列表
    """

    __tablename__ = "playlist_schedules"

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # 外键关联
    device_id = Column(
        Integer,
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="目标设备 ID",
    )
    playlist_id = Column(
        Integer,
        ForeignKey("playlists.id", ondelete="CASCADE"),
        nullable=False,
        doc="要激活的播放列表 ID",
    )

    # 调度时间
    start_time = Column(Time, nullable=False, doc="调度开始时间 (HH:MM:SS)")
    end_time = Column(Time, nullable=False, doc="调度结束时间 (HH:MM:SS)，必须大于 start_time")

    # 星期位掩码 (Mon=1, Tue=2, Wed=4, Thu=8, Fri=16, Sat=32, Sun=64)
    days_of_week = Column(
        Integer,
        nullable=False,
        default=127,
        doc="星期位掩码 (1-127)，Mon=1, Tue=2, ..., Sun=64, All=127",
    )

    # 状态和优先级
    enabled = Column(Boolean, nullable=False, default=True, doc="是否启用")
    priority = Column(
        Integer,
        nullable=False,
        default=0,
        doc="优先级，数值越大优先级越高，冲突时高优先级生效",
    )

    # 关系
    device = relationship("Device", backref="playlist_schedules")
    playlist = relationship("Playlist", backref="playlist_schedules")

    def __repr__(self) -> str:
        return f"<PlaylistSchedule(id={self.id}, device_id={self.device_id}, playlist_id={self.playlist_id}, start={self.start_time}, end={self.end_time})>"

    def is_active_on_day(self, day_of_week: int) -> bool:
        """
        检查是否在指定星期几激活

        Args:
            day_of_week: 星期几 (0=Monday, 1=Tuesday, ..., 6=Sunday)

        Returns:
            是否在该天激活
        """
        # 将 Python 的星期几 (0-6) 转换为位掩码值 (1, 2, 4, 8, 16, 32, 64)
        bit_value = 1 << day_of_week
        return bool(self.days_of_week & bit_value)

    def get_days_display(self) -> list[str]:
        """
        获取星期显示列表

        Returns:
            星期缩写列表，如 ["Mon", "Tue", "Wed", "Thu", "Fri"]
        """
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        return [
            day_names[i] for i in range(7) if self.days_of_week & (1 << i)
        ]


# 星期位掩码常量
class DayOfWeek:
    """星期位掩码常量"""

    MONDAY = 1  # 0000001
    TUESDAY = 2  # 0000010
    WEDNESDAY = 4  # 0000100
    THURSDAY = 8  # 0001000
    FRIDAY = 16  # 0010000
    SATURDAY = 32  # 0100000
    SUNDAY = 64  # 1000000

    WEEKDAYS = 31  # 0011111 (Mon-Fri)
    WEEKENDS = 96  # 1100000 (Sat-Sun)
    ALL_WEEK = 127  # 1111111 (All days)
