/**
 * 设备 API
 */
import { api } from './client';
import type { Device, DeviceSchedule, DevicePlaylist, ApiResponse } from '../types';

export interface DeviceListParams {
  skip?: number;
  limit?: number;
  status?: 'online' | 'offline';
}

export interface CreateDeviceParams {
  device_id: string;
  device_name?: string;
  timezone?: string;
}

export interface UpdateDeviceParams {
  device_name?: string;
  timezone?: string;
  status?: 'online' | 'offline';
}

export interface SetScheduleParams {
  power_on_time: string;
  power_off_time: string;
  is_enabled: boolean;
  weekdays: number[];
}

// 设备注册
export const registerDevice = (params: CreateDeviceParams) =>
  api.post<ApiResponse<{ device: Device }>>('/devices/register', params);

// 设备心跳
export const deviceHeartbeat = (deviceId: number) =>
  api.put<void>(`/devices/${deviceId}/heartbeat`);

// 获取设备列表
export const getDeviceList = (params: DeviceListParams = {}) =>
  api.get<{ items: Device[]; total: number }>('/devices/', { params });

// 获取设备详情
export const getDevice = (deviceId: number) =>
  api.get<Device>(`/devices/${deviceId}`);

// 更新设备
export const updateDevice = (deviceId: number, params: UpdateDeviceParams) =>
  api.put<Device>(`/devices/${deviceId}`, params);

// 删除设备
export const deleteDevice = (deviceId: number) =>
  api.delete<void>(`/devices/${deviceId}`);

// 设置定时配置
export const setDeviceSchedule = (deviceId: number, params: SetScheduleParams) =>
  api.post<ApiResponse<{ schedule: DeviceSchedule }>>(`/devices/${deviceId}/schedule`, params);

// 获取定时配置
export const getDeviceSchedule = (deviceId: number) =>
  api.get<DeviceSchedule>(`/devices/${deviceId}/schedule`);

// 获取设备关联的播放列表
export const getDevicePlaylists = (deviceId: number) =>
  api.get<{ device_id: number; playlists: DevicePlaylist[] }>(`/devices/${deviceId}/playlists`);

// 禁用/启用设备
export const toggleDeviceDisabled = (deviceId: number, isDisabled: boolean) =>
  api.put<Device>(`/devices/${deviceId}/disable`, { is_disabled: isDisabled });

// 清理无效设备
export const cleanupInvalidDevices = () =>
  api.post<{ deleted_count: number; message: string }>('/devices/cleanup');
