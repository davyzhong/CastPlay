/**
 * 调度 API
 */
import { api } from './client';
import type {
  PlaylistSchedule,
  ScheduleCreateParams,
  ScheduleUpdateParams,
  ScheduleListResponse,
  ActiveScheduleResponse,
} from '../types';

// 获取设备的调度列表
export const getSchedules = (deviceId: number) =>
  api.get<ScheduleListResponse>(`/schedules/`, { params: { device_id: deviceId } });

// 获取单个调度详情
export const getSchedule = (scheduleId: number) =>
  api.get<PlaylistSchedule>(`/schedules/${scheduleId}`);

// 创建调度
export const createSchedule = (params: ScheduleCreateParams) =>
  api.post<PlaylistSchedule>(`/schedules/`, params);

// 更新调度
export const updateSchedule = (scheduleId: number, params: ScheduleUpdateParams) =>
  api.put<PlaylistSchedule>(`/schedules/${scheduleId}`, params);

// 删除调度
export const deleteSchedule = (scheduleId: number) =>
  api.delete<void>(`/schedules/${scheduleId}`);

// 获取当前激活的调度
export const getActiveSchedule = (deviceId: number) =>
  api.get<ActiveScheduleResponse>(`/schedules/active`, { params: { device_id: deviceId } });

// 获取播放端调度数据（用于离线评估）
export const getPlayerSchedules = (deviceUuid: string) =>
  api.get(`/player/${deviceUuid}/schedules`);

// 辅助函数：将星期列表转换为位掩码
export const daysToBitmask = (days: number[]): number => {
  let bitmask = 0;
  for (const day of days) {
    if (day >= 0 && day <= 6) {
      bitmask |= 1 << day;
    }
  }
  return bitmask;
};

// 辅助函数：将位掩码转换为星期列表
export const bitmaskToDays = (bitmask: number): number[] => {
  const days: number[] = [];
  for (let i = 0; i < 7; i++) {
    if (bitmask & (1 << i)) {
      days.push(i);
    }
  }
  return days;
};

// 辅助函数：获取星期显示名称
export const getDaysDisplay = (bitmask: number): string[] => {
  const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  return dayNames.filter((_, i) => bitmask & (1 << i));
};
