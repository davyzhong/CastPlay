/**
 * 播放列表同步 Hook（增强版）
 *
 * 新增功能：
 * 1. 实时推送通知处理
 * 2. 下载进度上报
 * 3. 自动切换播放列表
 * 4. 增量更新支持
 */
import { useState, useCallback, useEffect, useRef } from 'react';
import axios from 'axios';
import type { PlayerPlaylist, PlayerPlaylistItem, PlayerInitResponse } from '../types';
import { useMediaCache } from '../useMediaCache';

// ==================== 类型定义 ====================

export interface PlaylistSyncState {
  status: 'idle' | 'syncing' | 'downloading' | 'ready' | 'switching' | 'error';
  pendingUpdate: PlaylistUpdateNotification | null;
  downloadProgress: Map<number, MediaDownloadProgress>;
  lastSyncTime: Date | null;
  error: string | null;
}

export interface PlaylistUpdateNotification {
  playlist_id: number;
  playlist_name: string;
  version: string;
  action: 'assign' | 'update' | 'remove' | 'activate' | 'deactivate';
  item_count: number;
  total_size: number;
  priority: 'high' | 'normal' | 'low';
  changes?: {
    added?: number[];
    removed?: number[];
    reordered?: boolean;
  };
}

export interface MediaDownloadProgress {
  mediaId: number;
  mediaName: string;
  status: 'pending' | 'downloading' | 'completed' | 'failed';
  progress: number;        // 0-100
  downloadedBytes: number;
  totalBytes: number;
  error?: string;
}

export interface UsePlaylistSyncEnhancedReturn {
  playlists: PlayerPlaylist[];
  currentPlaylist: PlayerPlaylist | null;
  syncState: PlaylistSyncState;
  syncPlaylist: (playlistId: number) => Promise<void>;
  selectPlaylist: (playlistId: number) => void;
  forceRefresh: () => Promise<void>;
  getDownloadProgress: (mediaId: number) => MediaDownloadProgress | undefined;
  reportDownloadProgress: (progress: MediaDownloadProgress) => void;
  reportPlaylistSwitched: (playlistId: number, version: string) => void;
}

// ==================== WebSocket 消息类型 ====================

type WsMessageType =
  | 'playlist_assigned'
  | 'playlist_updated'
  | 'playlist_removed'
  | 'playlist_activated'
  | 'playlist_deactivated'
  | 'device_config_updated'
  | 'device_disabled'
  | 'schedule_updated'
  | 'force_sync'
  | 'control';

interface WsMessage {
  type: WsMessageType;
  device_id: string;
  timestamp: string;
  data: Record<string, unknown>;
}

// ==================== Hook 实现 ====================

