/**
 * 媒体缓存 Hook
 * 处理媒体文件的下载、缓存和离线访问
 */
import { useState, useCallback, useEffect } from 'react';
import type { PlayerPlaylistItem, CachedMediaInfo, CacheStatus } from './types';

export interface UseMediaCacheReturn {
  cachedMedia: Map<number, CachedMediaInfo>;
  downloadMedia: (item: PlayerPlaylistItem) => Promise<boolean>;
  getMediaUrl: (item: PlayerPlaylistItem) => string;
  isCached: (mediaId: number) => boolean;
  getCacheProgress: (mediaId: number) => number;
  preloadPlaylist: (items: PlayerPlaylistItem[]) => Promise<void>;
  clearCache: () => void;
}

export const useMediaCache = (isOnline: boolean = true): UseMediaCacheReturn => {
  const [cachedMedia, setCachedMedia] = useState<Map<number, CachedMediaInfo>>(new Map());

  // 获取 Android Bridge
  const getAndroidBridge = useCallback(() => {
    return window.AndroidBridge;
  }, []);

  // 检查媒体是否已缓存
  const isCached = useCallback((mediaId: number): boolean => {
    const bridge = getAndroidBridge();
    if (bridge) {
      return bridge.isMediaCached(mediaId.toString());
    }

    // Web 环境：检查内存缓存
    return cachedMedia.has(mediaId) && cachedMedia.get(mediaId)?.status === 'completed';
  }, [cachedMedia, getAndroidBridge]);

  // 获取缓存进度
  const getCacheProgress = useCallback((mediaId: number): number => {
    const bridge = getAndroidBridge();
    if (bridge) {
      return bridge.getDownloadProgress(mediaId.toString());
    }

    // Web 环境
    const info = cachedMedia.get(mediaId);
    return info?.progress || 0;
  }, [cachedMedia, getAndroidBridge]);

  // 获取媒体 URL（优先使用缓存）
  const getMediaUrl = useCallback((item: PlayerPlaylistItem): string => {
    // 在线时直接返回原始 URL
    if (isOnline) {
      return item.file_url;
    }

    // 离线时尝试使用缓存
    const bridge = getAndroidBridge();
    if (bridge) {
      const cachedPath = bridge.getCachedMediaPath(item.media_id.toString());
      if (cachedPath) {
        return `file://${cachedPath}`;
      }
    }

    // Web 环境：检查 Cache API
    const info = cachedMedia.get(item.media_id);
    if (info?.status === 'completed' && info.local_path) {
      return info.local_path;
    }

    // 最后尝试使用原始 URL（可能会失败）
    return item.file_url;
  }, [isOnline, cachedMedia, getAndroidBridge]);

  // 下载媒体文件
  const downloadMedia = useCallback(async (item: PlayerPlaylistItem): Promise<boolean> => {
    const bridge = getAndroidBridge();

    // 更新状态为下载中
    setCachedMedia(prev => {
      const newMap = new Map(prev);
      newMap.set(item.media_id, {
        media_id: item.media_id,
        local_path: '',
        status: 'downloading' as CacheStatus,
        progress: 0,
      });
      return newMap;
    });

    if (bridge) {
      // Android 环境：调用原生下载
      bridge.downloadMedia(item.file_url, item.media_id.toString());

      // 轮询下载进度
      return new Promise((resolve) => {
        const checkProgress = setInterval(() => {
          const progress = bridge.getDownloadProgress(item.media_id.toString());

          // 更新进度
          setCachedMedia(prev => {
            const newMap = new Map(prev);
            const info = newMap.get(item.media_id);
            if (info) {
              info.progress = progress;
            }
            return newMap;
          });

          if (progress >= 100) {
            clearInterval(checkProgress);
            setCachedMedia(prev => {
              const newMap = new Map(prev);
              const info = newMap.get(item.media_id);
              if (info) {
                info.status = 'completed';
                info.local_path = bridge.getCachedMediaPath(item.media_id.toString()) || '';
              }
              return newMap;
            });
            resolve(true);
          }
        }, 500);

        // 设置超时
        setTimeout(() => {
          clearInterval(checkProgress);
          resolve(false);
        }, 60000);
      });
    } else {
      // Web 环境：使用 Cache API
      try {
        const cache = await caches.open('media-cache');
        await cache.add(item.file_url);

        const response = await fetch(item.file_url);
        const blob = await response.blob();
        const localUrl = URL.createObjectURL(blob);

        setCachedMedia(prev => {
          const newMap = new Map(prev);
          newMap.set(item.media_id, {
            media_id: item.media_id,
            local_path: localUrl,
            status: 'completed',
            progress: 100,
          });
          return newMap;
        });

        return true;
      } catch {
        setCachedMedia(prev => {
          const newMap = new Map(prev);
          newMap.set(item.media_id, {
            media_id: item.media_id,
            local_path: '',
            status: 'failed',
            progress: 0,
          });
          return newMap;
        });
        return false;
      }
    }
  }, [getAndroidBridge]);

  // 预加载播放列表中的所有媒体
  const preloadPlaylist = useCallback(async (items: PlayerPlaylistItem[]) => {
    for (const item of items) {
      if (!isCached(item.media_id)) {
        await downloadMedia(item);
      }
    }
  }, [isCached, downloadMedia]);

  // 从本地存储恢复缓存状态
  useEffect(() => {
    const storedCache = localStorage.getItem('cached_media_info');
    if (storedCache) {
      try {
        const parsed = JSON.parse(storedCache) as CachedMediaInfo[];
        const map = new Map<number, CachedMediaInfo>();
        parsed.forEach(info => {
          map.set(info.media_id, info);
        });
        setCachedMedia(map);
      } catch {
        // 忽略解析错误
      }
    }
  }, []);

  // 保存缓存状态到本地存储
  useEffect(() => {
    const array = Array.from(cachedMedia.values());
    localStorage.setItem('cached_media_info', JSON.stringify(array));
  }, [cachedMedia]);

  // 清理缓存
  const clearCache = useCallback(() => {
    setCachedMedia(new Map());
    localStorage.removeItem('cached_media_info');

    // Web 环境清理 Cache API
    if (!getAndroidBridge()) {
      caches.delete('media-cache').catch(() => {});
    }
  }, [getAndroidBridge]);

  return {
    cachedMedia,
    downloadMedia,
    getMediaUrl,
    isCached,
    getCacheProgress,
    preloadPlaylist,
    clearCache,
  };
};
