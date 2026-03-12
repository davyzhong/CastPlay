/**
 * 播放列表选择 Hook
 * 处理首次安装时的播放列表选择和后台下载
 */
import { useState, useEffect, useCallback } from 'react';
import { createDownloadManager } from '../services/DownloadManager';

export interface PlaylistInfo {
    id: number;
    name: string;
    media_count: number;
    total_size_mb: number;
}

export interface UsePlaylistSelectionResult {
    availablePlaylists: PlaylistInfo[];
    selectedPlaylist: PlaylistInfo | null;
    isLoading: boolean;
    isDownloading: boolean;
    error: string | null;
    loadPlaylists: () => Promise<void>;
    selectPlaylist: (playlist: PlaylistInfo) => void;
    skipSelection: () => void;
}

const SETUP_COMPLETED_KEY = 'castplay_setup_completed';
const SELECTED_PLAYLIST_KEY = 'castplay_selected_playlist_id';

/**
 * 获取可用播放列表
 */
async function fetchAvailablePlaylists(): Promise<PlaylistInfo[]> {
    const response = await fetch('/api/player/playlists/available');
    if (!response.ok) {
        throw new Error('Failed to fetch available playlists');
    }
    const data = await response.json();
    return data.playlists || [];
}

/**
 * 播放列表选择 Hook
 */
export function usePlaylistSelection(deviceId: string): UsePlaylistSelectionResult {
    const [availablePlaylists, setAvailablePlaylists] = useState<PlaylistInfo[]>([]);
    const [selectedPlaylist, setSelectedPlaylist] = useState<PlaylistInfo | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [isDownloading, setIsDownloading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // 检查是否已完成设置
    const isSetupCompleted = localStorage.getItem(SETUP_COMPLETED_KEY) === 'true';

    /**
     * 加载可用播放列表
     */
    const loadPlaylists = useCallback(async () => {
        if (isSetupCompleted) {
            return; // 已完成设置，无需加载
        }

        setIsLoading(true);
        setError(null);

        try {
            const playlists = await fetchAvailablePlaylists();
            setAvailablePlaylists(playlists);
        } catch (err) {
            console.error('Failed to load playlists:', err);
            setError('加载播放列表失败，将使用默认播放列表');
        } finally {
            setIsLoading(false);
        }
    }, [isSetupCompleted]);

    /**
     * 选择播放列表并开始后台下载
     */
    const selectPlaylist = useCallback(async (playlist: PlaylistInfo) => {
        setSelectedPlaylist(playlist);
        setIsDownloading(true);
        setError(null);

        try {
            // 检查存储空间
            const downloadManager = createDownloadManager(deviceId);
            const hasSpace = await downloadManager.checkStorageSpace(playlist.total_size_mb);

            if (!hasSpace) {
                throw new Error('存储空间不足');
            }

            // TODO: 开始后台下载播放列表
            // 这里需要集成到实际的下载流程中
            console.log('Starting background download for playlist:', playlist);

            // 标记为已完成设置
            localStorage.setItem(SETUP_COMPLETED_KEY, 'true');
            localStorage.setItem(SELECTED_PLAYLIST_KEY, playlist.id.toString());

            setIsDownloading(false);
        } catch (err) {
            console.error('Failed to select playlist:', err);
            setError(err instanceof Error ? err.message : '选择播放列表失败');
            setIsDownloading(false);
        }
    }, [deviceId]);

    /**
     * 跳过选择，使用默认播放列表
     */
    const skipSelection = useCallback(() => {
        localStorage.setItem(SETUP_COMPLETED_KEY, 'true');
        setSelectedPlaylist(null);
    }, []);

    // 初始加载
    useEffect(() => {
        if (!isSetupCompleted) {
            loadPlaylists();
        }
    }, [isSetupCompleted, loadPlaylists]);

    return {
        availablePlaylists,
        selectedPlaylist,
        isLoading,
        isDownloading,
        error,
        loadPlaylists,
        selectPlaylist,
        skipSelection
    };
}
