/**
 * 媒体 API
 */
import { api } from './client';
import type { MediaFile, PaginatedResponse } from '../types';

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
  // 注意：file_type 需要作为 query 参数传递，而不是 form data
  return api.post<{ message: string; media: MediaFile }>(`/media/upload?file_type=${fileType}`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

// 获取媒体列表
export const getMediaList = (params: MediaListParams = {}) =>
  api.get<PaginatedResponse<MediaFile>>('/media', { params });

// 获取媒体详情
export const getMedia = (mediaId: number) =>
  api.get<MediaFile>(`/media/${mediaId}`);

// 删除媒体
export const deleteMedia = (mediaId: number) =>
  api.delete<void>(`/media/${mediaId}`);

// 下载媒体
export const downloadMedia = (mediaId: number) => {
  return `/api/media/${mediaId}/download`;
};

// 获取缩略图
export const getThumbnail = (mediaId: number) => {
  return `/api/media/${mediaId}/thumbnail`;
};

// 获取媒体文件 URL（用于预览）
export const getMediaFileUrl = (mediaId: number) => {
  return `/api/media/${mediaId}/download`;
};

// 重试 PPT 转换
export const retryConversion = (mediaId: number) =>
  api.post<MediaFile>(`/media/${mediaId}/retry`);
