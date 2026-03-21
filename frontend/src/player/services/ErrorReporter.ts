/**
 * 错误上报服务
 * 统一收集和上报播放端错误
 */
import axios from 'axios';

// 错误类型定义
export type ErrorType =
    | 'download_failed'
    | 'playback_error'
    | 'cache_error'
    | 'network_error'
    | 'playlist_sync_failed'
    | 'registration_failed'
    | 'insufficient_storage'
    | 'switch_failed'
    | 'media_load_error'
    | 'unknown_error';

// 错误上报数据结构
interface ErrorReport {
    device_id: string;
    type: ErrorType;
    message: string;
    playlist_id?: number | null;
    media_id?: number | null;
    timestamp: string;
    additional_data?: Record<string, unknown>;
}

// 错误上报配置
interface ErrorReporterConfig {
    enabled: boolean;
    maxRetries: number;
    retryDelay: number;
    batchSize: number;
    flushInterval: number;
}

// 默认配置
const DEFAULT_CONFIG: ErrorReporterConfig = {
    enabled: true,
    maxRetries: 3,
    retryDelay: 5000,
    batchSize: 10,
    flushInterval: 30000
};

/**
 * 错误上报服务类
 */
class ErrorReporterService {
    private deviceId: string | null = null;
    private config: ErrorReporterConfig;
    private errorQueue: ErrorReport[] = [];
    private flushTimer: ReturnType<typeof setInterval> | null = null;

    constructor(config: Partial<ErrorReporterConfig> = {}) {
        this.config = { ...DEFAULT_CONFIG, ...config };
    }

    /**
     * 初始化错误上报服务
     */
    init(deviceId: string): void {
        this.deviceId = deviceId;
        this.startFlushTimer();

        // 监听页面关闭，发送剩余错误
        window.addEventListener('beforeunload', () => {
            this.flush(true);
        });
    }

    /**
     * 设置设备 ID
     */
    setDeviceId(deviceId: string): void {
        this.deviceId = deviceId;
    }

    /**
     * 上报错误
     */
    report(
        type: ErrorType,
        message: string,
        options: {
            playlistId?: number | null;
            mediaId?: number | null;
            additionalData?: Record<string, unknown>;
        } = {}
    ): void {
        if (!this.config.enabled || !this.deviceId) {
            console.debug('ErrorReporter disabled or no device ID');
            return;
        }

        const errorReport: ErrorReport = {
            device_id: this.deviceId,
            type,
            message,
            playlist_id: options.playlistId ?? null,
            media_id: options.mediaId ?? null,
            timestamp: new Date().toISOString(),
            additional_data: options.additionalData
        };

        console.warn(`[ErrorReporter] ${type}: ${message}`);

        // 添加到队列
        this.errorQueue.push(errorReport);

        // 如果队列达到批量大小，立即发送
        if (this.errorQueue.length >= this.config.batchSize) {
            this.flush();
        }
    }

    /**
     * 上报下载失败
     */
    reportDownloadFailed(
        message: string,
        playlistId?: number,
        mediaId?: number,
        additionalData?: Record<string, unknown>
    ): void {
        this.report('download_failed', message, {
            playlistId,
            mediaId,
            additionalData
        });
    }

    /**
     * 上报播放错误
     */
    reportPlaybackError(
        message: string,
        mediaId?: number,
        additionalData?: Record<string, unknown>
    ): void {
        this.report('playback_error', message, {
            mediaId,
            additionalData
        });
    }

    /**
     * 上报缓存错误
     */
    reportCacheError(
        message: string,
        additionalData?: Record<string, unknown>
    ): void {
        this.report('cache_error', message, { additionalData });
    }

    /**
     * 上报网络错误
     */
    reportNetworkError(
        message: string,
        additionalData?: Record<string, unknown>
    ): void {
        this.report('network_error', message, { additionalData });
    }

    /**
     * 上报播放列表同步失败
     */
    reportPlaylistSyncFailed(
        message: string,
        playlistId?: number,
        additionalData?: Record<string, unknown>
    ): void {
        this.report('playlist_sync_failed', message, {
            playlistId,
            additionalData
        });
    }

    /**
     * 上报存储空间不足
     */
    reportInsufficientStorage(
        requiredBytes: number,
        availableBytes: number
    ): void {
        this.report('insufficient_storage',
            `Storage insufficient: required ${requiredBytes}, available ${availableBytes}`, {
                additionalData: { requiredBytes, availableBytes }
            });
    }

    /**
     * 刷新错误队列到服务器
     */
    async flush(useBeacon: boolean = false): Promise<void> {
        if (this.errorQueue.length === 0 || !this.deviceId) {
            return;
        }

        const errorsToSend = [...this.errorQueue];
        this.errorQueue = [];

        try {
            if (useBeacon && navigator.sendBeacon) {
                // 使用 sendBeacon 发送（页面关闭时）
                const blob = new Blob([JSON.stringify({
                    device_id: this.deviceId,
                    errors: errorsToSend
                })], { type: 'application/json' });
                navigator.sendBeacon('/api/player/devices/notifications', blob);
            } else {
                // 正常发送
                // 批量发送错误
                for (const error of errorsToSend) {
                    await this.sendWithRetry({
                        device_id: error.device_id,
                        type: error.type as string,
                        playlist_id: error.playlist_id,
                        error_message: error.message
                    });
                }
            }
        } catch (error) {
            console.error('[ErrorReporter] Failed to flush errors:', error);
            // 将失败的错误重新加入队列
            this.errorQueue.unshift(...errorsToSend);
        }
    }

    /**
     * 带重试的发送
     */
    private async sendWithRetry(payload: Record<string, unknown>, retryCount: number = 0): Promise<void> {
        try {
            await axios.post('/api/player/devices/notifications', payload, {
                timeout: 5000
            });
        } catch (error) {
            if (retryCount < this.config.maxRetries) {
                await new Promise(resolve => setTimeout(resolve, this.config.retryDelay));
                await this.sendWithRetry(payload, retryCount + 1);
            } else {
                console.error('[ErrorReporter] Max retries exceeded for error report');
            }
        }
    }

    /**
     * 启动定时刷新
     */
    private startFlushTimer(): void {
        if (this.flushTimer) {
            clearInterval(this.flushTimer);
        }
        this.flushTimer = setInterval(() => {
            this.flush();
        }, this.config.flushInterval);
    }

    /**
     * 停止服务
     */
    stop(): void {
        if (this.flushTimer) {
            clearInterval(this.flushTimer);
            this.flushTimer = null;
        }
        this.flush(true);
    }

    /**
     * 获取当前队列长度
     */
    getQueueLength(): number {
        return this.errorQueue.length;
    }
}

// 导出单例
export const ErrorReporter = new ErrorReporterService();
export default ErrorReporter;
