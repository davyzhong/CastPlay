/**
 * 服务器配置 Hook
 * 管理服务器地址配置、连接测试和持久化
 */
import { useState, useCallback, useEffect } from 'react';
import { configStorage } from '../services/ConfigStorage';
import { validateAddress, testServerConnection } from '../services/AddressValidator';
import type { ServerConfig, AddressValidationResult, ConnectionStatus } from '../types/config';
import { STORAGE_KEYS } from '../types/config';

interface UseServerConfigResult {
  /** 当前服务器配置 */
  config: ServerConfig | null;
  /** 是否已配置 */
  isConfigured: boolean;
  /** 是否正在测试连接 */
  isTesting: boolean;
  /** 验证地址 */
  validateAddress: (input: string) => AddressValidationResult;
  /** 保存配置 */
  saveConfig: (address: string, port: number) => Promise<{ success: boolean; error?: string }>;
  /** 测试连接 */
  testConnection: () => Promise<{ success: boolean; protocol: 'http' | 'https'; error?: string }>;
  /** 清除配置 */
  clearConfig: () => void;
  /** 更新连接状态 */
  updateConnectionStatus: (status: ConnectionStatus) => void;
}

export function useServerConfig(): UseServerConfigResult {
  const [config, setConfig] = useState<ServerConfig | null>(() => {
    // 首次加载时检查配置
    const stored = configStorage.get<ServerConfig>(STORAGE_KEYS.SERVER_CONFIG);

    // Web 环境开发模式：如果没有配置，使用默认配置
    if (!stored && !window.AndroidBridge) {
      const defaultConfig: ServerConfig = {
        address: 'localhost',
        port: 8001,
        protocol: 'http',
        configuredAt: new Date().toISOString(),
        lastConnectionStatus: 'success',
        lastConnectionAt: new Date().toISOString(),
      };
      console.log('[useServerConfig] Using default config for web development:', defaultConfig);
      configStorage.set(STORAGE_KEYS.SERVER_CONFIG, defaultConfig);
      return defaultConfig;
    }

    return stored;
  });

  const [isTesting, setIsTesting] = useState(false);

  // 监听存储变化（多标签页同步）
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === STORAGE_KEYS.SERVER_CONFIG) {
        const newConfig = configStorage.get<ServerConfig>(STORAGE_KEYS.SERVER_CONFIG);
        setConfig(newConfig);
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  const validateAddressInput = useCallback((input: string): AddressValidationResult => {
    return validateAddress(input);
  }, []);

  const saveConfig = useCallback(async (
    address: string,
    port: number
  ): Promise<{ success: boolean; error?: string }> => {
    // 先测试连接
    setIsTesting(true);
    try {
      const result = await testServerConnection(address, port);
      setIsTesting(false);

      if (!result.success) {
        return { success: false, error: result.error || '无法连接到服务器' };
      }

      // 创建配置对象
      const newConfig: ServerConfig = {
        address,
        port,
        protocol: result.protocol,
        configuredAt: new Date().toISOString(),
        lastConnectionStatus: 'success',
        lastConnectionAt: new Date().toISOString(),
      };

      // 保存到存储
      configStorage.set(STORAGE_KEYS.SERVER_CONFIG, newConfig);
      setConfig(newConfig);

      console.log('[useServerConfig] Config saved:', newConfig);
      return { success: true };
    } catch (error) {
      setIsTesting(false);
      const errorMessage = error instanceof Error ? error.message : '未知错误';
      return { success: false, error: errorMessage };
    }
  }, []);

  const testConnectionFn = useCallback(async () => {
    if (!config) {
      return { success: false, protocol: 'https' as const, error: '未配置服务器地址' };
    }

    setIsTesting(true);
    try {
      const result = await testServerConnection(config.address, config.port);
      setIsTesting(false);

      // 更新连接状态
      const updatedConfig: ServerConfig = {
        ...config,
        lastConnectionStatus: result.success ? 'success' : 'failed',
        lastConnectionAt: new Date().toISOString(),
      };
      configStorage.set(STORAGE_KEYS.SERVER_CONFIG, updatedConfig);
      setConfig(updatedConfig);

      return result;
    } catch (error) {
      setIsTesting(false);
      return {
        success: false,
        protocol: 'https' as const,
        error: error instanceof Error ? error.message : '未知错误',
      };
    }
  }, [config]);

  const clearConfig = useCallback(() => {
    configStorage.remove(STORAGE_KEYS.SERVER_CONFIG);
    setConfig(null);
    console.log('[useServerConfig] Config cleared');
  }, []);

  const updateConnectionStatus = useCallback((status: ConnectionStatus) => {
    if (!config) return;

    const updatedConfig: ServerConfig = {
      ...config,
      lastConnectionStatus: status,
      lastConnectionAt: new Date().toISOString(),
    };
    configStorage.set(STORAGE_KEYS.SERVER_CONFIG, updatedConfig);
    setConfig(updatedConfig);
  }, [config]);

  return {
    config,
    isConfigured: config !== null,
    isTesting,
    validateAddress: validateAddressInput,
    saveConfig,
    testConnection: testConnectionFn,
    clearConfig,
    updateConnectionStatus,
  };
}
