/**
 * 播放列表选择 Hook
 * 支持多选、持久化存储、至少保留一个限制
 */
import { useState, useEffect, useCallback } from 'react';
import { playerApi } from '../../utils/apiClient';
import { configStorage } from '../services/ConfigStorage';
import { STORAGE_KEYS } from '../types/config';

export interface PlaylistInfo {
  id: number;
  name: string;
  media_count: number;
  total_size_mb: number;
  thumbnail_url?: string;
}

export interface PlaylistSelectionState {
  /** 选中的播放列表 ID 列表 */
  selectedIds: number[];
  /** 最后更新时间 */
  updatedAt: string;
  /** 是否由用户手动修改 */
  userModified: boolean;
}

export interface UsePlaylistSelectionResult {
  /** 可用的播放列表 */
  availablePlaylists: PlaylistInfo[];
  /** 选中的播放列表 ID 列表 */
  selectedIds: number[];
  /** 是否正在加载 */
  isLoading: boolean;
  /** 错误信息 */
  error: string | null;
  /** 加载播放列表 */
  loadPlaylists: () => Promise<void>;
  /** 切换播放列表选择状态 */
  toggleSelection: (playlistId: number) => void;
  /** 全选 */
  selectAll: () => void;
  /** 取消全选（保留一个） */
  deselectAll: () => void;
  /** 确认选择 */
  confirmSelection: () => void;
  /** 跳过选择 */
  skipSelection: () => void;
  /** 是否已完成选择 */
  isSelectionComplete: boolean;
  /** 选中的播放列表详情 */
  selectedPlaylists: PlaylistInfo[];
}

const SELECTION_STORAGE_KEY = 'castplay_playlist_selection';
const SETUP_COMPLETED_KEY = 'castplay_setup_completed';

/**
 * 从存储加载选择状态
 */
function loadSelectionState(): PlaylistSelectionState | null {
  const stored = localStorage.getItem(SELECTION_STORAGE_KEY);
  if (stored) {
    try {
      return JSON.parse(stored);
    } catch {
      return null;
    }
  }
  return null;
}

/**
 * 保存选择状态到存储
 */
function saveSelectionState(state: PlaylistSelectionState): void {
  localStorage.setItem(SELECTION_STORAGE_KEY, JSON.stringify(state));
}

/**
 * 播放列表选择 Hook
 */
export function usePlaylistSelection(deviceId: string | null): UsePlaylistSelectionResult {
  const [availablePlaylists, setAvailablePlaylists] = useState<PlaylistInfo[]>([]);
  const [selectedIds, setSelectedIds] = useState<number[]>(() => {
    const state = loadSelectionState();
    return state?.selectedIds || [];
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSelectionComplete, setIsSelectionComplete] = useState(() => {
    return localStorage.getItem(SETUP_COMPLETED_KEY) === 'true';
  });

  // 加载可用播放列表
  const loadPlaylists = useCallback(async () => {
    if (!deviceId) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const data = await playerApi.get<{ playlists: PlaylistInfo[] }>('/player/playlists/available');
      const playlists = data.playlists || [];
      setAvailablePlaylists(playlists);

      // 如果是首次加载且没有选择，默认全选
      const state = loadSelectionState();
      if (!state || state.selectedIds.length === 0) {
        if (playlists.length > 0) {
          const allIds = playlists.map(p => p.id);
          setSelectedIds(allIds);
          console.log('[usePlaylistSelection] First load, selecting all playlists:', allIds);
        }
      } else {
        // 恢复之前的选择
        setSelectedIds(state.selectedIds);
      }
    } catch (err) {
      console.error('[usePlaylistSelection] Failed to load playlists:', err);
      setError('加载播放列表失败');
    } finally {
      setIsLoading(false);
    }
  }, [deviceId]);

  // 切换选择状态
  const toggleSelection = useCallback((playlistId: number) => {
    setSelectedIds(prev => {
      // 如果只剩一个且要取消，阻止操作
      if (prev.length === 1 && prev.includes(playlistId)) {
        console.log('[usePlaylistSelection] Cannot deselect last playlist');
        return prev;
      }

      if (prev.includes(playlistId)) {
        return prev.filter(id => id !== playlistId);
      } else {
        return [...prev, playlistId];
      }
    });
  }, []);

  // 全选
  const selectAll = useCallback(() => {
    const allIds = availablePlaylists.map(p => p.id);
    setSelectedIds(allIds);
    console.log('[usePlaylistSelection] Selected all playlists:', allIds);
  }, [availablePlaylists]);

  // 取消全选（保留第一个）
  const deselectAll = useCallback(() => {
    if (availablePlaylists.length > 0) {
      const firstId = availablePlaylists[0].id;
      setSelectedIds([firstId]);
      console.log('[usePlaylistSelection] Deselected all, keeping first:', firstId);
    }
  }, [availablePlaylists]);

  // 确认选择
  const confirmSelection = useCallback(() => {
    if (selectedIds.length === 0) {
      setError('请至少选择一个播放列表');
      return;
    }

    // 保存选择状态
    const state: PlaylistSelectionState = {
      selectedIds,
      updatedAt: new Date().toISOString(),
      userModified: true,
    };
    saveSelectionState(state);

    // 同时保存到 configStorage 以便跨平台使用
    configStorage.set(STORAGE_KEYS.PLAYLIST_SELECTION, {
      selectedIds,
      updatedAt: state.updatedAt,
      userModified: true,
    });

    // 标记设置完成
    localStorage.setItem(SETUP_COMPLETED_KEY, 'true');
    setIsSelectionComplete(true);

    console.log('[usePlaylistSelection] Selection confirmed:', selectedIds);
  }, [selectedIds]);

  // 跳过选择（使用全部）
  const skipSelection = useCallback(() => {
    const allIds = availablePlaylists.map(p => p.id);
    setSelectedIds(allIds);

    const state: PlaylistSelectionState = {
      selectedIds: allIds,
      updatedAt: new Date().toISOString(),
      userModified: false,
    };
    saveSelectionState(state);

    localStorage.setItem(SETUP_COMPLETED_KEY, 'true');
    setIsSelectionComplete(true);

    console.log('[usePlaylistSelection] Skipped selection, using all playlists');
  }, [availablePlaylists]);

  // 获取选中的播放列表详情
  const selectedPlaylists = availablePlaylists.filter(p => selectedIds.includes(p.id));

  // 初始加载
  useEffect(() => {
    if (deviceId && !isSelectionComplete) {
      loadPlaylists();
    }
  }, [deviceId, isSelectionComplete, loadPlaylists]);

  return {
    availablePlaylists,
    selectedIds,
    isLoading,
    error,
    loadPlaylists,
    toggleSelection,
    selectAll,
    deselectAll,
    confirmSelection,
    skipSelection,
    isSelectionComplete,
    selectedPlaylists,
  };
}
