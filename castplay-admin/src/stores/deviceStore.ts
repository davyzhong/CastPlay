/**
 * Zustand Store - 设备状态管理
 *
 * 集中管理设备列表、选中状态、在线状态等
 */
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { deviceApi, Device } from '../api/device';

interface DeviceState {
  // 数据
  devices: Device[];
  selectedDeviceIds: number[];
  loading: boolean;
  error: string | null;
  pagination: {
    page: number;
    pageSize: number;
    total: number;
  };

  // Actions
  fetchDevices: (page?: number, pageSize?: number) => Promise<void>;
  selectDevice: (id: number) => void;
  deselectDevice: (id: number) => void;
  toggleDeviceSelection: (id: number) => void;
  selectAllDevices: () => void;
  clearSelection: () => void;
  updateDeviceStatus: (deviceId: number, status: 'online' | 'offline') => void;
  refreshDevice: (deviceId: number) => Promise<void>;
}

export const useDeviceStore = create<DeviceState>()(
  devtools(
    (set, get) => ({
      // 初始状态
      devices: [],
      selectedDeviceIds: [],
      loading: false,
      error: null,
      pagination: {
        page: 1,
        pageSize: 20,
        total: 0,
      },

      // 获取设备列表
      fetchDevices: async (page = 1, pageSize = 20) => {
        set({ loading: true, error: null });
        try {
          const response = await deviceApi.list({ page, per_page: pageSize });
          set({
            devices: response.devices,
            pagination: {
              page: response.page,
              pageSize: response.per_page,
              total: response.total,
            },
            loading: false,
          });
        } catch (error: any) {
          set({
            error: error.message || '获取设备列表失败',
            loading: false,
          });
        }
      },

      // 选择设备
      selectDevice: (id) => {
        set((state) => ({
          selectedDeviceIds: state.selectedDeviceIds.includes(id)
            ? state.selectedDeviceIds
            : [...state.selectedDeviceIds, id],
        }));
      },

      // 取消选择
      deselectDevice: (id) => {
        set((state) => ({
          selectedDeviceIds: state.selectedDeviceIds.filter((i) => i !== id),
        }));
      },

      // 切换选择状态
      toggleDeviceSelection: (id) => {
        const { selectedDeviceIds } = get();
        if (selectedDeviceIds.includes(id)) {
          get().deselectDevice(id);
        } else {
          get().selectDevice(id);
        }
      },

      // 全选
      selectAllDevices: () => {
        set((state) => ({
          selectedDeviceIds: state.devices.map((d) => d.id),
        }));
      },

      // 清空选择
      clearSelection: () => {
        set({ selectedDeviceIds: [] });
      },

      // 更新设备状态（WebSocket 推送时调用）
      updateDeviceStatus: (deviceId, status) => {
        set((state) => ({
          devices: state.devices.map((d) =>
            d.id === deviceId ? { ...d, status } : d
          ),
        }));
      },

      // 刷新单个设备
      refreshDevice: async (deviceId) => {
        try {
          const device = await deviceApi.get(deviceId);
          set((state) => ({
            devices: state.devices.map((d) =>
              d.id === deviceId ? device : d
            ),
          }));
        } catch (error) {
          console.error('Failed to refresh device:', error);
        }
      },
    }),
    { name: 'device-store' }
  )
);