export const usePlaylistSyncEnhanced = (
  deviceId: string | null,
  isOnline: boolean = true
): UsePlaylistSyncEnhancedReturn => {
  const [playlists, setPlaylists] = useState<PlayerPlaylist[]>([]);
  const [currentPlaylist, setCurrentPlaylist] = useState<PlayerPlaylist | null>(null);
  const [syncState, setSyncState] = useState<PlaylistSyncState>({
    status: 'idle',
    pendingUpdate: null,
    downloadProgress: new Map(),
    lastSyncTime: null,
    error: null,
  });

  const wsRef = useRef<WebSocket | null>(null);
  const { downloadMedia, isCached, getCacheStatus } = useMediaCache(isOnline);

  // 当前播放列表引用（用于切换）
  const currentPlaylistRef = useRef<PlayerPlaylist | null>(null);
  const pendingPlaylistRef = useRef<PlayerPlaylist | null>(null);

  // ==================== 上报下载进度 ====================

  const reportDownloadProgress = useCallback((progress: MediaDownloadProgress) => {
    setSyncState(prev => {
      const newProgress = new Map(prev.downloadProgress);
      newProgress.set(progress.mediaId, progress);
      return { ...prev, downloadProgress: newProgress };
    });

    // 通过 WebSocket 上报进度
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'download_progress',
        device_id: deviceId,
        timestamp: new Date().toISOString(),
        data: {
          playlist_id: pendingPlaylistRef.current?.id,
          media_id: progress.mediaId,
          media_name: progress.mediaName,
          progress: progress.progress,
          status: progress.status,
          downloaded_bytes: progress.downloadedBytes,
          total_bytes: progress.totalBytes,
          error: progress.error,
        }
      }));
    }
  }, [deviceId]);

  // ==================== 上报播放列表切换完成 ====================

  const reportPlaylistSwitched = useCallback((playlistId: number, version: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'playlist_switched',
        device_id: deviceId,
        timestamp: new Date().toISOString(),
        data: {
          playlist_id: playlistId,
          version: version,
        }
      }));
    }
  }, [deviceId]);

  // ==================== 初始化播放列表 ====================

  const initPlaylists = useCallback(async () => {
    if (!deviceId) return;

    setSyncState(prev => ({ ...prev, status: 'syncing', error: null }));

    try {
      const response = await axios.post<PlayerInitResponse>('/api/player/init', {
        device_id: deviceId,
      });

      const fetchedPlaylists = response.data.playlists || [];
      setPlaylists(fetchedPlaylists);

      // 保存到本地存储（离线时使用）
      localStorage.setItem('cached_playlists', JSON.stringify(fetchedPlaylists));

      // 恢复上次播放的播放列表
      if (fetchedPlaylists.length > 0) {
        const lastPlaylistId = localStorage.getItem('last_playlist_id');
        const lastPlaylist = lastPlaylistId
          ? fetchedPlaylists.find(p => p.id === parseInt(lastPlaylistId))
          : null;

        const targetPlaylist = lastPlaylist || fetchedPlaylists[0];
        setCurrentPlaylist(targetPlaylist);
        currentPlaylistRef.current = targetPlaylist;

        if (lastPlaylist) {
          localStorage.setItem('last_playlist_id', lastPlaylist.id.toString());
        }
      }

      setSyncState(prev => ({
        ...prev,
        status: 'ready',
        lastSyncTime: new Date(),
      }));

    } catch (err) {
      const errorMessage = axios.isAxiosError(err)
        ? (err.response?.data?.detail || '获取播放列表失败')
        : '获取播放列表失败';

      setSyncState(prev => ({ ...prev, status: 'error', error: errorMessage }));

      // 尝试从本地存储加载
      const cachedPlaylists = localStorage.getItem('cached_playlists');
      if (cachedPlaylists) {
        try {
          const parsed = JSON.parse(cachedPlaylists) as PlayerPlaylist[];
          setPlaylists(parsed);
          if (parsed.length > 0) {
            setCurrentPlaylist(parsed[0]);
            currentPlaylistRef.current = parsed[0];
          }
        } catch {
          // 忽略解析错误
        }
      }
    }
  }, [deviceId]);

  // ==================== 同步单个播放列表（带下载） ====================

  const syncPlaylistWithDownload = useCallback(async (
    playlistId: number,
    _notification?: PlaylistUpdateNotification
  ) => {
    setSyncState(prev => ({ ...prev, status: 'syncing' }));

    try {
      // 1. 获取播放列表详情
      const detailResponse = await axios.get<{
        playlist: PlayerPlaylist;
        items: PlayerPlaylistItem[];
      }>(`/api/player/playlist/${playlistId}/detail`);

      const { playlist: newPlaylist, items } = detailResponse.data;

      // 2. 保存为待切换的播放列表
      pendingPlaylistRef.current = { ...newPlaylist, items };

      // 3. 开始后台下载媒体
      setSyncState(prev => ({ ...prev, status: 'downloading' }));

      await downloadPlaylistMedia(items, playlistId);

      // 4. 下载完成，执行原子切换
      await atomicSwitchPlaylist();

    } catch (err) {
      console.error('Sync playlist failed:', err);
      setSyncState(prev => ({
        ...prev,
        status: 'error',
        error: err instanceof Error ? err.message : '同步失败',
      }));
    }
  }, []);

  // ==================== 下载播放列表媒体 ====================

  const downloadPlaylistMedia = useCallback(async (
    items: PlayerPlaylistItem[],
    _playlistId: number
  ) => {
    const concurrency = 3; // 并发下载数
    const queue = [...items];
    const completedMediaIds: number[] = [];

    const downloadNext = async (): Promise<void> => {
    while (queue.length > 0) {
      const item = queue.shift();
      if (!item) break;

      try {
        // 检查是否已缓存
        const cached = await getCacheStatus(item.media_id);
        if (cached?.status === 'completed') {
          completedMediaIds.push(item.media_id);
          continue;
        }

        // 上报下载开始
        reportDownloadProgress({
          mediaId: item.media_id,
          mediaName: item.media?.file_name || `Media ${item.media_id}`,
          status: 'downloading',
          progress: 0,
          downloadedBytes: 0,
          totalBytes: item.media?.file_size || 0,
        });

        // 下载媒体
        await downloadMedia(item.media_id, item.media, (progress) => {
          reportDownloadProgress({
            mediaId: item.media_id,
            mediaName: item.media?.file_name || `Media ${item.media_id}`,
            status: 'downloading',
            progress: progress.percent,
            downloadedBytes: progress.loaded,
            totalBytes: progress.total,
          });
        });

        // 上报下载完成
        reportDownloadProgress({
          mediaId: item.media_id,
          mediaName: item.media?.file_name || `Media ${item.media_id}`,
          status: 'completed',
          progress: 100,
          downloadedBytes: item.media?.file_size || 0,
          totalBytes: item.media?.file_size || 0,
        });

        completedMediaIds.push(item.media_id);

      } catch (error) {
        // 上报下载失败
        reportDownloadProgress({
          mediaId: item.media_id,
          mediaName: item.media?.file_name || `Media ${item.media_id}`,
          status: 'failed',
          progress: 0,
          downloadedBytes: 0,
          totalBytes: item.media?.file_size || 0,
          error: error instanceof Error ? error.message : '下载失败',
        });
      }
    }
  };

  // 启动并发下载
  const downloadPromises: Promise<void>[] = [];
  for (let i = 0; i < concurrency; i++) {
    downloadPromises.push(downloadNext());
  }

  await Promise.all(downloadPromises);
  }, [downloadMedia, getCacheStatus, reportDownloadProgress]);

  // ==================== 原子切换播放列表 ====================

  const atomicSwitchPlaylist = useCallback(async () => {
    if (!pendingPlaylistRef.current) return;

    setSyncState(prev => ({ ...prev, status: 'switching' }));

    // 原子切换
    const newPlaylist = pendingPlaylistRef.current;
    currentPlaylistRef.current = newPlaylist;
    pendingPlaylistRef.current = null;

    // 更新状态
    setCurrentPlaylist(newPlaylist);
    localStorage.setItem('last_playlist_id', newPlaylist.id.toString());

    // 上报切换完成
    reportPlaylistSwitched(newPlaylist.id, newPlaylist.version || '1.0.0');

    setSyncState(prev => ({
      ...prev,
      status: 'ready',
      pendingUpdate: null,
      downloadProgress: new Map(),
      lastSyncTime: new Date(),
    }));

    console.log(`Playlist switched to: ${newPlaylist.name}`);
  }, [reportPlaylistSwitched]);

  // ==================== 处理 WebSocket 消息 ====================

  const handleWebSocketMessage = useCallback(async (message: WsMessage) => {
    console.log('Received WebSocket message:', message.type);

    switch (message.type) {
      case 'playlist_assigned': {
        const data = message.data as unknown as PlaylistUpdateNotification;
        await syncPlaylistWithDownload(data.playlist_id, data);
        break;
      }

      case 'playlist_updated': {
        const data = message.data as unknown as PlaylistUpdateNotification;
        await handleIncrementalUpdate(data);
        break;
      }

      case 'playlist_removed': {
        const { playlist_id } = message.data as { playlist_id: number };
        handlePlaylistRemoved(playlist_id);
        break;
      }

      case 'playlist_activated':
      case 'playlist_deactivated': {
        const { playlist_id, is_active } = message.data as { playlist_id: number; is_active: boolean };
        handlePlaylistActivation(playlist_id, is_active);
        break;
      }

      case 'force_sync': {
        await initPlaylists();
        break;
      }

      case 'device_disabled': {
        const { is_disabled } = message.data as { is_disabled: boolean };
        console.log(`Device ${is_disabled ? 'disabled' : 'enabled'}`);
        // 可以在这里触发 UI 提示
        break;
      }

      case 'schedule_updated': {
        console.log('Schedule updated, will apply on next playback cycle');
        break;
      }

      case 'control': {
        const controlData = message.data as { action: string; [key: string]: unknown };
        handleControlCommand(controlData);
        break;
      }
    }
  }, [syncPlaylistWithDownload, initPlaylists]);

  // ==================== 增量更新处理 ====================

  const handleIncrementalUpdate = useCallback(async (data: PlaylistUpdateNotification) => {
    // 如果是当前播放的列表，执行热更新
    if (currentPlaylistRef.current?.id === data.playlist_id) {
      // 获取最新数据
      try {
        const response = await axios.get<{
          playlist: PlayerPlaylist;
          items: PlayerPlaylistItem[];
        }>(`/api/player/playlist/${data.playlist_id}/detail`);

        const { playlist, items } = response.data;

        // 只下载新增的媒体
        if (data.changes?.added?.length) {
          const addedItems = items.filter(item =>
            data.changes!.added!.includes(item.media_id)
          );

          for (const item of addedItems) {
            if (!await isCached(item.media_id)) {
              await downloadMedia(item.media_id, item.media);
            }
          }
        }

        // 热更新播放列表（不中断播放）
        const updatedPlaylist = { ...playlist, items };
        currentPlaylistRef.current = updatedPlaylist;
        setCurrentPlaylist(updatedPlaylist);

        console.log(`Playlist ${data.playlist_name} hot-updated to v${data.version}`);
      } catch (error) {
        console.error('Incremental update failed:', error);
      }
    } else {
      // 非当前播放列表，标记为待更新
      setSyncState(prev => ({ ...prev, pendingUpdate: data }));
    }
  }, [downloadMedia, isCached]);

  // ==================== 处理播放列表移除 ====================

  const handlePlaylistRemoved = useCallback((playlistId: number) => {
    setPlaylists(prev => prev.filter(p => p.id !== playlistId));

    // 如果移除的是当前播放列表，切换到第一个可用列表
    if (currentPlaylistRef.current?.id === playlistId) {
      const remaining = playlists.filter(p => p.id !== playlistId);
      if (remaining.length > 0) {
        setCurrentPlaylist(remaining[0]);
        currentPlaylistRef.current = remaining[0];
      } else {
        setCurrentPlaylist(null);
        currentPlaylistRef.current = null;
      }
    }
  }, [playlists]);

  // ==================== 处理播放列表激活状态变更 ====================

  const handlePlaylistActivation = useCallback((playlistId: number, isActive: boolean) => {
    setPlaylists(prev => prev.map(p =>
      p.id === playlistId ? { ...p, is_active: isActive } : p
    ));

    // 如果激活的是新列表且当前无激活列表，可能需要切换
    if (isActive && currentPlaylistRef.current?.id !== playlistId) {
      const playlist = playlists.find(p => p.id === playlistId);
      if (playlist) {
        setCurrentPlaylist({ ...playlist, is_active: true });
        currentPlaylistRef.current = { ...playlist, is_active: true };
        localStorage.setItem('last_playlist_id', playlistId.toString());
      }
    }
  }, [playlists]);

  // ==================== 处理控制命令 ====================

  const handleControlCommand = useCallback((data: { action: string; [key: string]: unknown }) => {
    console.log('Control command received:', data.action);

    switch (data.action) {
      case 'reload':
        initPlaylists();
        break;
      case 'switch_playlist':
        if (typeof data.playlist_id === 'number') {
          syncPlaylistWithDownload(data.playlist_id);
        }
        break;
      // 其他控制命令由播放器组件处理
    }
  }, [initPlaylists, syncPlaylistWithDownload]);

  // ==================== 选择播放列表 ====================

  const selectPlaylist = useCallback((playlistId: number) => {
    const playlist = playlists.find(p => p.id === playlistId);
    if (playlist) {
      setCurrentPlaylist(playlist);
      currentPlaylistRef.current = playlist;
      localStorage.setItem('last_playlist_id', playlistId.toString());
    }
  }, [playlists]);

  // ==================== 强制刷新 ====================

  const forceRefresh = useCallback(async () => {
    await initPlaylists();
  }, [initPlaylists]);

  // ==================== 同步播放列表（兼容旧版） ====================

  const syncPlaylist = useCallback(async (playlistId: number) => {
    await syncPlaylistWithDownload(playlistId);
  }, [syncPlaylistWithDownload]);

  // ==================== 获取下载进度 ====================

  const getDownloadProgress = useCallback((mediaId: number) => {
    return syncState.downloadProgress.get(mediaId);
  }, [syncState.downloadProgress]);

  // ==================== WebSocket 重连配置 ====================
  const MAX_RECONNECT_ATTEMPTS = 10;
  const INITIAL_RECONNECT_DELAY = 1000; // 1秒
  const MAX_RECONNECT_DELAY = 30000; // 30秒

  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const isManualCloseRef = useRef(false);

  // ==================== WebSocket 连接 ====================

  const connectWebSocket = useCallback(() => {
    if (!deviceId || !isOnline) return;

    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/${deviceId}`;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        reconnectAttemptsRef.current = 0; // 重置重连计数

        // 发送连接确认
        ws.send(JSON.stringify({
          type: 'connection_ready',
          device_id: deviceId,
          timestamp: new Date().toISOString(),
        }));
      };

      ws.onmessage = (event) => {
        try {
          const message: WsMessage = JSON.parse(event.data);
          handleWebSocketMessage(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      ws.onclose = (event) => {
        console.log('WebSocket disconnected, code:', event.code, 'reason:', event.reason);

        // 如果是手动关闭，不进行重连
        if (isManualCloseRef.current) {
          console.log('Manual close, skipping reconnection');
          return;
        }

        // 尝试重连
        scheduleReconnect();
      };

    } catch (error) {
      console.error('WebSocket connection failed:', error);
      scheduleReconnect();
    }
  }, [deviceId, isOnline, handleWebSocketMessage]);

  // ==================== 指数退避重连 ====================

  const scheduleReconnect = useCallback(() => {
    // 清理之前的定时器
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // 检查是否超过最大重试次数
    if (reconnectAttemptsRef.current >= MAX_RECONNECT_ATTEMPTS) {
      console.error('Max reconnection attempts reached, giving up');
      setSyncState(prev => ({
        ...prev,
        status: 'error',
        error: '连接服务器失败，请检查网络后刷新页面',
      }));
      return;
    }

    // 计算延迟时间（指数退避）
    const delay = Math.min(
      INITIAL_RECONNECT_DELAY * Math.pow(2, reconnectAttemptsRef.current),
      MAX_RECONNECT_DELAY
    );

    reconnectAttemptsRef.current++;
    console.log(`Scheduling reconnect in ${delay}ms (attempt ${reconnectAttemptsRef.current}/${MAX_RECONNECT_ATTEMPTS})`);

    reconnectTimeoutRef.current = window.setTimeout(() => {
      console.log('Attempting to reconnect...');
      connectWebSocket();
    }, delay);
  }, [connectWebSocket]);

  // ==================== 组件挂载时连接 WebSocket ====================

  useEffect(() => {
    isManualCloseRef.current = false;
    reconnectAttemptsRef.current = 0;
    connectWebSocket();

    return () => {
      // 组件卸载时清理 - 设置手动关闭标志防止重连
      isManualCloseRef.current = true;

      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }

      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmount');
        wsRef.current = null;
      }
    };
  }, [deviceId, isOnline]); // 故意不包含 connectWebSocket 以避免无限循环

  // ==================== 初始化时加载播放列表 ====================

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
            const lastPlaylistId = localStorage.getItem('last_playlist_id');
            const lastPlaylist = lastPlaylistId
              ? parsed.find(p => p.id === parseInt(lastPlaylistId))
              : null;
            const targetPlaylist = lastPlaylist || parsed[0];
            setCurrentPlaylist(targetPlaylist);
            currentPlaylistRef.current = targetPlaylist;
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
    syncState,
    syncPlaylist,
    selectPlaylist,
    forceRefresh,
    getDownloadProgress,
    reportDownloadProgress,
    reportPlaylistSwitched,
  };
};
