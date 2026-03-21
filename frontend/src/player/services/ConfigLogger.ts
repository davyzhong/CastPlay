/**
 * 配置日志服务
 * 提供统一的配置操作日志记录
 */

export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

export interface LogEntry {
  timestamp: string;
  level: LogLevel;
  category: string;
  message: string;
  data?: Record<string, unknown>;
  error?: Error;
}

/**
 * 配置日志类
 */
class ConfigLogger {
  private static instance: ConfigLogger;
  private logs: LogEntry[] = [];
  private maxLogs: number = 1000;
  private enabled: boolean = true;
  private logToConsole: boolean = true;
  private deviceId: string | null = null;

  private constructor() {}

  static getInstance(): ConfigLogger {
    if (!ConfigLogger.instance) {
      ConfigLogger.instance = new ConfigLogger();
    }
    return ConfigLogger.instance;
  }

  /**
   * 初始化日志器
   */
  init(options: {
    deviceId?: string;
    enabled?: boolean;
    logToConsole?: boolean;
    maxLogs?: number;
  } = {}): void {
    this.deviceId = options.deviceId || null;
    this.enabled = options.enabled ?? true;
    this.logToConsole = options.logToConsole ?? true;
    this.maxLogs = options.maxLogs ?? 1000;

    this.info('ConfigLogger', 'Logger initialized', {
      deviceId: this.deviceId,
      enabled: this.enabled,
      logToConsole: this.logToConsole,
    });
  }

  /**
   * 设置设备 ID
   */
  setDeviceId(deviceId: string): void {
    this.deviceId = deviceId;
  }

  /**
   * 启用/禁用日志
   */
  setEnabled(enabled: boolean): void {
    this.enabled = enabled;
  }

  /**
   * 记录日志
   */
  private log(
    level: LogLevel,
    category: string,
    message: string,
    data?: Record<string, unknown>,
    error?: Error
  ): void {
    if (!this.enabled) return;

    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      category,
      message,
      data: data ? this.sanitizeData(data) : undefined,
      error,
    };

    // 添加到内存日志
    this.logs.push(entry);

    // 限制日志数量
    if (this.logs.length > this.maxLogs) {
      this.logs = this.logs.slice(-this.maxLogs);
    }

    // 输出到控制台
    if (this.logToConsole) {
      const prefix = `[ConfigLogger][${category}]`;
      const logData = data ? JSON.stringify(data, null, 2) : '';

      switch (level) {
        case 'debug':
          console.debug(prefix, message, logData);
          break;
        case 'info':
          console.info(prefix, message, logData);
          break;
        case 'warn':
          console.warn(prefix, message, logData);
          break;
        case 'error':
          console.error(prefix, message, logData, error || '');
          break;
      }
    }
  }

  /**
   * 清理敏感数据
   */
  private sanitizeData(data: Record<string, unknown>): Record<string, unknown> {
    const sanitized = { ...data };
    const sensitiveKeys = ['password', 'token', 'secret', 'key', 'credential'];

    for (const key of Object.keys(sanitized)) {
      if (sensitiveKeys.some(sk => key.toLowerCase().includes(sk))) {
        sanitized[key] = '***REDACTED***';
      }
    }

    return sanitized;
  }

  // ==================== 公共日志方法 ====================

  debug(category: string, message: string, data?: Record<string, unknown>): void {
    this.log('debug', category, message, data);
  }

  info(category: string, message: string, data?: Record<string, unknown>): void {
    this.log('info', category, message, data);
  }

  warn(category: string, message: string, data?: Record<string, unknown>): void {
    this.log('warn', category, message, data);
  }

  error(category: string, message: string, error?: Error, data?: Record<string, unknown>): void {
    this.log('error', category, message, data, error);
  }

  // ==================== 配置操作日志方法 ====================

  /**
   * 记录服务器配置操作
   */
  logServerConfig(action: 'load' | 'save' | 'validate' | 'test' | 'clear', data?: Record<string, unknown>): void {
    this.info('ServerConfig', `Server config ${action}`, data);
  }

  /**
   * 记录设备注册操作
   */
  logDeviceRegistration(action: 'start' | 'complete' | 'fail' | 'skip', data?: Record<string, unknown>): void {
    const level = action === 'fail' ? 'error' : 'info';
    this.log(level, 'DeviceRegistration', `Device registration ${action}`, data);
  }

  /**
   * 记录注册码操作
   */
  logRegistrationCode(action: 'display' | 'copy' | 'verify', data?: Record<string, unknown>): void {
    this.info('RegistrationCode', `Registration code ${action}`, data);
  }

  /**
   * 记录播放列表选择操作
   */
  logPlaylistSelection(action: 'show' | 'select' | 'deselect' | 'confirm' | 'skip', data?: Record<string, unknown>): void {
    this.info('PlaylistSelection', `Playlist selection ${action}`, data);
  }

  /**
   * 记录存储操作
   */
  logStorage(action: 'get' | 'set' | 'remove' | 'clear', key: string, data?: Record<string, unknown>): void {
    this.debug('Storage', `Storage ${action}: ${key}`, data);
  }

  /**
   * 记录网络操作
   */
  logNetwork(action: 'request' | 'response' | 'error', data?: Record<string, unknown>): void {
    const level = action === 'error' ? 'error' : 'debug';
    this.log(level, 'Network', `Network ${action}`, data);
  }

  // ==================== 日志管理方法 ====================

  /**
   * 获取所有日志
   */
  getLogs(): LogEntry[] {
    return [...this.logs];
  }

  /**
   * 获取指定级别的日志
   */
  getLogsByLevel(level: LogLevel): LogEntry[] {
    return this.logs.filter(log => log.level === level);
  }

  /**
   * 获取指定类别的日志
   */
  getLogsByCategory(category: string): LogEntry[] {
    return this.logs.filter(log => log.category === category);
  }

  /**
   * 清除日志
   */
  clearLogs(): void {
    this.logs = [];
    this.info('ConfigLogger', 'Logs cleared');
  }

  /**
   * 导出日志为 JSON
   */
  exportLogs(): string {
    const exportData = {
      deviceId: this.deviceId,
      exportedAt: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      logs: this.logs,
    };
    return JSON.stringify(exportData, null, 2);
  }

  /**
   * 下载日志文件
   */
  downloadLogs(): void {
    const logsJson = this.exportLogs();
    const blob = new Blob([logsJson], { type: 'application/json' });
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.href = url;
    link.download = `config-logs-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    this.info('ConfigLogger', 'Logs downloaded');
  }

  /**
   * 获取日志统计
   */
  getStats(): {
    total: number;
    byLevel: Record<LogLevel, number>;
    byCategory: Record<string, number>;
    oldestTimestamp: string | null;
    newestTimestamp: string | null;
  } {
    const byLevel: Record<LogLevel, number> = {
      debug: 0,
      info: 0,
      warn: 0,
      error: 0,
    };

    const byCategory: Record<string, number> = {};

    for (const log of this.logs) {
      byLevel[log.level]++;
      byCategory[log.category] = (byCategory[log.category] || 0) + 1;
    }

    return {
      total: this.logs.length,
      byLevel,
      byCategory,
      oldestTimestamp: this.logs[0]?.timestamp || null,
      newestTimestamp: this.logs[this.logs.length - 1]?.timestamp || null,
    };
  }
}

// 导出单例
export const configLogger = ConfigLogger.getInstance();
export default configLogger;
