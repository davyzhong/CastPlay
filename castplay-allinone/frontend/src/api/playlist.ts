/**
 * 播放列表 API
 */
import apiClient from './client';
import type {
  Playlist,
  PlaylistDetail,
  PaginatedResponse,
  PlaylistItem,
  DeviceAssignment,
  ApiResponse
} from '../types';

export interface CreatePlaylistParams {
  name: string;
  description?: string;
}

export interface UpdatePlaylistParams {
  name?: string;
  description?: string;
}

export interface AddItemParams {
  media_id: number;
  display_duration?: number;
}

export interface ReorderItemsParams {
  items: Array<{ id: number; order: number }>;
}

// 创建播放列表
export const createPlaylist = (params: CreatePlaylistParams) =>
  apiClient.post<ApiResponse<{ playlist: Playlist }>>('/playlists', params);

// 获取播放列表列表
export const getPlaylistList = (params: { skip?: number; limit?: number } = {}) =>
  apiClient.get<PaginatedResponse<Playlist>>('/playlists', { params });

// 获取播放列表详情
export const getPlaylistDetail = (playlistId: number) =>
  apiClient.get<PlaylistDetail>(`/playlists/${playlistId}`);

// 更新播放列表
export const updatePlaylist = (playlistId: number, params: UpdatePlaylistParams) =>
  apiClient.put<Playlist>(`/playlists/${playlistId}`, params);

// 删除播放列表
export const deletePlaylist = (playlistId: number) =>
  apiClient.delete(`/playlists/${playlistId}`);

// 添加媒体到播放列表
export const addItemToPlaylist = (playlistId: number, params: AddItemParams) =>
  apiClient.post<ApiResponse<{ item: PlaylistItem }>>(`/playlists/${playlistId}/items`, params);

// 从播放列表移除媒体
export const removeItemFromPlaylist = (playlistId: number, itemId: number) =>
  apiClient.delete(`/playlists/${playlistId}/items/${itemId}`);

// 重新排序播放列表项
export const reorderPlaylistItems = (playlistId: number, params: ReorderItemsParams) =>
  apiClient.put(`/playlists/${playlistId}/items/reorder`, params);

// 分配播放列表到设备
export const assignPlaylistToDevice = (playlistId: number, deviceId: number) =>
  apiClient.post<ApiResponse<{ assignment: DeviceAssignment }>>(
    `/playlists/${playlistId}/devices/${deviceId}`
  );

// 取消设备的播放列表分配
export const unassignPlaylistFromDevice = (playlistId: number, deviceId: number) =>
  apiClient.delete(`/playlists/${playlistId}/devices/${deviceId}`);

// 激活/停用设备上的播放列表
export const togglePlaylistActivation = (
  playlistId: number,
  deviceId: number,
  isActive: boolean
) =>
  apiClient.put(`/playlists/${playlistId}/devices/${deviceId}/activate`, {
    is_active: isActive,
  });
