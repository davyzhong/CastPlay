/**
 * 心跳上报 Hook
 * 每 2 小时上报一次播放端状态
 */
import { useEffect, useCallback, useRef } from 'react';
import axios from 'axios';

// 常量定义
export const HEARTBEAT_INTERVAL_MS = 2 * 60 * 60 * 1000; // 2 小时
export const HEARTBEAT_TIMEOUT_MS = 5000; // 5 秒超时

interface HeartbeatData {
    device_id: string;
    current_playlist_id: number | null;
    last_media_id: number | null;
    status: 'playing' | 'idle' | 'paused';
}

export const useHeartbeat = (
    deviceId: string | null,
    currentPlaylistId: number | null,
    lastMediaId: number | null,
    playbackStatus: 'playing' | 'idle' | 'paused'
) => {
    const intervalRef = useRef<NodeJS.Timeout | null>(null);

    /**
     * 发送心跳
     */
    const sendHeartbeat = useCallback(async () => {
        if (!deviceId) return;

        const payload: HeartbeatData = {
            device_id: deviceId,
            current_playlist_id: currentPlaylistId,
            last_media_id: lastMediaId,
            status: playbackStatus
        };

        try {
            await axios.post('/api/player/heartbeat', payload, {
                timeout: HEARTBEAT_TIMEOUT_MS
            });
            console.log('Heartbeat sent successfully');
        } catch (error) {
            // 静默失败，不影响播放
            console.debug('Heartbeat failed (offline):', error);
        }
    }, [deviceId, currentPlaylistId, lastMediaId, playbackStatus]);

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
                    status: 'offline'
                })], { type: 'application/json' });
                navigator.sendBeacon('/api/player/heartbeat', blob);
            }
        };

        window.addEventListener('beforeunload', handleBeforeUnload);
        return () => window.removeEventListener('beforeunload', handleBeforeUnload);
    }, [deviceId]);
};
