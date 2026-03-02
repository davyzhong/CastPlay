/**
 * Playlist API
 */
import client from './client';

export interface Playlist {
  id: number;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
  item_count: number;
}

export interface PlaylistItem {
  id: number;
  playlist_id: number;
  media_id: number;
  display_order: number;
  display_duration: number;
  media_name?: string;
  media_type?: string;
  media?: {
    id: number;
    file_name: string;
    file_type: string;
    file_size: number;
    thumbnail_path: string | null;
  };
}

export interface PlaylistDetail extends Playlist {
  items: PlaylistItem[];
  devices: Array<{
    device_id: number;
    device_name: string;
    is_active: boolean;
  }>;
}

export interface PlaylistListResponse {
  playlists: Playlist[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export const playlistApi = {
  /**
   * 创建播放列表
   */
  create: (data: { name: string; description?: string }): Promise<{ message: string; playlist: Playlist }> => {
    return client.post('/playlists', data);
  },

  /**
   * 播放列表列表
   */
  list: (params?: { page?: number; per_page?: number }): Promise<PlaylistListResponse> => {
    return client.get('/playlists', { params });
  },

  /**
   * 播放列表详情
   */
  get: (id: number): Promise<PlaylistDetail> => {
    return client.get(`/playlists/${id}`);
  },

  /**
   * 更新播放列表
   */
  update: (id: number, data: { name?: string; description?: string }): Promise<{ message: string; playlist: Playlist }> => {
    return client.put(`/playlists/${id}`, data);
  },

  /**
   * 删除播放列表
   */
  delete: (id: number): Promise<{ message: string }> => {
    return client.delete(`/playlists/${id}`);
  },

  /**
   * 添加媒体到播放列表
   */
  addMedia: (
    playlistId: number,
    data: {
      media_id: number;
      display_duration?: number;
    }
  ): Promise<{ message: string; item: PlaylistItem }> => {
    return client.post(`/playlists/${playlistId}/items`, data);
  },

  /**
   * 从播放列表移除媒体
   */
  removeMedia: (playlistId: number, itemId: number): Promise<{ message: string }> => {
    return client.delete(`/playlists/${playlistId}/items/${itemId}`);
  },

  /**
   * 重新排序播放列表项
   */
  reorderItems: (
    playlistId: number,
    items: Array<{ id: number; order: number }>
  ): Promise<{ message: string }> => {
    return client.put(`/playlists/${playlistId}/items/reorder`, {
      items,
    });
  },

  /**
   * 分配播放列表到设备
   */
  assignToDevice: (playlistId: number, deviceId: number): Promise<{ message: string }> => {
    return client.post(
      `/playlists/${playlistId}/devices/${deviceId}`,
      {}
    );
  },

  /**
   * 取消分配
   */
  unassignFromDevice: (playlistId: number, deviceId: number): Promise<{ message: string }> => {
    return client.delete(
      `/playlists/${playlistId}/devices/${deviceId}`
    );
  },

  /**
   * 激活/停用播放列表
   */
  toggleActive: (
    playlistId: number,
    deviceId: number,
    isActive: boolean
  ): Promise<{ message: string }> => {
    return client.put(
      `/playlists/${playlistId}/devices/${deviceId}/activate`,
      { is_active: isActive }
    );
  },
};
