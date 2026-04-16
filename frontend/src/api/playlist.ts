/**
 * 播放列表 API
 */
import { api } from './client';
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

export interface BatchAddItemsParams {
  media_ids: number[];
  display_duration?: number;
}

export interface BatchAddItemsResponse {
  added_count: number;
  items: PlaylistItem[];
  failed_media_ids: number[];
}

// 创建播放列表
export const createPlaylist = (params: CreatePlaylistParams) =>
  api.post<ApiResponse<{ playlist: Playlist }>>('/playlists/', params);

// 获取播放列表列表
export const getPlaylistList = (params: { skip?: number; limit?: number } = {}) =>
  api.get<PaginatedResponse<Playlist>>('/playlists/', { params });

// 获取播放列表详情
export const getPlaylistDetail = (playlistId: number) =>
  api.get<PlaylistDetail>(`/playlists/${playlistId}`);

// 更新播放列表
export const updatePlaylist = (playlistId: number, params: UpdatePlaylistParams) =>
  api.put<Playlist>(`/playlists/${playlistId}`, params);

// 删除播放列表
export const deletePlaylist = (playlistId: number) =>
  api.delete<void>(`/playlists/${playlistId}`);

// 添加媒体到播放列表
export const addItemToPlaylist = (playlistId: number, params: AddItemParams) =>
  api.post<ApiResponse<{ item: PlaylistItem }>>(`/playlists/${playlistId}/items`, params);

// 从播放列表移除媒体
export const removeItemFromPlaylist = (playlistId: number, itemId: number) =>
  api.delete<void>(`/playlists/${playlistId}/items/${itemId}`);

// 重新排序播放列表项
export const reorderPlaylistItems = (playlistId: number, params: ReorderItemsParams) =>
  api.put<void>(`/playlists/${playlistId}/items/reorder`, params);

// 分配播放列表到设备
export const assignPlaylistToDevice = (playlistId: number, deviceId: number) =>
  api.post<ApiResponse<{ assignment: DeviceAssignment }>>(
    `/playlists/${playlistId}/devices/${deviceId}`
  );

// 取消设备的播放列表分配
export const unassignPlaylistFromDevice = (playlistId: number, deviceId: number) =>
  api.delete<void>(`/playlists/${playlistId}/devices/${deviceId}`);

// 批量添加媒体到播放列表
export const addItemsToPlaylistBatch = (playlistId: number, params: BatchAddItemsParams) =>
  api.post<BatchAddItemsResponse>(`/playlists/${playlistId}/items/batch/`, params);

// 更新播放列表项的显示时长
export const updatePlaylistItem = (
  playlistId: number,
  itemId: number,
  data: { display_duration: number }
) =>
  api.put<PlaylistItem>(`/playlists/${playlistId}/items/${itemId}`, data);
