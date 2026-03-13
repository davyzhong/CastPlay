/**
 * 心跳上报 Hook
 * 每 2 小时上报一次播放端状态
 * 支持版本比对，检测播放列表更新
 */
import { useEffect, useCallback, useRef } from 'react';
import axios from 'axios';

// 常量定义
export const HEARTBEAT_INTERVAL_MS = 2 * 60 * 60 * 1000; // 2 小时
export const HEARTBEAT_TIMEOUT_MS = 5000; // 5 秒超时

interface HeartbeatData {
    device_id: string;
    current_playlist_id: number | null;
    current_playlist_version: string | null;
    last_media_id: number | null;
    status: 'playing' | 'idle' | 'paused';
    download_status?: DownloadStatus;
}

interface DownloadStatus {
    playlist_id: number;
    status: 'pending' | 'downloading' | 'completed' | 'failed';
    progress: number;
    completed_files: number;
    total_files: number;
}

// 与 usePlaylistChangeDetection 中的类型保持一致
interface PlaylistUpdateInfo {
    action: 'assign' | 'update' | 'remove' | 'activate';
    playlist_id: number;
    playlist_name: string;
    version: string;
    item_count: number;
    total_size?: number;
    priority?: 'high' | 'normal' | 'low';
    changes?: {
        added?: number[];
        removed?: number[];
        reordered?: boolean;
    };
}

interface HeartbeatResponse {
    acknowledged: boolean;
    server_time: string;
    playlist_update: PlaylistUpdateInfo | null;
}

interface UseHeartbeatOptions {
    deviceId: string | null;
    currentPlaylistId: number | null;
    currentPlaylistVersion: string | null;
    lastMediaId: number | null;
    playbackStatus: 'playing' | 'idle' | 'paused';
    downloadStatus?: DownloadStatus;
    onPlaylistUpdate?: (update: PlaylistUpdateInfo) => void;
}

export const useHeartbeat = (options: UseHeartbeatOptions) => {
    const {
        deviceId,
        currentPlaylistId,
        currentPlaylistVersion,
        lastMediaId,
        playbackStatus,
        downloadStatus,
        onPlaylistUpdate
    } = options;

    const intervalRef = useRef<NodeJS.Timeout | null>(null);

    /**
     * 发送心跳
     */
    const sendHeartbeat = useCallback(async () => {
        if (!deviceId) return;

        const payload: HeartbeatData = {
            device_id: deviceId,
            current_playlist_id: currentPlaylistId,
            current_playlist_version: currentPlaylistVersion,
            last_media_id: lastMediaId,
            status: playbackStatus,
            ...(downloadStatus && { download_status: downloadStatus })
        };

        try {
            const response = await axios.post<HeartbeatResponse>('/api/player/heartbeat', payload, {
                timeout: HEARTBEAT_TIMEOUT_MS
            });

            console.log('Heartbeat sent successfully');

            // 检查是否有播放列表更新
            if (response.data.playlist_update && onPlaylistUpdate) {
                console.log('Playlist update detected:', response.data.playlist_update);
                onPlaylistUpdate(response.data.playlist_update);
            }
        } catch (error) {
            // 静默失败，不影响播放
            console.debug('Heartbeat failed (offline):', error);
        }
    }, [deviceId, currentPlaylistId, currentPlaylistVersion, lastMediaId, playbackStatus, downloadStatus, onPlaylistUpdate]);

    // 启动定时任务
    useEffect(() => {
        if (!deviceId) return;

        // 立即发送一次（启动时）
        sendHeartbeat();

        // 定时发送
        intervalRef.current = setInterval(sendHeartbeat, HEARTBEAT_INTERVAL_MS);

        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current);
            }
        };
    }, [deviceId, sendHeartbeat]);

    // 页面关闭前发送最后一次心跳
    useEffect(() => {
        const handleBeforeUnload = () => {
            if (navigator.sendBeacon && deviceId) {
                // 使用 sendBeacon 确保离线也能发送
                const blob = new Blob([JSON.stringify({
                    device_id: deviceId,
                    current_playlist_id: currentPlaylistId,
                    current_playlist_version: currentPlaylistVersion,
                    status: 'offline'
                })], { type: 'application/json' });
                navigator.sendBeacon('/api/player/heartbeat', blob);
            }
        };

        window.addEventListener('beforeunload', handleBeforeUnload);
        return () => window.removeEventListener('beforeunload', handleBeforeUnload);
    }, [deviceId, currentPlaylistId, currentPlaylistVersion]);
};
