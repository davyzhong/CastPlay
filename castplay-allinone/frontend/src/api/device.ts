/**
 * 设备 API
 */
import apiClient from './client';
import type { Device, DeviceSchedule, ApiResponse } from '../types';

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
  apiClient.post<ApiResponse<{ device: Device }>>('/devices/register', params);

// 设备心跳
export const deviceHeartbeat = (deviceId: number) =>
  apiClient.put(`/devices/${deviceId}/heartbeat`);

// 获取设备列表
export const getDeviceList = (params: DeviceListParams = {}) =>
  apiClient.get<{ items: Device[]; total: number }>('/devices', { params });

// 获取设备详情
export const getDevice = (deviceId: number) =>
  apiClient.get<Device>(`/devices/${deviceId}`);

// 更新设备
export const updateDevice = (deviceId: number, params: UpdateDeviceParams) =>
  apiClient.put<Device>(`/devices/${deviceId}`, params);

// 删除设备
export const deleteDevice = (deviceId: number) =>
  apiClient.delete(`/devices/${deviceId}`);

// 设置定时配置
export const setDeviceSchedule = (deviceId: number, params: SetScheduleParams) =>
  apiClient.post<ApiResponse<{ schedule: DeviceSchedule }>>(`/devices/${deviceId}/schedule`, params);

// 获取定时配置
export const getDeviceSchedule = (deviceId: number) =>
  apiClient.get<DeviceSchedule>(`/devices/${deviceId}/schedule`);
