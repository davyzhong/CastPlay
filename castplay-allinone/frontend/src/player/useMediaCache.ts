/**
 * 媒体缓存 Hook
 * 处理媒体文件的下载、缓存和离线访问
 */
import { useState, useCallback, useEffect } from 'react';
import type { PlayerPlaylistItem, CachedMediaInfo, CacheStatus } from './types';

// 下载进度信息
export interface DownloadProgress {
  percent: number;      // 0-100
  loaded: number;       // 已下载字节
  total: number;        // 总字节
}

// 媒体信息（用于增强版下载）
export interface MediaInfo {
  id: number;
  file_name?: string;
  file_type?: string;
  file_url?: string;
  file_size?: number;
}

// 缓存状态详情
export interface CacheStatusDetail {
  mediaId: number;
  status: CacheStatus;
  progress: number;
  localPath?: string;
}

export interface UseMediaCacheReturn {
  cachedMedia: Map<number, CachedMediaInfo>;
  downloadMedia: (mediaId: number, media?: MediaInfo, onProgress?: (progress: DownloadProgress) => void) => Promise<boolean>;
  getMediaUrl: (item: PlayerPlaylistItem) => string;
  isCached: (mediaId: number) => Promise<boolean>;
  getCacheStatus: (mediaId: number) => Promise<CacheStatusDetail | null>;
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

  // 检查媒体是否已缓存（异步版本）
  const isCached = useCallback(async (mediaId: number): Promise<boolean> => {
    const bridge = getAndroidBridge();
    if (bridge) {
      return bridge.isMediaCached(mediaId.toString());
    }

    // Web 环境：检查内存缓存
    return cachedMedia.has(mediaId) && cachedMedia.get(mediaId)?.status === 'completed';
  }, [cachedMedia, getAndroidBridge]);

  // 获取缓存状态详情
  const getCacheStatus = useCallback(async (mediaId: number): Promise<CacheStatusDetail | null> => {
    const bridge = getAndroidBridge();
    if (bridge) {
      const isComplete = bridge.isMediaCached(mediaId.toString());
      const progress = bridge.getDownloadProgress(mediaId.toString());
      const localPath = bridge.getCachedMediaPath(mediaId.toString());

      return {
        mediaId,
        status: isComplete ? 'completed' : (progress > 0 ? 'downloading' : 'pending'),
        progress: isComplete ? 100 : progress,
        localPath: localPath || undefined,
      };
    }

    // Web 环境
    const info = cachedMedia.get(mediaId);
    if (info) {
      return {
        mediaId,
        status: info.status,
        progress: info.progress,
        localPath: info.local_path || undefined,
      };
    }

    return null;
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
  const downloadMedia = useCallback(async (
    mediaId: number,
    media?: MediaInfo,
    onProgress?: (progress: DownloadProgress) => void
  ): Promise<boolean> => {
    const bridge = getAndroidBridge();
    const fileUrl = media?.file_url || `/api/player/media/${mediaId}/download`;
    const fileSize = media?.file_size || 0;

    // 更新状态为下载中
    setCachedMedia(prev => {
      const newMap = new Map(prev);
      newMap.set(mediaId, {
        media_id: mediaId,
        local_path: '',
        status: 'downloading' as CacheStatus,
        progress: 0,
      });
      return newMap;
    });

    if (bridge) {
      // Android 环境：调用原生下载
      bridge.downloadMedia(fileUrl, mediaId.toString());

      // 轮询下载进度
      return new Promise((resolve) => {
        const checkProgress = setInterval(() => {
          const progress = bridge.getDownloadProgress(mediaId.toString());

          // 调用进度回调
          if (onProgress) {
            onProgress({
              percent: progress,
              loaded: Math.floor(fileSize * progress / 100),
              total: fileSize,
            });
          }

          // 更新进度
          setCachedMedia(prev => {
            const newMap = new Map(prev);
            const info = newMap.get(mediaId);
            if (info) {
              info.progress = progress;
            }
            return newMap;
          });

          if (progress >= 100) {
            clearInterval(checkProgress);
            setCachedMedia(prev => {
              const newMap = new Map(prev);
              const info = newMap.get(mediaId);
              if (info) {
                info.status = 'completed';
                info.local_path = bridge.getCachedMediaPath(mediaId.toString()) || '';
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
      // Web 环境：使用 fetch + Cache API
      try {
        // 使用 XMLHttpRequest 获取下载进度
        const response = await new Promise<Response>((resolve, reject) => {
          const xhr = new XMLHttpRequest();
          xhr.open('GET', fileUrl, true);
          xhr.responseType = 'blob';

          xhr.onprogress = (event) => {
            if (event.lengthComputable && onProgress) {
              onProgress({
                percent: Math.round((event.loaded / event.total) * 100),
                loaded: event.loaded,
                total: event.total,
              });
            }
          };

          xhr.onload = () => {
            if (xhr.status === 200) {
              resolve(new Response(xhr.response));
            } else {
              reject(new Error(`HTTP ${xhr.status}`));
            }
          };

          xhr.onerror = () => reject(new Error('Network error'));
          xhr.send();
        });

        const blob = await response.blob();
        const localUrl = URL.createObjectURL(blob);

        // 同时存储到 Cache API
        try {
          const cache = await caches.open('media-cache');
          const cacheResponse = new Response(blob);
          await cache.put(fileUrl, cacheResponse);
        } catch {
          // Cache API 失败不影响主要功能
        }

        setCachedMedia(prev => {
          const newMap = new Map(prev);
          newMap.set(mediaId, {
            media_id: mediaId,
            local_path: localUrl,
            status: 'completed',
            progress: 100,
          });
          return newMap;
        });

        // 最终进度回调
        if (onProgress) {
          onProgress({ percent: 100, loaded: fileSize, total: fileSize });
        }

        return true;
      } catch {
        setCachedMedia(prev => {
          const newMap = new Map(prev);
          newMap.set(mediaId, {
            media_id: mediaId,
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
      if (!(await isCached(item.media_id))) {
        await downloadMedia(item.media_id, {
          id: item.media_id,
          file_name: item.file_name,
          file_type: item.file_type,
          file_url: item.file_url,
          file_size: item.file_size,
        });
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
    getCacheStatus,
    getCacheProgress,
    preloadPlaylist,
    clearCache,
  };
};
