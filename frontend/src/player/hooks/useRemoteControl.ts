/**
 * 远程控制 Hook
 * 处理 WebSocket 远程控制指令
 */
import { useEffect, useCallback, useRef } from 'react';
import { ErrorReporter } from '../services/ErrorReporter';

// 控制指令类型
export type ControlAction =
    | 'pause'
    | 'resume'
    | 'volume'
    | 'reload'
    | 'seek'
    | 'next'
    | 'prev'
    | 'switch_playlist';

// 播放列表更新信息
export interface PlaylistUpdateData {
    playlist_id: number;
    playlist_name: string;
    version: string;
    action: string;
    item_count?: number;
    total_size?: number;
    priority?: 'high' | 'normal' | 'low';
    changes?: Record<string, unknown>;
}

// WebSocket 消息类型
interface WebSocketMessage {
    type: string;
    event?: string;
    action?: ControlAction;
    volume?: number;
    position?: number;
    playlist_id?: number;
    timestamp: string;
    data?: PlaylistUpdateData | Record<string, unknown>;
}

// 控制回调接口
export interface ControlCallbacks {
    onPause: () => void;
    onResume: () => void;
    onVolumeChange: (volume: number) => void;
    onReload: () => void;
    onSeek: (position: number) => void;
    onNext: () => void;
    onPrev: () => void;
    onSwitchPlaylist: (playlistId: number) => void;
    // 新增：播放列表变更回调
    onPlaylistAssigned?: (data: PlaylistUpdateData) => void;
    onPlaylistUpdated?: (data: PlaylistUpdateData) => void;
    onPlaylistRemoved?: (playlistId: number) => void;
    onForceSync?: () => void;
}

// 配置
interface UseRemoteControlConfig {
    wsUrl: string | null;
    deviceId: string | null;
    reconnectInterval: number;
    maxReconnectAttempts: number;
}

const DEFAULT_CONFIG: UseRemoteControlConfig = {
    wsUrl: null,
    deviceId: null,
    reconnectInterval: 5000,
    maxReconnectAttempts: 10
};

