/**
 * 播放列表变更感知 Hook
 *
 * 统一处理播放列表变更检测，支持两种感知方式：
 * 1. WebSocket 实时推送（主方案）
 * 2. 心跳版本比对（兜底方案）
 */
import { useEffect, useCallback, useState, useRef } from 'react';
import { useHeartbeat } from './useHeartbeat';

// 播放列表更新信息
export interface PlaylistUpdateInfo {
    action: 'switch' | 'check';
    playlist_id: number;
    playlist_name: string;
    version: string;
    media_count: number;
    priority?: 'high' | 'normal' | 'low';
    switch_policy?: {
        mode: string;
        min_ready_ratio: number;
        download_timeout_ms: number;
    };
}

// 下载状态
export interface DownloadStatus {
    playlist_id: number;
    status: 'pending' | 'downloading' | 'completed' | 'failed';
    progress: number;
    completed_files: number;
    total_files: number;
}

// WebSocket 消息类型
interface WebSocketMessage {
    type: string;
    device_id?: string;
    timestamp: string;
    data?: PlaylistUpdateInfo | Record<string, unknown>;
}

// 配置
export interface PlaylistChangeDetectionConfig {
    deviceId: string | null;
    currentPlaylistId: number | null;
    currentPlaylistVersion: string | null;
    wsUrl?: string | null;

    // 回调
    onPlaylistAssigned?: (info: PlaylistUpdateInfo) => void;
    onPlaylistUpdated?: (info: PlaylistUpdateInfo) => void;
    onForceSync?: () => void;
}

// 感知状态
export interface DetectionState {
    lastDetectionTime: Date | null;
    lastDetectionSource: 'websocket' | 'heartbeat' | null;
    pendingUpdate: PlaylistUpdateInfo | null;
    isConnected: boolean;
}

