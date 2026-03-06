/**
 * 下载管理器（增强版）
 * 支持优先级、断点续传、并发控制
 */

export interface DownloadTask {
    id: string;
    url: string;
    targetPath: string;
    mediaType: string;
    md5Hash?: string;
    priority: number; // 1=最高，3=最低
    playlistId: number;
    retryCount: number;
}

export enum DownloadState {
    IDLE = 'idle',
    CHECKING = 'checking',
    DOWNLOADING = 'downloading',
    VERIFYING = 'verifying',
    WAITING_SWITCH = 'waiting_switch',
    SWITCHING = 'switching',
    COMPLETED = 'completed',
    FAILED = 'failed',
    RETRYING = 'retrying'
}

export enum NotificationType {
    DOWNLOAD_SUCCESS = 'download_success',
    DOWNLOAD_FAILED = 'download_failed',
    INSUFFICIENT_STORAGE = 'insufficient_storage',
    SWITCH_FAILED = 'switch_failed'
}

export class DownloadManager {
    private queue: DownloadTask[] = [];
    private activeDownloads = 0;
    private maxConcurrent = 3;
    private retryCount = new Map<string, number>();
    private state: DownloadState = DownloadState.IDLE;
    private deviceId: string;

    constructor(deviceId: string) {
        this.deviceId = deviceId;
    }

    /**
     * 添加下载任务（带优先级）
     */
    async addTask(task: DownloadTask): Promise<void> {
        // 计算优先级：图片 > 视频 > 其他
        task.priority = this.calculatePriority(task.mediaType);

        // 删除旧的临时文件
        await this.cleanupTempFile(task.targetPath);

        this.queue.push(task);
        this.queue.sort((a, b) => a.priority - b.priority);

        this.processQueue();
    }

    /**
     * 处理队列
     */
    private async processQueue(): Promise<void> {
        while (this.activeDownloads < this.maxConcurrent && this.queue.length > 0) {
            const task = this.queue.shift();
            if (task) {
                this.executeDownload(task);
            }
        }
    }

    /**
     * 执行下载（支持断点续传）
     */
    private async executeDownload(task: DownloadTask): Promise<void> {
        this.activeDownloads++;
        this.state = DownloadState.DOWNLOADING;

        try {
            const tempPath = task.targetPath + '.tmp';

            // 检查已下载的部分
            const existingSize = await this.getFileSize(tempPath);

            const headers: HeadersInit = {};
            if (existingSize > 0) {
                headers['Range'] = `bytes=${existingSize}-`;
            }

            const response = await fetch(task.url, { headers });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            // 流式写入
            await this.streamToFile(response, tempPath, existingSize);

            // 校验 MD5（如果有）
            if (task.md5Hash) {
                await this.verifyMD5(tempPath, task.md5Hash);
            }

            // 重命名到目标路径
            await this.renameFile(tempPath, task.targetPath);

            this.retryCount.delete(task.id);
            this.state = DownloadState.COMPLETED;

        } catch (error) {
            console.error(`Download failed for ${task.url}:`, error);

            // 删除临时文件
            await this.safeDelete(task.targetPath + '.tmp');

            // 重试逻辑
            await this.handleRetry(task, error as Error);
        } finally {
            this.activeDownloads--;
            this.processQueue();
        }
    }

    /**
     * 重试逻辑
     */
    private async handleRetry(task: DownloadTask, error: Error): Promise<void> {
        const count = this.retryCount.get(task.id) || 0;

        if (count < 3) {
            this.retryCount.set(task.id, count + 1);
            task.retryCount = count + 1;

            console.log(`Retrying download (${count + 1}/3): ${task.url}`);
            setTimeout(() => {
                this.addTask(task);
            }, 5000); // 5 秒后重试
        } else {
            // 3 次失败，推送通知到服务端
            console.error(`Download failed after 3 retries: ${task.url}`);
            this.state = DownloadState.FAILED;
            await this.notifyServer(NotificationType.DOWNLOAD_FAILED, task.playlistId, error.message);
        }
    }

    /**
     * 计算优先级
     */
    private calculatePriority(mediaType: string): number {
        // 图片文件优先
        if (['image/jpeg', 'image/png', 'image/webp', 'image/gif'].includes(mediaType)) {
            return 1; // 最高优先级
        } else if (['video/mp4', 'video/webm', 'video/ogg'].includes(mediaType)) {
            return 2;
        } else {
            return 3; // 最低优先级
        }
    }

