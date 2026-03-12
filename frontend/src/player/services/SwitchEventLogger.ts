/**
 * 播放列表切换事件日志记录器
 *
 * 功能：
 * - 记录切换事件
 * - 记录下载进度
 * - 记录错误信息
 * - 提供日志查询接口
 */

// 切换事件类型
export type SwitchEventType =
    | 'switch_detected'      // 检测到切换
    | 'download_started'     // 开始下载
    | 'download_progress'    // 下载进度
    | 'download_completed'   // 下载完成
    | 'download_failed'      // 下载失败
    | 'switch_started'       // 开始切换
    | 'switch_completed'     // 切换完成
    | 'switch_failed'        // 切换失败
    | 'rollback_triggered'   // 触发回滚
    | 'error'                // 错误
    ;

// 切换事件日志
export interface SwitchEventLog {
    id: string;
    timestamp: string;
    type: SwitchEventType;
    playlistId: number | null;
    version: string | null;
    data: Record<string, unknown>;
    error?: string;
}

// 日志配置
const LOGGER_CONFIG = {
    // 最大日志条数
    MAX_LOGS: 500,
    // 本地存储 Key
    STORAGE_KEY: 'castplay_switch_logs',
    // 是否输出到控制台
    CONSOLE_OUTPUT: true,
};

class SwitchEventLogger {
    private logs: SwitchEventLog[] = [];
    private initialized: boolean = false;

    constructor() {
        this.init();
    }

    /**
     * 初始化，从本地存储恢复日志
     */
    private init(): void {
        if (this.initialized) return;

        try {
            const stored = localStorage.getItem(LOGGER_CONFIG.STORAGE_KEY);
            if (stored) {
                this.logs = JSON.parse(stored);
            }
        } catch (error) {
            console.error('[SwitchEventLogger] Failed to load logs:', error);
            this.logs = [];
        }

        this.initialized = true;
    }

    /**
     * 生成唯一 ID
     */
    private generateId(): string {
        return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * 保存日志到本地存储
     */
    private persist(): void {
        try {
            localStorage.setItem(
                LOGGER_CONFIG.STORAGE_KEY,
                JSON.stringify(this.logs)
            );
        } catch (error) {
            // 存储空间不足，清理旧日志
            if (this.logs.length > 50) {
                this.logs = this.logs.slice(-50);
                try {
                    localStorage.setItem(
                        LOGGER_CONFIG.STORAGE_KEY,
                        JSON.stringify(this.logs)
                    );
                } catch {
                    // 仍然失败，清除所有日志
                    this.logs = [];
                }
            }
        }
    }

    /**
     * 记录事件
     */
    log(
        type: SwitchEventType,
        data: {
            playlistId?: number | null;
            version?: string | null;
            error?: string;
            [key: string]: unknown;
        } = {}
    ): SwitchEventLog {
        const event: SwitchEventLog = {
            id: this.generateId(),
            timestamp: new Date().toISOString(),
            type,
            playlistId: data.playlistId ?? null,
            version: data.version ?? null,
            data: { ...data },
            error: data.error,
        };

        // 添加到日志列表
        this.logs.push(event);

        // 限制日志数量
        if (this.logs.length > LOGGER_CONFIG.MAX_LOGS) {
            this.logs = this.logs.slice(-LOGGER_CONFIG.MAX_LOGS);
        }

        // 持久化
        this.persist();

        // 控制台输出
        if (LOGGER_CONFIG.CONSOLE_OUTPUT) {
            const prefix = `[SwitchEvent:${type}]`;
            if (type === 'error' || type === 'switch_failed' || type === 'download_failed') {
                console.error(prefix, event);
            } else if (type === 'rollback_triggered') {
                console.warn(prefix, event);
            } else {
                console.log(prefix, event);
            }
        }

        return event;
    }

    /**
     * 记录切换检测
     */
    logSwitchDetected(playlistId: number, version: string): SwitchEventLog {
        return this.log('switch_detected', { playlistId, version });
    }

    /**
     * 记录下载开始
     */
    logDownloadStarted(playlistId: number, version: string, totalFiles: number): SwitchEventLog {
        return this.log('download_started', { playlistId, version, totalFiles });
    }

    /**
     * 记录下载进度
     */
    logDownloadProgress(
        playlistId: number,
        completed: number,
        total: number,
        percent: number
    ): SwitchEventLog {
        return this.log('download_progress', { playlistId, completed, total, percent });
    }

    /**
     * 记录下载完成
     */
    logDownloadCompleted(
        playlistId: number,
        version: string,
        successCount: number,
        failedCount: number
    ): SwitchEventLog {
        return this.log('download_completed', { playlistId, version, successCount, failedCount });
    }

    /**
     * 记录下载失败
     */
    logDownloadFailed(playlistId: number, error: string): SwitchEventLog {
        return this.log('download_failed', { playlistId, error });
    }

    /**
     * 记录切换开始
     */
    logSwitchStarted(playlistId: number, version: string): SwitchEventLog {
        return this.log('switch_started', { playlistId, version });
    }

    /**
     * 记录切换完成
     */
    logSwitchCompleted(playlistId: number, version: string): SwitchEventLog {
        return this.log('switch_completed', { playlistId, version });
    }

    /**
     * 记录切换失败
     */
    logSwitchFailed(playlistId: number, error: string): SwitchEventLog {
        return this.log('switch_failed', { playlistId, error });
    }

    /**
     * 记录回滚
     */
    logRollback(playlistId: number, reason: string): SwitchEventLog {
        return this.log('rollback_triggered', { playlistId, reason });
    }

    /**
     * 记录错误
     */
    logError(error: string, context?: Record<string, unknown>): SwitchEventLog {
        return this.log('error', { error, ...context });
    }

    /**
     * 获取所有日志
     */
    getLogs(): SwitchEventLog[] {
        return [...this.logs];
    }

    /**
     * 获取指定播放列表的日志
     */
    getLogsByPlaylist(playlistId: number): SwitchEventLog[] {
        return this.logs.filter(log => log.playlistId === playlistId);
    }

    /**
     * 获取最近的日志
     */
    getRecentLogs(count: number = 50): SwitchEventLog[] {
        return this.logs.slice(-count);
    }

    /**
     * 获取指定类型的日志
     */
    getLogsByType(type: SwitchEventType): SwitchEventLog[] {
        return this.logs.filter(log => log.type === type);
    }

    /**
     * 获取错误日志
     */
    getErrorLogs(): SwitchEventLog[] {
        return this.logs.filter(log =>
            log.type === 'error' ||
            log.type === 'switch_failed' ||
            log.type === 'download_failed'
        );
    }

    /**
     * 清除所有日志
     */
    clearLogs(): void {
        this.logs = [];
        localStorage.removeItem(LOGGER_CONFIG.STORAGE_KEY);
    }

    /**
     * 导出日志（用于调试）
     */
    exportLogs(): string {
        return JSON.stringify(this.logs, null, 2);
    }

    /**
     * 获取日志统计
     */
    getStats(): {
        total: number;
        byType: Record<SwitchEventType, number>;
        errors: number;
    } {
        const byType = {} as Record<SwitchEventType, number>;

        for (const log of this.logs) {
            byType[log.type] = (byType[log.type] || 0) + 1;
        }

        return {
            total: this.logs.length,
            byType,
            errors: this.getErrorLogs().length,
        };
    }
}

// 单例导出
export const switchEventLogger = new SwitchEventLogger();
