/**
 * 配置存储抽象层
 * 统一处理 Web localStorage 和 Android SharedPreferences 的访问
 */

import { STORAGE_KEYS } from '../types/config';

/**
 * 存储适配器接口
 */
interface StorageAdapter {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
}

/**
 * Web localStorage 适配器
 */
class WebStorageAdapter implements StorageAdapter {
  getItem(key: string): string | null {
    try {
      return localStorage.getItem(key);
    } catch (error) {
      console.error('[ConfigStorage] Failed to read from localStorage:', error);
      return null;
    }
  }

  setItem(key: string, value: string): void {
    try {
      localStorage.setItem(key, value);
    } catch (error) {
      console.error('[ConfigStorage] Failed to write to localStorage:', error);
      throw new Error('无法保存配置，本地存储可能已满');
    }
  }

  removeItem(key: string): void {
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.error('[ConfigStorage] Failed to remove from localStorage:', error);
    }
  }
}

/**
 * Android JsBridge 适配器
 */
class AndroidStorageAdapter implements StorageAdapter {
  private cache: Map<string, string> = new Map();

  getItem(key: string): string | null {
    try {
      // 优先使用缓存
      if (this.cache.has(key)) {
        return this.cache.get(key) || null;
      }

      // 从 Android 读取
      const value = window.AndroidBridge?.getConfig(key);
      if (value && value.length > 0) {
        this.cache.set(key, value);
        return value;
      }
      return null;
    } catch (error) {
      console.error('[ConfigStorage] Failed to read from AndroidBridge:', error);
      return null;
    }
  }

  setItem(key: string, value: string): void {
    try {
      window.AndroidBridge?.setConfig(key, value);
      this.cache.set(key, value);
    } catch (error) {
      console.error('[ConfigStorage] Failed to write to AndroidBridge:', error);
      throw new Error('无法保存配置到 Android 设备');
    }
  }

  removeItem(key: string): void {
    try {
      window.AndroidBridge?.setConfig(key, '');
      this.cache.delete(key);
    } catch (error) {
      console.error('[ConfigStorage] Failed to remove from AndroidBridge:', error);
    }
  }
}

/**
 * 配置存储服务
 * 提供统一的配置存储接口，自动检测平台并使用相应的存储后端
 */
export class ConfigStorage {
  private static instance: ConfigStorage;
  private adapter: StorageAdapter;
  private isAndroid: boolean;

  private constructor() {
    this.isAndroid = !!window.AndroidBridge;
    this.adapter = this.isAndroid
      ? new AndroidStorageAdapter()
      : new WebStorageAdapter();

    console.log(`[ConfigStorage] Initialized with ${this.isAndroid ? 'Android' : 'Web'} storage adapter`);
  }

  /**
   * 获取单例实例
   */
  static getInstance(): ConfigStorage {
    if (!ConfigStorage.instance) {
      ConfigStorage.instance = new ConfigStorage();
    }
    return ConfigStorage.instance;
  }

  /**
   * 读取配置
   * @param key 存储键
   * @returns 解析后的对象，如果不存在则返回 null
   */
  get<T>(key: string): T | null {
    const raw = this.adapter.getItem(key);
    if (!raw || raw.length === 0) {
      return null;
    }

    try {
      return JSON.parse(raw) as T;
    } catch (error) {
      console.error(`[ConfigStorage] Failed to parse config for key ${key}:`, error);
      return null;
    }
  }

  /**
   * 保存配置
   * @param key 存储键
   * @param value 要保存的对象
   */
  set<T>(key: string, value: T): void {
    const raw = JSON.stringify(value);
    this.adapter.setItem(key, raw);
    console.log(`[ConfigStorage] Saved config for key ${key}`);
  }

  /**
   * 删除配置
   * @param key 存储键
   */
  remove(key: string): void {
    this.adapter.removeItem(key);
    console.log(`[ConfigStorage] Removed config for key ${key}`);
  }

  /**
   * 检查配置是否存在
   * @param key 存储键
   */
  has(key: string): boolean {
    const value = this.adapter.getItem(key);
    return value !== null && value.length > 0;
  }

  /**
   * 清除所有配置
   */
  clearAll(): void {
    Object.values(STORAGE_KEYS).forEach(key => {
      this.remove(key);
    });
    console.log('[ConfigStorage] Cleared all config');
  }

  /**
   * 获取平台类型
   */
  getPlatform(): 'web' | 'android' {
    return this.isAndroid ? 'android' : 'web';
  }

  /**
   * 复制文本到剪贴板
   * @param text 要复制的文本
   * @returns 是否成功
   */
  async copyToClipboard(text: string): Promise<boolean> {
    try {
      if (this.isAndroid && window.AndroidBridge?.copyToClipboard) {
        return window.AndroidBridge.copyToClipboard(text);
      }

      // Web 标准 API
      await navigator.clipboard.writeText(text);
      return true;
    } catch (error) {
      console.error('[ConfigStorage] Failed to copy to clipboard:', error);

      // 降级方案：使用 execCommand
      try {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        const success = document.execCommand('copy');
        document.body.removeChild(textarea);
        return success;
      } catch {
        return false;
      }
    }
  }
}

// 导出便捷方法
export const configStorage = ConfigStorage.getInstance();
