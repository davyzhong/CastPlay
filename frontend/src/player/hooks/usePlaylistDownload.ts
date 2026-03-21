/**
 * 播放列表下载 Hook
 *
 * 封装 PlaylistDownloadManager，提供 React Hook 接口
 * 支持 Web 和 Android 两套下载策略
 */
import { useState, useCallback, useRef } from 'react';
import {
    PlaylistDownloadState,
    playlistDownloadManager,
    MediaItem,
    DownloadTask,
} from '../services/PlaylistDownloadManager';

// 下载状态
export type DownloadStatus = 'idle' | 'pending' | 'downloading' | 'completed' | 'failed' | 'partial' | 'cancelled';

// Hook 返回值
export interface UsePlaylistDownloadReturn {
    // 状态
    status: DownloadStatus;
    progress: number;
    completedFiles: number;
    totalFiles: number;
    failedFiles: number;
    currentTask: DownloadTask | null;

    // 方法
    startDownload: (playlistId: number, version: string, mediaList: MediaItem[]) => Promise<void>;
    cancelDownload: () => void;
    getCacheStatus: (playlistId: number) => Promise<PlaylistDownloadState | null>;

    // Android 专用
    startAndroidDownload: (playlistId: number, version: string, mediaList: MediaItem[]) => Promise<void>;
    getAndroidDownloadProgress: (playlistId: number) => number;
    isAndroidDownloadComplete: (playlistId: number) => boolean;
}

