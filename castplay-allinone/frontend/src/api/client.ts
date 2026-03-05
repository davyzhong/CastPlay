/**
 * API 客户端
 * 封装 axios 实例，统一错误处理
 */
import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';

// API 基础 URL
// 后端路由格式: /api/auth/*, /api/devices/* 等
// 开发环境通过 Vite 代理（/api -> http://localhost:8000/api）
// @ts-ignore - Vite 注入的环境变量
const API_BASE_URL = (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_URL) || '/api';

// 创建 axios 实例
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 添加认证 token
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.set('Authorization', `Bearer ${token}`);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error: AxiosError) => {
    // 处理错误
    if (error.response) {
      const status = error.response.status;
      const data = error.response.data as { error?: string; message?: string; detail?: string };

      if (status === 401) {
        // 未授权，清除 token 并跳转到登录
        localStorage.removeItem('token');
        // 避免在登录页面重复跳转
        if (!window.location.pathname.includes('/login')) {
          window.location.href = '/login';
        }
      }

      // 返回标准化的错误格式
      return Promise.reject({
        status,
        message: data?.error || data?.message || data?.detail || '请求失败',
      });
    }

    // 网络错误
    if (!error.response) {
      return Promise.reject({
        message: '网络连接失败，请检查网络设置',
      });
    }

    return Promise.reject(error);
  }
);

export default apiClient;

// 类型安全的 API 方法包装器
// 因为拦截器返回 response.data，所以这里重新定义返回类型
export const api = {
  get: <T>(url: string, config?: object): Promise<T> =>
    apiClient.get(url, config) as Promise<T>,

  post: <T>(url: string, data?: unknown, config?: object): Promise<T> =>
    apiClient.post(url, data, config) as Promise<T>,

  put: <T>(url: string, data?: unknown, config?: object): Promise<T> =>
    apiClient.put(url, data, config) as Promise<T>,

  delete: <T>(url: string, config?: object): Promise<T> =>
    apiClient.delete(url, config) as Promise<T>,
};
