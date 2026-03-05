/**
 * WebSocket 客户端
 */
import { io, Socket } from 'socket.io-client';
import type { WebSocketMessage } from '../types';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:5000/ws';

class WebSocketClient {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 5000;

  connect(deviceId: string) {
    console.log('Connecting to WebSocket for device:', deviceId);

    // 创建连接
    this.socket = io(WS_URL, {
      transports: ['websocket', 'polling'],
      query: { device_id: deviceId },
      reconnection: true,
      reconnectionDelay: this.reconnectDelay,
      reconnectionAttempts: this.maxReconnectAttempts,
    });

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
    });

    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
    });

    this.socket.on('error', (error) => {
      console.error('WebSocket error:', error);
    });

    // 监听服务器推送的消息
    this.setupMessageHandlers();
  }

  private setupMessageHandlers() {
    if (!this.socket) return;

    // 播放列表更新
    this.socket.on('playlist_update', (data: WebSocketMessage) => {
      console.log('Playlist update received:', data);
      // 可以在这里触发 UI 更新，如刷新播放列表
      if (data.event === 'playlist_update') {
        // 通知用户需要重新同步
        alert('播放列表已更新，建议重新同步设备');
      }
    });

    // 定时配置更新
    this.socket.on('schedule_update', (data: WebSocketMessage) => {
      console.log('Schedule update received:', data);
      // 更新设备定时配置
    });

    // 强制同步
    this.socket.on('force_sync', (data: WebSocketMessage) => {
      console.log('Force sync received:', data);
    });

    // 重启命令
    this.socket.on('reboot', (data: WebSocketMessage) => {
      console.log('Reboot command received:', data);
    });

    // 心跳确认
    this.socket.on('heartbeat_ack', (data: WebSocketMessage) => {
      console.log('Heartbeat ack:', data.timestamp);
    });
  }

  sendHeartbeat() {
    if (this.socket?.connected) {
      this.socket.emit('heartbeat', { timestamp: new Date().toISOString() });
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      console.log('WebSocket disconnected');
    }
  }

  isConnected(): boolean {
    return this.socket?.connected || false;
  }
}

export const wsClient = new WebSocketClient();
