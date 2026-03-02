/**
 * Media API
 */
import client from './client';

export interface MediaFile {
  id: number;
  file_name: string;
  file_type: 'image' | 'video' | 'ppt';
  file_path: string;
  converted_path: string | null;
  file_size: number;
  duration: number | null;
  thumbnail_path: string | null;
  md5_hash: string | null;
  upload_time: string;
  status: 'processing' | 'ready' | 'failed';
  folder_id: number | null;
  folder_name: string | null;
}

export interface MediaListParams {
  page?: number;
  per_page?: number;
  file_type?: 'image' | 'video' | 'ppt';
  status?: 'processing' | 'ready' | 'failed';
  folder_id?: number | string | null;  // 'null' 表示根目录
}

export interface MediaListResponse {
  media: MediaFile[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export const mediaApi = {
  /**
   * 上传媒体文件
   */
  upload: (file: File, fileType: 'image' | 'video' | 'ppt', folderId?: number | null): Promise<{ message: string; media: MediaFile }> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('file_type', fileType);
    if (folderId !== undefined && folderId !== null) {
      formData.append('folder_id', String(folderId));
    }

    return client.post('/media/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  /**
   * 媒体列表
   */
  list: (params?: MediaListParams): Promise<MediaListResponse> => {
    return client.get('/media', { params });
  },

  /**
   * 媒体详情
   */
  get: (id: number): Promise<MediaFile> => {
    return client.get(`/media/${id}`);
  },

  /**
   * 删除媒体
   */
  delete: (id: number): Promise<{ message: string }> => {
    return client.delete(`/media/${id}`);
  },

  /**
   * 获取下载URL
   */
  getDownloadUrl: (id: number) => {
    return `/api/media/${id}/download`;
  },

  /**
   * 获取缩略图URL
   */
  getThumbnailUrl: (id: number) => {
    return `/api/media/${id}/thumbnail`;
  },
};
