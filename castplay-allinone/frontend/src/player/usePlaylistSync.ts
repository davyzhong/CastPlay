/**
 * 播放列表同步 Hook
 * 处理播放列表的初始化、版本检查和增量更新
 */
import { useState, useCallback, useEffect, useRef } from 'react';
import axios from 'axios';
import type { PlayerPlaylist, PlayerPlaylistItem, PlayerInitResponse, PlayerWsMessage } from './types';

export interface UsePlaylistSyncReturn {
  playlists: PlayerPlaylist[];
  currentPlaylist: PlayerPlaylist | null;
  isLoading: boolean;
  error: string | null;
  syncPlaylist: (playlistId: number) => Promise<void>;
  selectPlaylist: (playlistId: number) => void;
  checkVersion: (playlistId: number) => Promise<boolean>;
}

export const usePlaylistSync = (
  deviceId: string | null,
  isOnline: boolean = true
): UsePlaylistSyncReturn => {
  const [playlists, setPlaylists] = useState<PlayerPlaylist[]>([]);
  const [currentPlaylist, setCurrentPlaylist] = useState<PlayerPlaylist | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // 初始化播放列表
  const initPlaylists = useCallback(async () => {
    if (!deviceId) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await axios.post<PlayerInitResponse>('/api/player/init', {
        device_id: deviceId,
      });

      const fetchedPlaylists = response.data.playlists || [];
      setPlaylists(fetchedPlaylists);

      // 保存到本地存储（离线时使用）
      localStorage.setItem('cached_playlists', JSON.stringify(fetchedPlaylists));

      // 如果有激活的播放列表， 设为当前
      if (fetchedPlaylists.length > 0) {
        // 检查是否有上次播放的播放列表
        const lastPlaylistId = localStorage.getItem('last_playlist_id');
        const lastPlaylist = lastPlaylistId
          ? fetchedPlaylists.find(p => p.id === parseInt(lastPlaylistId))
          : null;

        setCurrentPlaylist(lastPlaylist || fetchedPlaylists[0]);
        if (lastPlaylist) {
          localStorage.setItem('last_playlist_id', lastPlaylist.id.toString());
        }
      }
    } catch (err) {
      const errorMessage = axios.isAxiosError(err)
        ? (err.response?.data?.detail || '获取播放列表失败')
        : '获取播放列表失败';
      setError(errorMessage);

      // 尝试从本地存储加载
      const cachedPlaylists = localStorage.getItem('cached_playlists');
      if (cachedPlaylists) {
        try {
          const parsed = JSON.parse(cachedPlaylists) as PlayerPlaylist[];
          setPlaylists(parsed);
          if (parsed.length > 0) {
            setCurrentPlaylist(parsed[0]);
          }
        } catch {
          // 忽略解析错误
        }
      }
    } finally {
      setIsLoading(false);
    }
  }, [deviceId]);

  // 检查播放列表版本
  const checkVersion = useCallback(async (playlistId: number): Promise<boolean> => {
    try {
      const playlist = playlists.find(p => p.id === playlistId);
      if (!playlist) return false;

      const response = await axios.post(`/api/player/playlist/${playlistId}/check`, {
        version: playlist.version,
      });

      return response.data.needs_update;
    } catch {
      return false;
    }
  }, [playlists]);

  // 同步播放列表
  const syncPlaylist = useCallback(async (playlistId: number) => {
    setIsLoading(true);
    try {
      const needsUpdate = await checkVersion(playlistId);
      if (!needsUpdate) {
        return;
      }

      // 重新初始化获取最新数据
      await initPlaylists();
    } catch (err) {
      setError('同步播放列表失败');
    } finally {
      setIsLoading(false);
    }
  }, [checkVersion, initPlaylists]);

  // 选择播放列表
  const selectPlaylist = useCallback((playlistId: number) => {
    const playlist = playlists.find(p => p.id === playlistId);
    if (playlist) {
      setCurrentPlaylist(playlist);
      localStorage.setItem('last_playlist_id', playlistId.toString());
    }
  }, [playlists]);

  // WebSocket 连接
  useEffect(() => {
    if (!deviceId || !isOnline) return;

    const wsUrl = `ws://${window.location.host}/ws/player/${deviceId}`;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
      };

      ws.onmessage = (event) => {
        try {
          const message: PlayerWsMessage = JSON.parse(event.data);

          if (message.event === 'playlist_update') {
            syncPlaylist(message.playlist_id!);
          } else if (message.event === 'force_sync') {
            initPlaylists();
          }
        } catch {
          // 忽略解析错误
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
      };
    } catch {
      // WebSocket 连接失败
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [deviceId, isOnline, syncPlaylist, initPlaylists]);

  // 初始化时加载播放列表
  useEffect(() => {
    if (deviceId && isOnline) {
      initPlaylists();
    } else if (!isOnline) {
      // 离线时从本地存储加载
      const cachedPlaylists = localStorage.getItem('cached_playlists');
      if (cachedPlaylists) {
        try {
          const parsed = JSON.parse(cachedPlaylists) as PlayerPlaylist[];
          setPlaylists(parsed);
          if (parsed.length > 0) {
            setCurrentPlaylist(parsed[0]);
          }
        } catch {
          // 忽略解析错误
        }
      }
    }
  }, [deviceId, isOnline, initPlaylists]);

  return {
    playlists,
    currentPlaylist,
    isLoading,
    error,
    syncPlaylist,
    selectPlaylist,
    checkVersion,
  };
};
