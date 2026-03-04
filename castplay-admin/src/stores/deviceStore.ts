import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import api from '../api/client';
import { Device as ApiDevice, DeviceListResponse } from '../api/device';

// 重新导出 Device 类型（复用 API 定义）
export type Device = ApiDevice;

interface DeviceSchedule {
  power_on_time?: string;
  power_off_time?: string;
  is_enabled: boolean;
  weekdays: number[];
}

// Store 状态类型
interface DeviceState {
  // 状态
  devices: Device[];
  currentDevice: Device | null;
  loading: boolean;
  error: string | null;
  total: number;
  page: number;
  pageSize: number;

  // 操作
  fetchDevices: (params?: { page?: number; pageSize?: number; status?: string }) => Promise<void>;
  fetchDeviceById: (id: number) => Promise<Device>;
  createDevice: (data: { device_name?: string; timezone?: string }) => Promise<Device>;
  updateDevice: (id: number, data: Partial<Device>) => Promise<void>;
  deleteDevice: (id: number) => Promise<void>;
  setSchedule: (deviceId: number, schedule: Partial<DeviceSchedule>) => Promise<void>;
  setCurrentDevice: (device: Device | null) => void;
  clearError: () => void;
}

/**
 * 设备状态管理 Store
 */
export const useDeviceStore = create<DeviceState>()(
  devtools(
    (set, get) => ({
      // 初始状态
      devices: [],
      currentDevice: null,
      loading: false,
      error: null,
      total: 0,
      page: 1,
      pageSize: 20,

      // 获取设备列表
      fetchDevices: async (params = {}) => {
        set({ loading: true, error: null });

        try {
          const { page = get().page, pageSize = get().pageSize, status } = params;

          const queryParams = new URLSearchParams({
            page: String(page),
            per_page: String(pageSize),
          });

          if (status) queryParams.set('status', status);

          const response: DeviceListResponse = await api.get(`/devices?${queryParams}`);

          set({
            devices: response.devices,
            total: response.total,
            page: response.page,
            loading: false,
          });
        } catch (error: any) {
          set({
            error: error.response?.data?.error || '获取设备列表失败',
            loading: false,
          });
        }
      },

      // 根据 ID 获取设备
      fetchDeviceById: async (id: number) => {
        set({ loading: true, error: null });

        try {
          const device: Device = await api.get(`/devices/${id}`);

          set({ currentDevice: device, loading: false });
          return device;
        } catch (error: any) {
          set({
            error: error.response?.data?.error || '获取设备详情失败',
            loading: false,
          });
          throw error;
        }
      },

      // 创建设备
      createDevice: async (data) => {
        const response = await api.post('/devices', data);

        set(state => ({
          devices: [response.device, ...state.devices],
          total: state.total + 1,
        }));

        return response.device;
      },

      // 更新设备
      updateDevice: async (id, data) => {
        const response = await api.put(`/devices/${id}`, data);

        set(state => ({
          devices: state.devices.map(d =>
            d.id === id ? { ...d, ...response.device } : d
          ),
          currentDevice: state.currentDevice?.id === id
            ? { ...state.currentDevice, ...response.device }
            : state.currentDevice,
        }));
      },

      // 删除设备
      deleteDevice: async (id) => {
        await api.delete(`/devices/${id}`);

        set(state => ({
          devices: state.devices.filter(d => d.id !== id),
          total: state.total - 1,
          currentDevice: state.currentDevice?.id === id ? null : state.currentDevice,
        }));
      },

      // 设置定时配置
      setSchedule: async (deviceId, schedule) => {
        await api.put(`/devices/${deviceId}/schedule`, schedule);

        // 刷新当前设备
        if (get().currentDevice?.id === deviceId) {
          await get().fetchDeviceById(deviceId);
        }
      },

      // 设置当前设备
      setCurrentDevice: (device) => set({ currentDevice: device }),

      // 清除错误
      clearError: () => set({ error: null }),
    }),
    { name: 'device-store' }
  )
);
