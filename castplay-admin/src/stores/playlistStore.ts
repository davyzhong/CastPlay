import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import api from '../api/client';

// 播放列表类型
interface Playlist {
  id: number;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  items?: PlaylistItem[];
  devices?: PlaylistDevice[];
}

interface PlaylistItem {
  id: number;
  media_id: number;
  media_name: string;
  media_type: string;
  display_order: number;
  display_duration: number;
  status?: string;
  file_url?: string;
}

interface PlaylistDevice {
  device_id: number;
  device_name: string;
  is_active: boolean;
}

// Store 状态类型
interface PlaylistState {
  // 状态
  playlists: Playlist[];
  currentPlaylist: Playlist | null;
  loading: boolean;
  error: string | null;
  total: number;
  page: number;
  pageSize: number;

  // 操作
  fetchPlaylists: (params?: { page?: number; pageSize?: number }) => Promise<void>;
  fetchPlaylistById: (id: number) => Promise<Playlist>;
  createPlaylist: (data: { name: string; description?: string }) => Promise<Playlist>;
  updatePlaylist: (id: number, data: Partial<Playlist>) => Promise<void>;
  deletePlaylist: (id: number) => Promise<void>;
  addItemToPlaylist: (playlistId: number, mediaId: number, duration?: number) => Promise<void>;
  removeItemFromPlaylist: (playlistId: number, itemId: number) => Promise<void>;
  reorderPlaylistItems: (playlistId: number, items: { id: number; order: number }[]) => Promise<void>;
  assignToDevice: (playlistId: number, deviceId: number) => Promise<void>;
  unassignFromDevice: (playlistId: number, deviceId: number) => Promise<void>;
  setCurrentPlaylist: (playlist: Playlist | null) => void;
  clearError: () => void;
}

/**
 * 播放列表状态管理 Store
 */
export const usePlaylistStore = create<PlaylistState>()(
  devtools(
    (set, get) => ({
      // 初始状态
      playlists: [],
      currentPlaylist: null,
      loading: false,
      error: null,
      total: 0,
      page: 1,
      pageSize: 20,

      // 获取播放列表
      fetchPlaylists: async (params = {}) => {
        set({ loading: true, error: null });

        try {
          const { page = get().page, pageSize = get().pageSize } = params;

          const response = await api.get(`/playlists?page=${page}&per_page=${pageSize}`);

          set({
            playlists: response.data.playlists,
            total: response.data.total,
            page: response.data.page,
            loading: false,
          });
        } catch (error: any) {
          set({
            error: error.response?.data?.error || '获取播放列表失败',
            loading: false,
          });
        }
      },

      // 根据 ID 获取播放列表
      fetchPlaylistById: async (id: number) => {
        set({ loading: true, error: null });

        try {
          const response = await api.get(`/playlists/${id}`);
          const playlist = response.data;

          set({ currentPlaylist: playlist, loading: false });
          return playlist;
        } catch (error: any) {
          set({
            error: error.response?.data?.error || '获取播放列表详情失败',
            loading: false,
          });
          throw error;
        }
      },

      // 创建播放列表
      createPlaylist: async (data) => {
        const response = await api.post('/playlists', data);

        // 添加到列表
        set(state => ({
          playlists: [response.data.playlist, ...state.playlists],
          total: state.total + 1,
        }));

        return response.data.playlist;
      },

      // 更新播放列表
      updatePlaylist: async (id, data) => {
        const response = await api.put(`/playlists/${id}`, data);

        // 更新列表中的项
        set(state => ({
          playlists: state.playlists.map(p =>
            p.id === id ? { ...p, ...response.data.playlist } : p
          ),
          currentPlaylist: state.currentPlaylist?.id === id
            ? { ...state.currentPlaylist, ...response.data.playlist }
            : state.currentPlaylist,
        }));
      },

      // 删除播放列表
      deletePlaylist: async (id) => {
        await api.delete(`/playlists/${id}`);

        set(state => ({
          playlists: state.playlists.filter(p => p.id !== id),
          total: state.total - 1,
          currentPlaylist: state.currentPlaylist?.id === id ? null : state.currentPlaylist,
        }));
      },

      // 添加媒体到播放列表
      addItemToPlaylist: async (playlistId, mediaId, duration = 10) => {
        await api.post(`/playlists/${playlistId}/items`, {
          media_id: mediaId,
          display_duration: duration,
        });

        // 刷新当前播放列表
        if (get().currentPlaylist?.id === playlistId) {
          await get().fetchPlaylistById(playlistId);
        }
      },

      // 从播放列表移除媒体
      removeItemFromPlaylist: async (playlistId, itemId) => {
        await api.delete(`/playlists/${playlistId}/items/${itemId}`);

        // 刷新当前播放列表
        if (get().currentPlaylist?.id === playlistId) {
          await get().fetchPlaylistById(playlistId);
        }
      },

      // 重新排序播放列表项
      reorderPlaylistItems: async (playlistId, items) => {
        await api.put(`/playlists/${playlistId}/items/reorder`, { items });

        // 刷新当前播放列表
        if (get().currentPlaylist?.id === playlistId) {
          await get().fetchPlaylistById(playlistId);
        }
      },

      // 分配播放列表到设备
      assignToDevice: async (playlistId, deviceId) => {
        await api.post(`/playlists/${playlistId}/devices/${deviceId}`);

        // 刷新当前播放列表
        if (get().currentPlaylist?.id === playlistId) {
          await get().fetchPlaylistById(playlistId);
        }
      },

      // 取消分配
      unassignFromDevice: async (playlistId, deviceId) => {
        await api.delete(`/playlists/${playlistId}/devices/${deviceId}`);

        // 刷新当前播放列表
        if (get().currentPlaylist?.id === playlistId) {
          await get().fetchPlaylistById(playlistId);
        }
      },

      // 设置当前播放列表
      setCurrentPlaylist: (playlist) => set({ currentPlaylist: playlist }),

      // 清除错误
      clearError: () => set({ error: null }),
    }),
    { name: 'playlist-store' }
  )
);
