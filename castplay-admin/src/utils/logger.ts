/**
 * Logger Utility
 * 统一的日志管理工具
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

class Logger {
  private enabled: boolean;
  private level: LogLevel;

  constructor(enabled?: boolean, level?: LogLevel) {
    // 生产环境默认关闭 debug 日志
    this.enabled = enabled ?? import.meta.env.DEV;
    this.level = level ?? (import.meta.env.DEV ? 'debug' : 'warn');
  }

  private shouldLog(level: LogLevel): boolean {
    if (!this.enabled) return false;

    const levels: LogLevel[] = ['debug', 'info', 'warn', 'error'];
    return levels.indexOf(level) >= levels.indexOf(this.level);
  }

  debug(message: string, ...args: any[]): void {
    if (this.shouldLog('debug')) {
      console.debug(`[DEBUG] ${new Date().toISOString()} - ${message}`, ...args);
    }
  }

  info(message: string, ...args: any[]): void {
    if (this.shouldLog('info')) {
      console.info(`[INFO] ${new Date().toISOString()} - ${message}`, ...args);
    }
  }

  warn(message: string, ...args: any[]): void {
    if (this.shouldLog('warn')) {
      console.warn(`[WARN] ${new Date().toISOString()} - ${message}`, ...args);
    }
  }

  error(message: string, ...args: any[]): void {
    if (this.shouldLog('error')) {
      console.error(`[ERROR] ${new Date().toISOString()} - ${message}`, ...args);
    }
  }
}

// 创建默认实例
export const logger = new Logger();

// 导出不同用途的 logger
export const apiLogger = new Logger(import.meta.env.DEV, 'info');
export const wsLogger = new Logger(import.meta.env.DEV, 'info');
export const uiLogger = new Logger(import.meta.env.DEV, 'warn');