export const useRemoteControl = (
    callbacks: ControlCallbacks,
    config: Partial<UseRemoteControlConfig> = {}
) => {
    const fullConfig = { ...DEFAULT_CONFIG, ...config };
    const wsRef = useRef<WebSocket | null>(null);
    const reconnectAttemptsRef = useRef(0);
    const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    // 处理接收到的消息
    const handleMessage = useCallback((event: MessageEvent) => {
        try {
            const message: WebSocketMessage = JSON.parse(event.data);

            // 统一消息格式：支持 type 和 event 两种格式
            const msgType = message.type || message.event;

            switch (msgType) {
                case 'control':
                    if (message.action) {
                        handleControlMessage(message);
                    }
                    break;

                case 'playlist_assigned':
                    console.log('[RemoteControl] Playlist assigned:', message.data);
                    if (message.data && callbacks.onPlaylistAssigned) {
                        callbacks.onPlaylistAssigned(message.data as PlaylistUpdateData);
                    }
                    break;

                case 'playlist_updated':
                    console.log('[RemoteControl] Playlist updated:', message.data);
                    if (message.data && callbacks.onPlaylistUpdated) {
                        callbacks.onPlaylistUpdated(message.data as PlaylistUpdateData);
                    }
                    break;

                case 'playlist_removed':
                    console.log('[RemoteControl] Playlist removed:', message.data);
                    if (message.data && callbacks.onPlaylistRemoved) {
                        callbacks.onPlaylistRemoved((message.data as { playlist_id: number }).playlist_id);
                    }
                    break;

                case 'playlist_update':
                case 'force_sync':
                    console.log('[RemoteControl] Force sync received');
                    if (callbacks.onForceSync) {
                        callbacks.onForceSync();
                    } else {
                        callbacks.onReload();
                    }
                    break;

                case 'schedule_update':
                    console.log('[RemoteControl] Schedule update received');
                    break;

                case 'reboot':
                    console.log('[RemoteControl] Reboot command received');
                    window.location.reload();
                    break;

                default:
                    console.debug('[RemoteControl] Unknown message type:', msgType);
            }
        } catch (error) {
            console.error('[RemoteControl] Failed to parse message:', error);
        }
    }, [callbacks]);

    // 处理控制消息
    const handleControlMessage = useCallback((message: WebSocketMessage) => {
        const { action, volume, position, playlist_id } = message;

        console.log(`[RemoteControl] Control action: ${action}`);

        switch (action) {
            case 'pause':
                callbacks.onPause();
                break;

            case 'resume':
                callbacks.onResume();
                break;

            case 'volume':
                if (typeof volume === 'number') {
                    callbacks.onVolumeChange(volume);
                }
                break;

            case 'reload':
                callbacks.onReload();
                break;

            case 'seek':
                if (typeof position === 'number') {
                    callbacks.onSeek(position);
                }
                break;

            case 'next':
                callbacks.onNext();
                break;

            case 'prev':
                callbacks.onPrev();
                break;

            case 'switch_playlist':
                if (typeof playlist_id === 'number') {
                    callbacks.onSwitchPlaylist(playlist_id);
                }
                break;

            default:
                console.warn(`[RemoteControl] Unknown action: ${action}`);
        }
    }, [callbacks]);

    // 连接 WebSocket
    const connect = useCallback(() => {
        if (!fullConfig.wsUrl || !fullConfig.deviceId) {
            console.log('[RemoteControl] No WebSocket URL or device ID');
            return;
        }

        if (wsRef.current?.readyState === WebSocket.OPEN) {
            console.log('[RemoteControl] Already connected');
            return;
        }

        try {
            const wsUrl = `${fullConfig.wsUrl}?device_id=${fullConfig.deviceId}`;
            wsRef.current = new WebSocket(wsUrl);

            wsRef.current.onopen = () => {
                console.log('[RemoteControl] WebSocket connected');
                reconnectAttemptsRef.current = 0;

                // 发送设备注册消息
                wsRef.current?.send(JSON.stringify({
                    type: 'register',
                    device_id: fullConfig.deviceId
                }));
            };

            wsRef.current.onmessage = handleMessage;

            wsRef.current.onerror = (error) => {
                console.error('[RemoteControl] WebSocket error:', error);
                ErrorReporter.report('network_error', 'WebSocket connection error');
            };

            wsRef.current.onclose = (event) => {
                console.log('[RemoteControl] WebSocket closed:', event.code, event.reason);
                wsRef.current = null;

                // 尝试重连
                if (reconnectAttemptsRef.current < fullConfig.maxReconnectAttempts) {
                    scheduleReconnect();
                } else {
                    console.error('[RemoteControl] Max reconnect attempts reached');
                    ErrorReporter.report('network_error', 'WebSocket max reconnect attempts reached');
                }
            };
        } catch (error) {
            console.error('[RemoteControl] Failed to create WebSocket:', error);
            ErrorReporter.report('network_error', `WebSocket creation failed: ${error}`);
        }
    }, [fullConfig.wsUrl, fullConfig.deviceId, fullConfig.maxReconnectAttempts, handleMessage]);

    // 调度重连
    const scheduleReconnect = useCallback(() => {
        if (reconnectTimerRef.current) {
            clearTimeout(reconnectTimerRef.current);
        }

        reconnectAttemptsRef.current++;
        const delay = fullConfig.reconnectInterval * Math.min(reconnectAttemptsRef.current, 5);

        console.log(`[RemoteControl] Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current})`);

        reconnectTimerRef.current = setTimeout(() => {
            connect();
        }, delay);
    }, [connect, fullConfig.reconnectInterval]);

    // 断开连接
    const disconnect = useCallback(() => {
        if (reconnectTimerRef.current) {
            clearTimeout(reconnectTimerRef.current);
            reconnectTimerRef.current = null;
        }

        if (wsRef.current) {
            wsRef.current.close(1000, 'Manual disconnect');
            wsRef.current = null;
        }
    }, []);

    // 发送消息
    const sendMessage = useCallback((message: Record<string, unknown>) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify(message));
            return true;
        }
        console.warn('[RemoteControl] WebSocket not connected');
        return false;
    }, []);

    // 上报状态
    const reportStatus = useCallback((status: {
        isPlaying: boolean;
        currentIndex: number;
        playlistId?: number;
        mediaId?: number;
    }) => {
        sendMessage({
            type: 'status',
            ...status
        });
    }, [sendMessage]);

    // 初始化和清理
    useEffect(() => {
        connect();

        return () => {
            disconnect();
        };
    }, [connect, disconnect]);

    // 页面可见性变化时重连
    useEffect(() => {
        const handleVisibilityChange = () => {
            if (document.visibilityState === 'visible') {
                if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
                    console.log('[RemoteControl] Page visible, reconnecting...');
                    reconnectAttemptsRef.current = 0;
                    connect();
                }
            }
        };

        document.addEventListener('visibilitychange', handleVisibilityChange);

        return () => {
            document.removeEventListener('visibilitychange', handleVisibilityChange);
        };
    }, [connect]);

    return {
        isConnected: wsRef.current?.readyState === WebSocket.OPEN,
        connect,
        disconnect,
        sendMessage,
        reportStatus
    };
};

export default useRemoteControl;
