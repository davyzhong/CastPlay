/**
 * 设备注册码 Hook
 * 管理注册码显示、复制和设备注册状态
 */
import { useState, useCallback, useEffect } from 'react';
import { configStorage } from '../services/ConfigStorage';
import type { DeviceRegistration } from '../types/config';
import { STORAGE_KEYS } from '../types/config';

// 从构建时环境变量获取注册码
// @ts-ignore - Vite 注入的环境变量
const REGISTRATION_CODE: string = typeof import.meta !== 'undefined'
  ? import.meta.env?.VITE_REGISTRATION_CODE || ''
  : '';

interface UseRegistrationCodeResult {
  /** 注册码（从构建配置读取） */
  registrationCode: string;
  /** 设备注册状态 */
  registration: DeviceRegistration;
  /** 设备是否已注册 */
  isRegistered: boolean;
  /** 是否有可用的注册码 */
  hasRegistrationCode: boolean;
  /** 复制注册码到剪贴板 */
  copyRegistrationCode: () => Promise<boolean>;
  /** 完成注册 */
  completeRegistration: (deviceId: string) => void;
  /** 清除注册状态（用于测试） */
  clearRegistration: () => void;
}

export function useRegistrationCode(): UseRegistrationCodeResult {
  const [registration, setRegistration] = useState<DeviceRegistration>(() => {
    return configStorage.get<DeviceRegistration>(STORAGE_KEYS.DEVICE_REGISTRATION) || {
      isRegistered: false,
      deviceId: null,
      registeredAt: null,
      registeredBy: null,
    };
  });

  // 监听存储变化
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === STORAGE_KEYS.DEVICE_REGISTRATION) {
        const newRegistration = configStorage.get<DeviceRegistration>(
          STORAGE_KEYS.DEVICE_REGISTRATION
        );
        if (newRegistration) {
          setRegistration(newRegistration);
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  const copyRegistrationCode = useCallback(async (): Promise<boolean> => {
    if (!REGISTRATION_CODE) {
      console.warn('[useRegistrationCode] No registration code available');
      return false;
    }

    const success = await configStorage.copyToClipboard(REGISTRATION_CODE);
    if (success) {
      console.log('[useRegistrationCode] Registration code copied to clipboard');
    } else {
      console.error('[useRegistrationCode] Failed to copy registration code');
    }
    return success;
  }, []);

  const completeRegistration = useCallback((deviceId: string) => {
    const newRegistration: DeviceRegistration = {
      isRegistered: true,
      deviceId,
      registeredAt: new Date().toISOString(),
      registeredBy: 'user',
    };

    configStorage.set(STORAGE_KEYS.DEVICE_REGISTRATION, newRegistration);
    setRegistration(newRegistration);
    console.log('[useRegistrationCode] Registration completed:', { deviceId });
  }, []);

  const clearRegistration = useCallback(() => {
    configStorage.remove(STORAGE_KEYS.DEVICE_REGISTRATION);
    setRegistration({
      isRegistered: false,
      deviceId: null,
      registeredAt: null,
      registeredBy: null,
    });
    console.log('[useRegistrationCode] Registration cleared');
  }, []);

  return {
    registrationCode: REGISTRATION_CODE,
    registration,
    isRegistered: registration.isRegistered,
    hasRegistrationCode: REGISTRATION_CODE.length > 0,
    copyRegistrationCode,
    completeRegistration,
    clearRegistration,
  };
}
