/**
 * 离线模式 Hook
 * 处理网络状态检测和离线播放逻辑
 */
import { useState, useCallback, useEffect } from 'react';
import type { PlayerPlaylistItem } from './types';

export interface UseOfflineModeReturn {
  isOnline: boolean;
  wasOffline: boolean;
  lastOnlineTime: Date | null;
  getMediaUrl: (item: PlayerPlaylistItem) => string;
  showOfflineToast: () => void;
}

export const useOfflineMode = (): UseOfflineModeReturn => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [wasOffline, setWasOffline] = useState(false);
  const [lastOnlineTime, setLastOnlineTime] = useState<Date | null>(() => {
    const stored = localStorage.getItem('last_online_time');
    return stored ? new Date(stored) : null;
  });

  // 获取 Android Bridge
  const getAndroidBridge = useCallback(() => {
    return (window as Window & { AndroidBridge?: unknown }).AndroidBridge;
  }, []);

  // 显示离线提示
  const showOfflineToast = useCallback((message: string = '网络已断开，正在使用离线模式...') => {
    const bridge = getAndroidBridge();
    if (bridge && typeof bridge === 'object' && 'showToast' in bridge) {
      (bridge as { showToast: (msg: string) => void }).showToast(message);
    } else {
      // Web 环境：使用 console
      console.warn('Offline:', message);
    }
  }, [getAndroidBridge]);

  // 获取媒体 URL
  const getMediaUrl = useCallback((item: PlayerPlaylistItem): string => {
    // 在线时直接返回原始 URL
    if (isOnline) {
      return item.file_url;
    }

    // 离线时尝试使用本地缓存
    const bridge = getAndroidBridge();
    if (bridge && typeof bridge === 'object' && 'getCachedMediaPath' in bridge) {
      const cachedPath = (bridge as { getCachedMediaPath: (id: string) => string | null }).getCachedMediaPath(item.media_id.toString());
      if (cachedPath) {
        return `file://${cachedPath}`;
      }
    }

    // 尝试使用默认媒体目录
    if (bridge && typeof bridge === 'object') {
      // 对于系统默认媒体
      if (item.file_name.includes('device_info') ||
          item.file_name.includes('system_intro') ||
          item.file_name.includes('company_promo')) {
        return `file:///android_asset/default_media/${item.file_name}`;
      }
    }

    // 返回原始 URL（可能会失败）
    return item.file_url;
  }, [isOnline, getAndroidBridge]);

  // 监听网络状态
  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      setLastOnlineTime(new Date());
      setWasOffline(false);
    };

    const handleOffline = () => {
      setIsOnline(false);
      setWasOffline(true);
      showOfflineToast('网络已断开，正在使用离线模式...');
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [showOfflineToast]);

  // 定期检查网络状态（Android 环境）
  useEffect(() => {
    const bridge = getAndroidBridge();
    if (!bridge) return;

    const checkInterval = setInterval(() => {
      const online = navigator.onLine;
      if (online !== isOnline) {
        setIsOnline(online);
        if (!online) {
          setWasOffline(true);
          showOfflineToast('网络已断开，正在使用离线模式...');
        } else {
          setLastOnlineTime(new Date());
          setWasOffline(false);
        }
      }
    }, 5000);

    return () => {
      clearInterval(checkInterval);
    };
  }, [isOnline, getAndroidBridge, showOfflineToast]);

  // 记录最后在线时间
  useEffect(() => {
    if (isOnline) {
      setLastOnlineTime(new Date());
      localStorage.setItem('last_online_time', new Date().toISOString());
    }
  }, [isOnline]);

  return {
    isOnline,
    wasOffline,
    lastOnlineTime,
    getMediaUrl,
    showOfflineToast: () => showOfflineToast(),
  };
};
