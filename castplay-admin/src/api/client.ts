/**
 * API Client Configuration
 *
 * 统一的 API 请求客户端配置
 * 所有 API 相关的 URL 配置都从这里获取
 */
import axios, { AxiosError, AxiosResponse } from 'axios';

// API 基础 URL - 从环境变量获取，避免硬编码
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001/api';

// 服务器基础 URL（不含 /api 路径，用于媒体文件等静态资源）
export const SERVER_BASE_URL = API_BASE_URL.replace(/\/api$/, '');

// 请求超时时间（毫秒）
const REQUEST_TIMEOUT = 30000;

// 创建 axios 实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: REQUEST_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 可以在这里添加认证 token
    // const token = localStorage.getItem('token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response.data,
  (error: AxiosError<{ error?: string; message?: string }>) => {
    // 统一错误处理
    const errorMessage = error.response?.data?.message
      || error.response?.data?.error
      || error.message
      || '请求失败';

    // 开发环境打印详细错误
    if (import.meta.env.DEV) {
      console.error('API Error:', {
        url: error.config?.url,
        method: error.config?.method,
        status: error.response?.status,
        message: errorMessage,
      });
    }

    return Promise.reject(error);
  }
);

/**
 * 构建媒体文件 URL
 * @param mediaId 媒体文件 ID
 * @param type 'download' | 'thumbnail' | 'converted'
 */
export const getMediaUrl = (mediaId: number, type: 'download' | 'thumbnail' | 'converted' = 'download'): string => {
  if (type === 'converted') {
    return `${API_BASE_URL}/player/media/${mediaId}/converted`;
  }
  return `${API_BASE_URL}/media/${mediaId}/${type}`;
};

/**
 * 构建缩略图 URL
 * @param thumbnailPath 缩略图路径（如 /api/media/1/thumbnail）
 */
export const getThumbnailUrl = (thumbnailPath: string | null): string | null => {
  if (!thumbnailPath) return null;
  // 如果已经是完整 URL，直接返回
  if (thumbnailPath.startsWith('http')) return thumbnailPath;
  // 否则拼接服务器 URL
  return `${SERVER_BASE_URL}${thumbnailPath}`;
};

export default apiClient;
