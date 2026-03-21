/**
 * Zustand 状态管理
 */
import { create } from 'zustand';
import type { User, Device, MediaFile, Playlist, WebSocketMessage, PlaylistSchedule } from '../types';
import type { ServerConfig, DeviceRegistration, PlaylistSelection, ConnectionStatus } from '../player/types/config';

// 服务器配置初始值
const defaultDeviceRegistration: DeviceRegistration = {
  isRegistered: false,
  deviceId: null,
  registeredAt: null,
  registeredBy: null,
};

const defaultPlaylistSelection: PlaylistSelection = {
  selectedIds: [],
  updatedAt: new Date().toISOString(),
  userModified: false,
};

interface AppState {
  // 用户状态
  user: User | null;
  setUser: (user: User | null) => void;
  logout: () => void;

  // 设备状态
  devices: Device[];
  setDevices: (devices: Device[]) => void;
  updateDevice: (device: Device) => void;
  removeDevice: (deviceId: number) => void;

  // 媒体状态
  mediaFiles: MediaFile[];
  setMediaFiles: (files: MediaFile[]) => void;
  updateMediaFile: (file: MediaFile) => void;
  removeMediaFile: (mediaId: number) => void;

  // 播放列表状态
  playlists: Playlist[];
  setPlaylists: (playlists: Playlist[]) => void;
  addPlaylist: (playlist: Playlist) => void;
  updatePlaylist: (playlist: Playlist) => void;
  removePlaylist: (playlistId: number) => void;

  // 调度状态
  schedules: PlaylistSchedule[];
  setSchedules: (schedules: PlaylistSchedule[]) => void;
  addSchedule: (schedule: PlaylistSchedule) => void;
  updateSchedule: (schedule: PlaylistSchedule) => void;
  removeSchedule: (scheduleId: number) => void;

  // 播放器配置状态 (新增)
  serverConfig: ServerConfig | null;
  setServerConfig: (config: Omit<ServerConfig, 'configuredAt' | 'lastConnectionStatus'>) => void;
  updateConnectionStatus: (status: ConnectionStatus) => void;
  deviceRegistration: DeviceRegistration;
  setDeviceRegistration: (registration: DeviceRegistration) => void;
  setRegistrationComplete: (deviceId: string) => void;
  playlistSelection: PlaylistSelection;
  setPlaylistSelection: (ids: number[], userModified: boolean) => void;
  clearAllConfig: () => void;

  // WebSocket 消息
  wsMessages: WebSocketMessage[];
  addWsMessage: (message: WebSocketMessage) => void;

  // 加载状态
  isLoading: boolean;
  setLoading: (loading: boolean) => void;

  // 通知
  notification: { message: string; type: 'success' | 'error' | 'info' } | null;
  setNotification: (notification: { message: string; type: 'success' | 'error' | 'info' }) => void;
}

const useStore = create<AppState>((set, _get) => ({
  // 用户状态
  user: null,
  setUser: (user) => set({ user }),
  logout: () => {
    set({ user: null });
    window.location.href = '/login';
  },

  // 设备状态
  devices: [],
  setDevices: (devices) => set({ devices }),
  updateDevice: (device) =>
    set((state) => ({
      devices: state.devices.map((d) => (d.id === device.id ? device : d)),
    })),
  removeDevice: (deviceId) =>
    set((state) => ({
      devices: state.devices.filter((d) => d.id !== deviceId),
    })),

  // 媒体状态
  mediaFiles: [],
  setMediaFiles: (files) => set({ mediaFiles: files }),
  updateMediaFile: (file) =>
    set((state) => ({
      mediaFiles: state.mediaFiles.map((m) => (m.id === file.id ? file : m)),
    })),
  removeMediaFile: (mediaId) =>
    set((state) => ({
      mediaFiles: state.mediaFiles.filter((m) => m.id !== mediaId),
    })),

  // 播放列表状态
  playlists: [],
  setPlaylists: (playlists) => set({ playlists }),
  addPlaylist: (playlist) =>
    set((state) => ({ playlists: [...state.playlists, playlist] })),
  updatePlaylist: (playlist) =>
    set((state) => ({
      playlists: state.playlists.map((p) => (p.id === playlist.id ? playlist : p)),
    })),
  removePlaylist: (playlistId) =>
    set((state) => ({
      playlists: state.playlists.filter((p) => p.id !== playlistId),
    })),

  // 调度状态
  schedules: [],
  setSchedules: (schedules) => set({ schedules }),
  addSchedule: (schedule) =>
    set((state) => ({ schedules: [...state.schedules, schedule] })),
  updateSchedule: (schedule) =>
    set((state) => ({
      schedules: state.schedules.map((s) => (s.id === schedule.id ? schedule : s)),
    })),
  removeSchedule: (scheduleId) =>
    set((state) => ({
      schedules: state.schedules.filter((s) => s.id !== scheduleId),
    })),

  // 播放器配置状态 (新增)
  serverConfig: null,
  setServerConfig: (config) =>
    set({
      serverConfig: {
        ...config,
        configuredAt: new Date().toISOString(),
        lastConnectionStatus: 'pending' as ConnectionStatus,
        lastConnectionAt: null,
      },
    }),
  updateConnectionStatus: (status) =>
    set((state) => ({
      serverConfig: state.serverConfig
        ? {
            ...state.serverConfig,
            lastConnectionStatus: status,
            lastConnectionAt: new Date().toISOString(),
          }
        : null,
    })),

  deviceRegistration: defaultDeviceRegistration,
  setDeviceRegistration: (registration) => set({ deviceRegistration: registration }),
  setRegistrationComplete: (deviceId) =>
    set({
      deviceRegistration: {
        isRegistered: true,
        deviceId,
        registeredAt: new Date().toISOString(),
        registeredBy: 'user',
      },
    }),

  playlistSelection: defaultPlaylistSelection,
  setPlaylistSelection: (ids, userModified) =>
    set({
      playlistSelection: {
        selectedIds: ids,
        updatedAt: new Date().toISOString(),
        userModified,
      },
    }),

  clearAllConfig: () =>
    set({
      serverConfig: null,
      deviceRegistration: defaultDeviceRegistration,
      playlistSelection: defaultPlaylistSelection,
    }),

  // WebSocket 消息
  wsMessages: [],
  addWsMessage: (message) =>
    set((state) => ({
      wsMessages: [...state.wsMessages.slice(-50), message], // 保留最近50条消息
    })),

  // 加载状态
  isLoading: false,
  setLoading: (loading) => set({ isLoading: loading }),

  // 通知
  notification: null,
  setNotification: (notification) => set({ notification }),
}));

export default useStore;
export { useStore };
