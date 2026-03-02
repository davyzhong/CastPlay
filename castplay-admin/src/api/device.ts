/**
 * Device API
 */
import client from './client';

export interface Device {
  id: number;
  device_id: string;
  device_name: string;
  timezone: string;
  last_online: string | null;
  status: 'online' | 'offline';
  created_at: string;
  updated_at: string;
}

export interface DeviceSchedule {
  id: number;
  device_id: number;
  power_on_time: string | null;
  power_off_time: string | null;
  is_enabled: boolean;
  weekdays: number[];
}

export interface DeviceListParams {
  page?: number;
  per_page?: number;
  status?: 'online' | 'offline';
}

export interface DeviceListResponse {
  devices: Device[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export const deviceApi = {
  /**
   * 创建设备
   */
  create: (data: {
    device_id?: string;
    device_name?: string;
    timezone?: string;
  }): Promise<{ message: string; device: Device }> => {
    return client.post('/devices', data);
  },

  /**
   * 设备注册
   */
  register: (data: {
    device_id: string;
    device_name?: string;
    timezone?: string;
  }): Promise<{ message: string; device: Device }> => {
    return client.post('/devices/register', data);
  },

  /**
   * 设备列表
   */
  list: (params?: DeviceListParams): Promise<DeviceListResponse> => {
    return client.get('/devices', { params });
  },

  /**
   * 设备详情
   */
  get: (id: number): Promise<Device> => {
    return client.get(`/devices/${id}`);
  },

  /**
   * 更新设备
   */
  update: (id: number, data: Partial<Device>): Promise<{ message: string; device: Device }> => {
    return client.put(`/devices/${id}`, data);
  },

  /**
   * 删除设备
   */
  delete: (id: number): Promise<{ message: string }> => {
    return client.delete(`/devices/${id}`);
  },

  /**
   * 设置定时配置
   */
  setSchedule: (
    id: number,
    data: {
      power_on_time?: string;
      power_off_time?: string;
      weekdays?: number[];
      is_enabled?: boolean;
    }
  ): Promise<{ message: string; schedule: DeviceSchedule }> => {
    return client.post(`/devices/${id}/schedule`, data);
  },

  /**
   * 获取定时配置
   */
  getSchedule: (id: number): Promise<DeviceSchedule> => {
    return client.get(`/devices/${id}/schedule`);
  },
};