export const usePlaylistChangeDetection = (
    config: PlaylistChangeDetectionConfig
) => {
    const {
        deviceId,
        currentPlaylistId,
        currentPlaylistVersion,
        wsUrl,
        onPlaylistAssigned,
        onPlaylistUpdated,
        onForceSync
    } = config;

    const [detectionState, setDetectionState] = useState<DetectionState>({
        lastDetectionTime: null,
        lastDetectionSource: null,
        pendingUpdate: null,
        isConnected: false
    });

    const [downloadStatus, setDownloadStatus] = useState<DownloadStatus | null>(null);
    const wsRef = useRef<WebSocket | null>(null);
    const reconnectAttemptsRef = useRef(0);
    const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    // 使用 ref 存储回调，避免依赖数组变化导致 WebSocket 重连
    const callbacksRef = useRef({
        onPlaylistAssigned,
        onPlaylistUpdated,
        onForceSync
    });

    // 更新 callbacks ref（不触发重渲染）
    callbacksRef.current = {
        onPlaylistAssigned,
        onPlaylistUpdated,
        onForceSync
    };

    /**
     * 处理检测到的播放列表更新
     */
    const handlePlaylistUpdate = useCallback((update: PlaylistUpdateInfo, source: 'websocket' | 'heartbeat') => {
        console.log(`[PlaylistDetection] Update detected via ${source}:`, update);

        setDetectionState(prev => ({
            ...prev,
            lastDetectionTime: new Date(),
            lastDetectionSource: source,
            pendingUpdate: update
        }));

        // 触发回调（使用 ref 避免依赖变化）
        if (update.action === 'switch' && callbacksRef.current.onPlaylistAssigned) {
            callbacksRef.current.onPlaylistAssigned(update);
        } else if (update.action === 'check' && callbacksRef.current.onPlaylistUpdated) {
            callbacksRef.current.onPlaylistUpdated(update);
        }
    }, []);

    /**
     * 处理 WebSocket 消息
     */
    const handleWsMessage = useCallback((event: MessageEvent) => {
        try {
            const message: WebSocketMessage = JSON.parse(event.data);

            switch (message.type) {
                case 'playlist_assigned':
                case 'playlist_updated':
                    if (message.data) {
                        handlePlaylistUpdate(message.data as PlaylistUpdateInfo, 'websocket');
                    }
                    break;

                case 'force_sync':
                    console.log('[PlaylistDetection] Force sync received');
                    if (callbacksRef.current.onForceSync) {
                        callbacksRef.current.onForceSync();
                    }
                    break;

                case 'schedule_updated':
                    console.log('[PlaylistDetection] Schedule update received');
                    break;

                case 'control':
                    // 控制指令由 useRemoteControl 处理
                    break;

                default:
                    console.debug('[PlaylistDetection] Unknown message type:', message.type);
            }
        } catch (error) {
            console.error('[PlaylistDetection] Failed to parse WebSocket message:', error);
        }
    }, [handlePlaylistUpdate]);

    /**
     * 连接 WebSocket
     */
    const connectWebSocket = useCallback(() => {
        if (!wsUrl || !deviceId) {
            console.log('[PlaylistDetection] Skipping WebSocket connection: wsUrl or deviceId not available');
            return;
        }

        // 验证 wsUrl 格式是否正确（必须包含主机名）
        if (!wsUrl.match(/^wss?:\/\/[^/]+/)) {
            console.warn('[PlaylistDetection] Invalid wsUrl format:', wsUrl, '- skipping connection');
            return;
        }

        if (wsRef.current?.readyState === WebSocket.OPEN) {
            return;
        }

        try {
            const fullWsUrl = `${wsUrl}/ws/${deviceId}`;
            console.log('[PlaylistDetection] Connecting to WebSocket:', fullWsUrl);
            wsRef.current = new WebSocket(fullWsUrl);

            wsRef.current.onopen = () => {
                console.log('[PlaylistDetection] WebSocket connected');
                reconnectAttemptsRef.current = 0;
                setDetectionState(prev => ({ ...prev, isConnected: true }));

                // 发送注册消息
                wsRef.current?.send(JSON.stringify({
                    type: 'register',
                    device_id: deviceId
                }));
            };

            wsRef.current.onmessage = handleWsMessage;

            wsRef.current.onerror = (error) => {
                console.error('[PlaylistDetection] WebSocket error:', error);
            };

            wsRef.current.onclose = (event) => {
                console.log('[PlaylistDetection] WebSocket closed:', event.code);
                wsRef.current = null;
                setDetectionState(prev => ({ ...prev, isConnected: false }));

                // 尝试重连
                if (reconnectAttemptsRef.current < 10) {
                    const delay = 5000 * Math.min(reconnectAttemptsRef.current + 1, 5);
                    reconnectTimerRef.current = setTimeout(() => {
                        reconnectAttemptsRef.current++;
                        connectWebSocket();
                    }, delay);
                }
            };
        } catch (error) {
            console.error('[PlaylistDetection] Failed to create WebSocket:', error);
        }
    }, [wsUrl, deviceId, handleWsMessage]);

    /**
     * 断开 WebSocket
     */
    const disconnectWebSocket = useCallback(() => {
        if (reconnectTimerRef.current) {
            clearTimeout(reconnectTimerRef.current);
            reconnectTimerRef.current = null;
        }

        if (wsRef.current) {
            wsRef.current.close(1000, 'Manual disconnect');
            wsRef.current = null;
        }
    }, []);

    /**
     * 发送下载进度
     */
    const reportDownloadProgress = useCallback((status: DownloadStatus) => {
        setDownloadStatus(status);

        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({
                type: 'download_progress',
                ...status
            }));
        }
    }, []);

    /**
     * 确认播放列表切换完成
     */
    const acknowledgeSwitch = useCallback((playlistId: number, version: string) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({
                type: 'playlist_switched',
                playlist_id: playlistId,
                version: version
            }));
        }

        // 清除待处理更新
        setDetectionState(prev => ({
            ...prev,
            pendingUpdate: null
        }));
    }, []);

    // 心跳回调 - 处理心跳返回的播放列表更新
    const handleHeartbeatUpdate = useCallback((update: PlaylistUpdateInfo) => {
        // 只有在 WebSocket 未连接时才使用心跳检测结果
        if (!detectionState.isConnected) {
            handlePlaylistUpdate(update, 'heartbeat');
        }
    }, [detectionState.isConnected, handlePlaylistUpdate]);

    // 使用心跳 Hook
    useHeartbeat({
        deviceId,
        currentPlaylistId,
        currentPlaylistVersion,
        lastMediaId: null,
        playbackStatus: 'playing',
        downloadStatus: downloadStatus || undefined,
        onPlaylistUpdate: handleHeartbeatUpdate
    });

    // 初始化 WebSocket 连接
    useEffect(() => {
        connectWebSocket();

        return () => {
            disconnectWebSocket();
        };
    }, [connectWebSocket, disconnectWebSocket]);

    // 页面可见性变化时重连
    useEffect(() => {
        const handleVisibilityChange = () => {
            if (document.visibilityState === 'visible') {
                if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
                    reconnectAttemptsRef.current = 0;
                    connectWebSocket();
                }
            }
        };

        document.addEventListener('visibilitychange', handleVisibilityChange);
        return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
    }, [connectWebSocket]);

    return {
        // 状态
        detectionState,
        isConnected: detectionState.isConnected,

        // 方法
        reportDownloadProgress,
        acknowledgeSwitch,

        // 手动触发检测
        forceCheck: () => {
            // 触发心跳检测
            // 心跳 Hook 会自动处理
        }
    };
};

export default usePlaylistChangeDetection;
