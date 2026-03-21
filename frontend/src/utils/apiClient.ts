/**
 * 播放器专用 API 客户端
 * 支持动态服务器地址配置
 */
import axios, { AxiosInstance, AxiosError } from 'axios';
import { configStorage } from '../player/services/ConfigStorage';
import type { ServerConfig } from '../player/types/config';
import { STORAGE_KEYS } from '../player/types/config';

/**
 * 播放器 API 客户端类
 * 支持动态配置服务器地址
 */
export class PlayerApiClient {
  private instance: AxiosInstance | null = null;
  private currentBaseUrl: string | null = null;

  /**
   * 构建基础 URL
   */
  private buildBaseUrl(config: ServerConfig): string {
    const protocol = config.protocol || 'https';
    const port = config.port || 8000;
    const portSuffix = (protocol === 'https' && port === 443) ||
                       (protocol === 'http' && port === 80)
                       ? '' : `:${port}`;
    return `${protocol}://${config.address}${portSuffix}/api`;
  }

  /**
   * 获取或创建 axios 实例
   * 如果服务器配置发生变化，会重新创建实例
   */
  getInstance(): AxiosInstance {
    const config = configStorage.get<ServerConfig>(STORAGE_KEYS.SERVER_CONFIG);
    const baseUrl = config ? this.buildBaseUrl(config) : '/api';

    // 如果 URL 没有变化，复用现有实例
    if (this.instance && this.currentBaseUrl === baseUrl) {
      return this.instance;
    }

    // 创建新实例
    this.instance = axios.create({
      baseURL: baseUrl,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // 请求拦截器
    this.instance.interceptors.request.use(
      (config) => {
        console.log(`[PlayerApi] ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // 响应拦截器
    this.instance.interceptors.response.use(
      (response) => {
        return response;
      },
      (error: AxiosError) => {
        const message = error.response?.statusText || error.message;
        console.error(`[PlayerApi] Error: ${message}`);
        return Promise.reject(error);
      }
    );

    this.currentBaseUrl = baseUrl;
    return this.instance;
  }

  /**
   * 重置客户端实例
   */
  reset(): void {
    this.instance = null;
    this.currentBaseUrl = null;
  }

  async get<T>(url: string, config?: object): Promise<T> {
    const response = await this.getInstance().get(url, config);
    return response.data;
  }

  async post<T>(url: string, data?: unknown, config?: object): Promise<T> {
    const response = await this.getInstance().post(url, data, config);
    return response.data;
  }

  async put<T>(url: string, data?: unknown, config?: object): Promise<T> {
    const response = await this.getInstance().put(url, data, config);
    return response.data;
  }

  async delete<T>(url: string, config?: object): Promise<T> {
    const response = await this.getInstance().delete(url, config);
    return response.data;
  }
}

// 导出单例
export const playerApiClient = new PlayerApiClient();

// 导出便捷方法
export const playerApi = {
  get: <T>(url: string, config?: object): Promise<T> => playerApiClient.get(url, config),
  post: <T>(url: string, data?: unknown, config?: object): Promise<T> => playerApiClient.post(url, data, config),
  put: <T>(url: string, data?: unknown, config?: object): Promise<T> => playerApiClient.put(url, data, config),
  delete: <T>(url: string, config?: object): Promise<T> => playerApiClient.delete(url, config),
  reset: () => playerApiClient.reset(),
};
