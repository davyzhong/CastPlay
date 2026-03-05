/**
 * API 客户端
 * 封装 axios 实例，统一错误处理
 */
import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';

// API 基础 URL
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

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
      config.headers = {
        ...config.headers,
        Authorization: `Bearer ${token}`,
      };
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
      const data = error.response.data as any;

      if (status === 401) {
        // 未授权，清除 token 并跳转到登录
        localStorage.removeItem('token');
        window.location.href = '/login';
      }

      return Promise.reject({
        status,
        message: data?.error || data?.message || '请求失败',
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