export const usePlaylistDownload = (): UsePlaylistDownloadReturn => {
    const [status, setStatus] = useState<DownloadStatus>('idle');
    const [progress, setProgress] = useState(0);
    const [completedFiles, setCompletedFiles] = useState(0);
    const [totalFiles, setTotalFiles] = useState(0);
    const [failedFiles, setFailedFiles] = useState(0);
    const [currentTask, setCurrentTask] = useState<DownloadTask | null>(null);

    const currentPlaylistId = useRef<number | null>(null);
    const isAndroid = typeof window.AndroidBridge !== 'undefined';

    /**
     * 更新状态
     */
    const updateState = useCallback((state: PlaylistDownloadState) => {
        setStatus(state.status as DownloadStatus);
        setProgress(state.progress);
        setCompletedFiles(state.completedFiles);
        setTotalFiles(state.totalFiles);
        setFailedFiles(state.failedFiles);
    }, []);

    /**
     * 开始 Web 下载
     */
    const startDownload = useCallback(async (
        playlistId: number,
        _version: string,
        mediaList: MediaItem[]
    ): Promise<void> => {
        if (isAndroid) {
            // Android 环境使用 JsBridge
            return startAndroidDownload(playlistId, _version, mediaList);
        }

        currentPlaylistId.current = playlistId;
        setStatus('pending');
        setTotalFiles(mediaList.length);
        setProgress(0);
        setCompletedFiles(0);
        setFailedFiles(0);

        try {
            const state = await playlistDownloadManager.startDownload(
                playlistId,
                _version,
                mediaList,
                {
                    onTaskProgress: (_mediaId, task) => {
                        setCurrentTask(task);
                    },
                    onTaskComplete: (_mediaId, _task) => {
                        console.log(`[usePlaylistDownload] Task complete: ${_mediaId}`);
                    },
                    onTaskFailed: (_mediaId, task) => {
                        console.error(`[usePlaylistDownload] Task failed: ${_mediaId}`, task.error);
                    },
                    onPlaylistProgress: (state) => {
                        updateState(state);
                    },
                    onPlaylistComplete: (state) => {
                        updateState(state);
                        setCurrentTask(null);
                        console.log(`[usePlaylistDownload] Playlist download complete:`, state.status);
                    },
                }
            );

            updateState(state);
        } catch (error) {
            console.error('[usePlaylistDownload] Download failed:', error);
            setStatus('failed');
        }
    }, [isAndroid, updateState]);

    /**
     * 开始 Android 下载
     */
    const startAndroidDownload = useCallback(async (
        playlistId: number,
        _version: string,
        mediaList: MediaItem[]
    ): Promise<void> => {
        const bridge = window.AndroidBridge;
        if (!bridge) {
            console.error('[usePlaylistDownload] AndroidBridge not available');
            setStatus('failed');
            return;
        }

        currentPlaylistId.current = playlistId;
        setStatus('pending');
        setTotalFiles(mediaList.length);
        setProgress(0);
        setCompletedFiles(0);
        setFailedFiles(0);

        // 设置回调
        window.AndroidBridgeCallbacks = {
            onDownloadProgress: (data) => {
                setProgress(data.percent);
                setCompletedFiles(data.completed);
                setTotalFiles(data.total);
                setStatus('downloading');
            },
            onDownloadCompleted: (data) => {
                setCompletedFiles(data.success_count);
                setFailedFiles(data.failed_count);
                setProgress(100);
                setStatus(data.failed_count > 0 ? 'partial' : 'completed');
            },
            onDownloadError: (data) => {
                console.error('[usePlaylistDownload] Android download error:', data.error);
                setStatus('failed');
            },
        };

        // 调用 JsBridge 开始下载
        bridge.startPlaylistDownload(
            playlistId.toString(),
            JSON.stringify(mediaList)
        );

        setStatus('downloading');
    }, []);

    /**
     * 取消下载
     */
    const cancelDownload = useCallback(() => {
        if (isAndroid) {
            const bridge = window.AndroidBridge;
            if (bridge && currentPlaylistId.current) {
                bridge.cancelPlaylistDownload(currentPlaylistId.current.toString());
            }
        } else {
            playlistDownloadManager.cancelDownload();
        }

        setStatus('cancelled');
        setCurrentTask(null);
    }, [isAndroid]);

    /**
     * 获取缓存状态
     */
    const getCacheStatus = useCallback(async (playlistId: number): Promise<PlaylistDownloadState | null> => {
        if (isAndroid) {
            // Android 从 JsBridge 获取状态
            const bridge = window.AndroidBridge;
            if (bridge) {
                const json = bridge.getPlaylistCacheStatus(playlistId.toString());
                try {
                    const data = JSON.parse(json);
                    return {
                        playlistId,
                        version: '',
                        status: data.is_ready ? 'completed' : 'pending',
                        totalFiles: data.total_files,
                        completedFiles: data.cached_files,
                        failedFiles: 0,
                        progress: data.total_files > 0 ? Math.round((data.cached_files / data.total_files) * 100) : 0,
                        tasks: new Map(),
                    };
                } catch {
                    return null;
                }
            }
            return null;
        }

        return playlistDownloadManager.restoreDownload(playlistId);
    }, [isAndroid]);

    /**
     * 获取 Android 下载进度
     */
    const getAndroidDownloadProgress = useCallback((playlistId: number): number => {
        const bridge = window.AndroidBridge;
        if (bridge) {
            try {
                const json = bridge.getPlaylistCacheStatus(playlistId.toString());
                const data = JSON.parse(json);
                return data.total_files > 0 ? Math.round((data.cached_files / data.total_files) * 100) : 0;
            } catch {
                return 0;
            }
        }
        return 0;
    }, []);

    /**
     * 检查 Android 下载是否完成
     */
    const isAndroidDownloadComplete = useCallback((playlistId: number): boolean => {
        const bridge = window.AndroidBridge;
        if (bridge) {
            try {
                const json = bridge.getPlaylistCacheStatus(playlistId.toString());
                const data = JSON.parse(json);
                return data.is_ready;
            } catch {
                return false;
            }
        }
        return false;
    }, []);

    return {
        status,
        progress,
        completedFiles,
        totalFiles,
        failedFiles,
        currentTask,
        startDownload,
        cancelDownload,
        getCacheStatus,
        startAndroidDownload,
        getAndroidDownloadProgress,
        isAndroidDownloadComplete,
    };
};

export default usePlaylistDownload;
