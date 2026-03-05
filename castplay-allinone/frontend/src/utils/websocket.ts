/**
 * WebSocket 客户端
 * 使用原生 WebSocket API 与后端 FastAPI WebSocket 通信
 */
import type { WebSocketMessage } from '../types';

// WebSocket 基础 URL
// 使用类型断言处理 Vite 环境变量
const WS_BASE_URL = (typeof import.meta !== 'undefined' && (import.meta as { env?: { VITE_WS_URL?: string } }).env?.VITE_WS_URL)
  || `ws://${window.location.host}`;

// 消息处理器类型
type MessageHandler = (data: WebSocketMessage) => void;

class WebSocketClient {
  private socket: WebSocket | null = null;
  private deviceId: string | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 5000;
  private heartbeatInterval: ReturnType<typeof setInterval> | null = null;
  private messageHandlers: Map<string, MessageHandler[]> = new Map();
  private isManualClose = false;

  /**
   * 连接到 WebSocket 服务器
   * @param deviceId 设备 ID
   */
  connect(deviceId: string) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    this.deviceId = deviceId;
    this.isManualClose = false;
    const wsUrl = `${WS_BASE_URL}/ws/${deviceId}`;

    console.log('Connecting to WebSocket:', wsUrl);

    try {
      this.socket = new WebSocket(wsUrl);
      this.setupEventHandlers();
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.scheduleReconnect();
    }
  }

  /**
   * 设置 WebSocket 事件处理器
   */
  private setupEventHandlers() {
    if (!this.socket) return;

    this.socket.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.startHeartbeat();
    };

    this.socket.onclose = (event) => {
      console.log('WebSocket disconnected:', event.code, event.reason);
      this.stopHeartbeat();

      // 非手动关闭时尝试重连
      if (!this.isManualClose) {
        this.scheduleReconnect();
      }
    };

    this.socket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.socket.onmessage = (event) => {
      this.handleMessage(event.data);
    };
  }

  /**
   * 处理接收到的消息
   */
  private handleMessage(data: string) {
    try {
      const message: WebSocketMessage = JSON.parse(data);
      console.log('WebSocket message received:', message);

      // 根据消息类型触发对应的处理器
      const handlers = this.messageHandlers.get(message.event) || [];
      handlers.forEach(handler => handler(message));

      // 触发通用处理器
      const allHandlers = this.messageHandlers.get('*') || [];
      allHandlers.forEach(handler => handler(message));
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  }

  /**
   * 开始心跳
   */
  private startHeartbeat() {
    this.stopHeartbeat();
    this.heartbeatInterval = setInterval(() => {
      this.sendHeartbeat();
    }, 30000); // 每 30 秒发送一次心跳
  }

  /**
   * 停止心跳
   */
  private stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * 发送心跳
   */
  sendHeartbeat() {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.sendMessage({ type: 'heartbeat', timestamp: new Date().toISOString() });
    }
  }

  /**
   * 发送消息
   */
  sendMessage(data: Record<string, unknown>) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket is not connected');
    }
  }

  /**
   * 安排重连
   */
  private scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('Max reconnect attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * this.reconnectAttempts;
    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

    setTimeout(() => {
      if (this.deviceId && !this.isManualClose) {
        this.connect(this.deviceId);
      }
    }, delay);
  }

  /**
   * 注册消息处理器
   * @param event 事件类型 ('playlist_update', 'schedule_update', 'force_sync', 'reboot', '*')
   * @param handler 处理函数
   */
  on(event: string, handler: MessageHandler) {
    const handlers = this.messageHandlers.get(event) || [];
    handlers.push(handler);
    this.messageHandlers.set(event, handlers);
  }

  /**
   * 移除消息处理器
   */
  off(event: string, handler: MessageHandler) {
    const handlers = this.messageHandlers.get(event) || [];
    const index = handlers.indexOf(handler);
    if (index > -1) {
      handlers.splice(index, 1);
      this.messageHandlers.set(event, handlers);
    }
  }

  /**
   * 断开连接
   */
  disconnect() {
    this.isManualClose = true;
    this.stopHeartbeat();

    if (this.socket) {
      this.socket.close(1000, 'Client disconnect');
      this.socket = null;
    }

    console.log('WebSocket disconnected');
  }

  /**
   * 检查是否已连接
   */
  isConnected(): boolean {
    return this.socket?.readyState === WebSocket.OPEN;
  }

  /**
   * 获取当前连接状态
   */
  getReadyState(): number {
    return this.socket?.readyState ?? WebSocket.CLOSED;
  }
}

// 导出单例
export const wsClient = new WebSocketClient();

// 导出类以支持测试
export { WebSocketClient };
