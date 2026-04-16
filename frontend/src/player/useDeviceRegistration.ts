/**
 * 设备注册 Hook
 * 处理设备注册逻辑，支持 MAC 地址注册和传统 device_id 注册
 */
import { useState, useCallback, useEffect } from 'react';
import { playerApi } from '../utils/apiClient';
import type { PlayerDeviceInfo } from './types';

// 模拟 MAC 地址生成（固定格式用于 Web 端）
const generateMockMac = (): string => {
  const hexDigits = '0123456789ABCDEF';
  const parts: string[] = [];
  for (let i = 0; i < 6; i++) {
    let part = '';
    for (let j = 0; j < 2; j++) {
      part += hexDigits[Math.floor(Math.random() * hexDigits.length)];
    }
    parts.push(part);
  }
  return parts.join(':');
};

// 模拟注册码生成
const generateMockRegistrationCode = (macAddress: string): string => {
  const cleanMac = macAddress.replace(/:/g, '').toUpperCase();
  let hash = 0;
  for (let i = 0; i < cleanMac.length; i++) {
    hash = ((hash << 5) - hash) + cleanMac.charCodeAt(i);
    hash = hash & hash;
  }
  const code = Math.abs(hash).toString(16).toUpperCase().padStart(12, '0').slice(0, 12);
  return `CP-${code.slice(0, 4)}-${code.slice(4, 8)}-${code.slice(8, 12)}`;
};

export interface UseDeviceRegistrationReturn {
  deviceInfo: PlayerDeviceInfo | null;
  isRegistered: boolean;
  isLoading: boolean;
  error: string | null;
  register: () => Promise<void>;
  checkRegistration: () => Promise<boolean>;
}

export const useDeviceRegistration = (): UseDeviceRegistrationReturn => {
  const [deviceInfo, setDeviceInfo] = useState<PlayerDeviceInfo | null>(null);
  const [isRegistered, setIsRegistered] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 获取 Android Bridge
  const getAndroidBridge = useCallback(() => {
    return window.AndroidBridge;
  }, []);

  // 获取设备信息
  const getDeviceInfo = useCallback(() => {
    const bridge = getAndroidBridge();

    if (bridge) {
      return {
        macAddress: bridge.getMacAddress(),
        ipAddress: bridge.getIPAddress() || '0.0.0.0',
        deviceId: bridge.getDeviceId(),
        registrationCode: bridge.getRegistrationCode(),
        timezone: bridge.getLocalTimezone() || Intl.DateTimeFormat().resolvedOptions().timeZone,
      };
    }

    // Web 环境模拟
    const mockMac = generateMockMac();
    return {
      macAddress: mockMac,
      ipAddress: '0.0.0.0',
      deviceId: null,
      registrationCode: generateMockRegistrationCode(mockMac),
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    };
  }, [getAndroidBridge]);

  // 检查是否已注册（从本地存储）
  const checkRegistration = useCallback(async (): Promise<boolean> => {
    const storedDevice = localStorage.getItem('player_device_info');
    if (storedDevice) {
      try {
        const info = JSON.parse(storedDevice) as PlayerDeviceInfo;
        setDeviceInfo(info);
        setIsRegistered(true);
        return true;
      } catch {
        localStorage.removeItem('player_device_info');
      }
    }
    return false;
  }, []);

  // 注册设备
  const register = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const deviceData = getDeviceInfo();
      const bridge = getAndroidBridge();
      const isAndroid = !!bridge;

      // 生成或获取 device_id
      let deviceId = deviceData.deviceId;
      if (!deviceId) {
        if (isAndroid) {
          // Android 设备使用存储的 device_id
          const storedDeviceId = localStorage.getItem('player_device_id');
          if (storedDeviceId) {
            deviceId = storedDeviceId;
          }
        } else {
          // Web 端使用 UUID 生成唯一 device_id
          // 优先从 localStorage 读取已保存的 device_id（保持会话持久性）
          let storedDeviceId = localStorage.getItem('player_device_id');
          if (!storedDeviceId) {
            // 生成新的 UUID v4 格式 device_id
            storedDeviceId = `web-${crypto.randomUUID()}`;
            localStorage.setItem('player_device_id', storedDeviceId);
          }
          deviceId = storedDeviceId;
        }
      }

      // 构建注册请求
      const payload: Record<string, unknown> = {
        device_id: deviceId,
        device_name: 'Default Device', // 让后端根据 device_type 生成正确的名称
        device_type: isAndroid ? 'android_tv' : 'web_browser',
        timezone: deviceData.timezone,
      };

      if (deviceData.macAddress) {
        payload.mac_address = deviceData.macAddress;
        payload.ip_address = deviceData.ipAddress;
      }

      const response = await playerApi.post<{ id: number; device_id: string; device_name: string; timezone: string; mac_address?: string; ip_address?: string; registration_code: string; playback_speed?: number }>('/devices/register', payload);
      const registeredDevice: PlayerDeviceInfo = {
        id: response.id,
        device_id: response.device_id,
        device_name: response.device_name,
        timezone: response.timezone,
        mac_address: response.mac_address,
        ip_address: response.ip_address,
        registration_code: response.registration_code,
        playback_speed: response.playback_speed || 1,
      };

      // 保存到本地存储
      localStorage.setItem('player_device_info', JSON.stringify(registeredDevice));
      setDeviceInfo(registeredDevice);
      setIsRegistered(true);
    } catch (err) {
      const errorMessage = err instanceof Error
        ? err.message
        : '注册失败';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [getDeviceInfo, getAndroidBridge]);

  // 初始化时检查注册状态
  useEffect(() => {
    checkRegistration();
  }, [checkRegistration]);

  return {
    deviceInfo,
    isRegistered,
    isLoading,
    error,
    register,
    checkRegistration,
  };
};
