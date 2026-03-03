import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import api from '../api/client';

// 媒体文件类型
interface MediaFile {
  id: number;
  file_name: string;
  file_type: 'image' | 'video' | 'ppt';
  file_size: number;
  status: string;
  folder_id: number | null;
  upload_time: string;
  thumbnail_path?: string;
}

// Store 状态类型
interface MediaState {
  // 状态
  mediaList: MediaFile[];
  loading: boolean;
  error: string | null;
  total: number;
  page: number;
  pageSize: number;

  // 操作
  fetchMedia: (params?: { page?: number; pageSize?: number; fileType?: string; folderId?: string }) => Promise<void>;
  uploadMedia: (file: File, fileType: string, folderId?: number) => Promise<MediaFile>;
  deleteMedia: (id: number) => Promise<void>;
  updateMedia: (id: number, data: Partial<MediaFile>) => Promise<void>;
  setPage: (page: number) => void;
  clearError: () => void;
}

/**
 * 媒体文件状态管理 Store
 */
export const useMediaStore = create<MediaState>()(
  devtools(
    (set, get) => ({
      // 初始状态
      mediaList: [],
      loading: false,
      error: null,
      total: 0,
      page: 1,
      pageSize: 20,

      // 获取媒体列表
      fetchMedia: async (params = {}) => {
        set({ loading: true, error: null });

        try {
          const { page = get().page, pageSize = get().pageSize, fileType, folderId } = params;

          const queryParams = new URLSearchParams({
            page: String(page),
            per_page: String(pageSize),
          });

          if (fileType) queryParams.set('file_type', fileType);
          if (folderId !== undefined) queryParams.set('folder_id', folderId);

          const response = await api.get(`/media?${queryParams}`);

          set({
            mediaList: response.data.media,
            total: response.data.total,
            page: response.data.page,
            loading: false,
          });
        } catch (error: any) {
          set({
            error: error.response?.data?.error || '获取媒体列表失败',
            loading: false,
          });
        }
      },

      // 上传媒体文件
      uploadMedia: async (file: File, fileType: string, folderId?: number) => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('file_type', fileType);
        if (folderId) formData.append('folder_id', String(folderId));

        const response = await api.post('/media/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });

        // 刷新列表
        await get().fetchMedia();

        return response.data.media;
      },

      // 删除媒体文件
      deleteMedia: async (id: number) => {
        await api.delete(`/media/${id}`);

        // 从列表中移除
        set(state => ({
          mediaList: state.mediaList.filter(m => m.id !== id),
          total: state.total - 1,
        }));
      },

      // 更新媒体文件
      updateMedia: async (id: number, data: Partial<MediaFile>) => {
        const response = await api.put(`/media/${id}`, data);

        // 更新列表中的项
        set(state => ({
          mediaList: state.mediaList.map(m =>
            m.id === id ? { ...m, ...response.data.media } : m
          ),
        }));
      },

      // 设置页码
      setPage: (page: number) => {
        set({ page });
        get().fetchMedia({ page });
      },

      // 清除错误
      clearError: () => set({ error: null }),
    }),
    { name: 'media-store' }
  )
);
