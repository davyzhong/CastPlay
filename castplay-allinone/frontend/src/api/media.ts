/**
 * 媒体 API
 */
import apiClient from './client';
import type { MediaFile, PaginatedResponse, ApiResponse } from '../types';

export interface MediaListParams {
  skip?: number;
  limit?: number;
  file_type?: 'image' | 'video' | 'ppt';
  status?: 'ready' | 'processing' | 'failed';
}

// 上传媒体文件
export const uploadMedia = async (file: File, fileType: 'image' | 'video' | 'ppt') => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('file_type', fileType);

  return apiClient.post<ApiResponse<{ media: MediaFile }>>('/media/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

// 获取媒体列表
export const getMediaList = (params: MediaListParams = {}) =>
  apiClient.get<PaginatedResponse<MediaFile>>('/media', { params });

// 获取媒体详情
export const getMedia = (mediaId: number) =>
  apiClient.get<MediaFile>(`/media/${mediaId}`);

// 删除媒体
export const deleteMedia = (mediaId: number) =>
  apiClient.delete(`/media/${mediaId}`);

// 下载媒体
export const downloadMedia = (mediaId: number) => {
  return `/api/media/${mediaId}/download`;
};

// 获取缩略图
export const getThumbnail = (mediaId: number) => {
  return `/api/media/${mediaId}/thumbnail`;
};
