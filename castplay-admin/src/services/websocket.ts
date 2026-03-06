/**
 * WebSocket Service
 * 实时通信服务
 */
import { io, Socket } from 'socket.io-client';
import { message } from 'antd';
import { wsLogger } from '../utils/logger';

type EventCallback = (...args: any[]) => void;

class WebSocketService {
  private socket: Socket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 3000;
  private eventCallbacks: Map<string, EventCallback[]> = new Map();

  constructor(url: string) {
    this.url = url;
  }

  /**
   * 连接 WebSocket
   */
  connect(): void {
    if (this.socket?.connected) {
      wsLogger.debug('WebSocket already connected');
      return;
    }

    this.socket = io(this.url, {
      transports: ['websocket'],
      reconnection: true,
      reconnectionAttempts: this.maxReconnectAttempts,
      reconnectionDelay: this.reconnectDelay,
    });

    this.setupEventListeners();
  }

  /**
   * 设置事件监听器
   */
  private setupEventListeners(): void {
    if (!this.socket) return;

    // 连接成功
    this.socket.on('connect', () => {
      wsLogger.info('WebSocket connected');
      this.reconnectAttempts = 0;
      message.success('实时连接已建立');
    });

    // 连接失败
    this.socket.on('connect_error', (error: Error) => {
      wsLogger.error('WebSocket connection error', error);
      this.reconnectAttempts++;

      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        message.error('无法连接到服务器，请检查网络');
      }
    });

    // 断开连接
    this.socket.on('disconnect', (reason: string) => {
      wsLogger.info('WebSocket disconnected', reason);
      if (reason === 'io server disconnect') {
        // 服务器主动断开，需要手动重连
        this.socket?.connect();
      }
    });

    // 设备状态更新
    this.socket.on('device_status_update', (data: any) => {
      wsLogger.debug('Device status update', data);
      this.emit('device_status_update', data);
    });

    // 播放列表更新
    this.socket.on('playlist_update', (data: any) => {
      wsLogger.debug('Playlist update', data);
      message.info(`播放列表已更新：${data.playlist_id}`);
      this.emit('playlist_update', data);
    });

    // 定时配置更新
    this.socket.on('schedule_update', (data: any) => {
      wsLogger.debug('Schedule update', data);
      message.info('定时配置已更新');
      this.emit('schedule_update', data);
    });

    // 媒体文件处理完成
    this.socket.on('media_processing_complete', (data: any) => {
      wsLogger.debug('Media processing complete', data);
      message.success(`媒体文件处理完成：${data.file_name}`);
      this.emit('media_processing_complete', data);
    });

    // 媒体文件处理失败
    this.socket.on('media_processing_failed', (data: any) => {
      wsLogger.warn('Media processing failed', data);
      message.error(`媒体文件处理失败：${data.file_name}`);
      this.emit('media_processing_failed', data);
    });
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  /**
   * 发送消息
   */
  send(event: string, data?: any): void {
    if (this.socket?.connected) {
      this.socket.emit(event, data);
    } else {
      wsLogger.warn('WebSocket not connected, cannot send message');
    }
  }

  /**
   * 订阅事件
   */
  on(event: string, callback: EventCallback): void {
    if (!this.eventCallbacks.has(event)) {
      this.eventCallbacks.set(event, []);
    }
    this.eventCallbacks.get(event)?.push(callback);
  }

  /**
   * 取消订阅
   */
  off(event: string, callback?: EventCallback): void {
    if (!callback) {
      this.eventCallbacks.delete(event);
      return;
    }

    const callbacks = this.eventCallbacks.get(event);
    if (callbacks) {
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  /**
   * 触发事件
   */
  private emit(event: string, data: any): void {
    const callbacks = this.eventCallbacks.get(event);
    if (callbacks) {
      callbacks.forEach((callback) => callback(data));
    }
  }

  /**
   * 检查连接状态
   */
  isConnected(): boolean {
    return this.socket?.connected || false;
  }
}

// 创建单例
const wsUrl = import.meta.env.VITE_WS_URL || 'http://localhost:5001';
const websocketService = new WebSocketService(wsUrl);

export default websocketService;
