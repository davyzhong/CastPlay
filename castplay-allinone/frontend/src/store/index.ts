/**
 * Zustand 状态管理
 */
import { create } from 'zustand';
import type { User, Device, MediaFile, Playlist, WebSocketMessage } from '../types';

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

const useStore = create<AppState>((set) => ({
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