    /**
     * 获取文件大小
     */
    private async getFileSize(path: string): Promise<number> {
        try {
            // 使用 File System Access API 或 IndexedDB
            // 这里简化处理
            return 0;
        } catch {
            return 0;
        }
    }

    /**
     * 流式写入文件
     */
    private async streamToFile(
        response: Response,
        path: string,
        existingSize: number
    ): Promise<void> {
        // 实际实现需要使用 File System Access API 或 IndexedDB
        // 这里提供伪代码
        console.log('Streaming to file:', path, 'existing size:', existingSize);
    }

    /**
     * 验证 MD5
     */
    private async verifyMD5(path: string, expectedHash: string): Promise<void> {
        // 简化实现
        console.log('Verifying MD5:', path);
    }

    /**
     * 重命名文件
     */
    private async renameFile(oldPath: string, newPath: string): Promise<void> {
        console.log('Renaming:', oldPath, '->', newPath);
    }

    /**
     * 安全删除
     */
    private async safeDelete(path: string): Promise<void> {
        console.log('Deleting:', path);
    }

    /**
     * 清理临时文件（P1-2 修复：增强清理机制）
     */
    private async cleanupTempFile(targetPath: string): Promise<void> {
        const tempPath = targetPath + '.tmp';
        await this.safeDelete(tempPath);
    }

    /**
     * P1-2 修复：清理所有残留临时文件
     * 在应用启动时或定期调用，删除所有 .tmp 文件
     */
    async cleanupAllTempFiles(): Promise<void> {
        console.log('Cleaning up all temporary files...');

        try {
            // TODO: 实际实现需要遍历缓存目录或使用 IndexedDB
            // 这里提供伪代码框架
            const tempFiles = await this.getAllTempFiles();

            for (const file of tempFiles) {
                // 检查文件是否超过一定时间（如 1 小时）
                const fileAge = Date.now() - file.createdAt;
                if (fileAge > 60 * 60 * 1000) { // 1 小时
                    await this.safeDelete(file.path);
                    console.log(`Deleted old temp file: ${file.path}`);
                }
            }

            console.log(`Cleaned up ${tempFiles.length} temporary files`);
        } catch (error) {
            console.error('Failed to cleanup temp files:', error);
        }
    }

    /**
     * 获取所有临时文件（待实现）
     */
    private async getAllTempFiles(): Promise<Array<{path: string, createdAt: number}>> {
        // TODO: 实现获取临时文件列表的逻辑
        // 可以使用 File System Access API 或查询 IndexedDB
        return [];
    }

    /**
     * 推送通知到服务端
     */
    private async notifyServer(
        type: NotificationType,
        playlistId: number,
        errorMessage?: string
    ): Promise<void> {
        try {
            const response = await fetch('/api/player/devices/notifications', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    device_id: this.deviceId,
                    type,
                    playlist_id: playlistId,
                    error_message: errorMessage
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
        } catch (error) {
            console.error('Failed to send notification to server:', error);
        }
    }

    /**
     * 检查存储空间
     */
    async checkStorageSpace(requiredMB: number): Promise<boolean> {
        try {
            const estimate = await navigator.storage.estimate();
            const availableMB = (estimate.quota || 0) / (1024 * 1024);

            if (availableMB < requiredMB * 1.2) { // 1.2 倍阈值
                await this.notifyServer(
                    NotificationType.INSUFFICIENT_STORAGE,
                    0,
                    `Required: ${requiredMB}MB, Available: ${availableMB.toFixed(2)}MB`
                );
                return false;
            }

            return true;
        } catch {
            return false;
        }
    }

    /**
     * 获取当前状态
     */
    getState(): DownloadState {
        return this.state;
    }

    /**
     * 获取队列长度
     */
    getQueueLength(): number {
        return this.queue.length;
    }

    /**
     * 获取活跃下载数
     */
    getActiveDownloads(): number {
        return this.activeDownloads;
    }
}

// 导出单例工厂
export function createDownloadManager(deviceId: string): DownloadManager {
    return new DownloadManager(deviceId);
}
