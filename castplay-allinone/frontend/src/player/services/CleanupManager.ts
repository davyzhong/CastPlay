/**
 * 清理管理器
 * 负责在成功播放 24 小时后清理旧播放列表
 */
import { NotificationType } from '../services/DownloadManager';

export interface CleanupConfig {
    deviceId: string;
    onCleanupStart?: (playlistId: number) => void;
    onCleanupComplete?: (playlistId: number) => void;
    onCleanupFailed?: (playlistId: number, error: Error) => void;
}

export interface CleanupSchedule {
    playlistId: number;
    scheduledTime: number; // 时间戳
    executed: boolean;
    executedAt?: number;
}

export class CleanupManager {
    private config: CleanupConfig;
    private cleanupTimers: Map<number, NodeJS.Timeout> = new Map();
    private readonly CLEANUP_DELAY_MS = 24 * 60 * 60 * 1000; // 24 小时

    constructor(config: CleanupConfig) {
        this.config = config;
        this.loadScheduledCleanups();
    }

    /**
     * 计划清理
     * @param playlistId 播放列表 ID
     * @param delayMs 延迟时间（毫秒），默认 24 小时
     */
    async scheduleCleanup(playlistId: number, delayMs?: number): Promise<void> {
        const executeTime = Date.now() + (delayMs || this.CLEANUP_DELAY_MS);

        console.log(`Schedule cleanup for playlist ${playlistId} at ${new Date(executeTime).toISOString()}`);

        // 保存到 localStorage
        await this.saveScheduledCleanup({
            playlistId,
            scheduledTime: executeTime,
            executed: false
        });

        // 设置定时器
        this.setCleanupTimer(playlistId, executeTime);
    }

    /**
     * 设置清理定时器
     */
    private setCleanupTimer(playlistId: number, executeTime: number): void {
        const delay = executeTime - Date.now();

        if (delay <= 0) {
            // 立即执行
            this.executeCleanup(playlistId);
            return;
        }

        const timer = setTimeout(async () => {
            await this.executeCleanup(playlistId);
        }, delay);

        this.cleanupTimers.set(playlistId, timer);
    }

    /**
     * 执行清理
     */
    private async executeCleanup(playlistId: number): Promise<void> {
        console.log(`Starting cleanup for playlist ${playlistId}`);

        if (this.config.onCleanupStart) {
            this.config.onCleanupStart(playlistId);
        }

        try {
            // 验证清理条件
            const canCleanup = await this.verifyCleanupConditions(playlistId);

            if (!canCleanup) {
                console.warn(`Cannot cleanup playlist ${playlistId}, conditions not met`);
                throw new Error('Cleanup conditions not met');
            }

            // 1. 删除缓存文件
            await this.deleteCachedFiles(playlistId);

            // 2. 清除 IndexedDB 记录
            await this.clearIndexedDBRecords(playlistId);

            // 3. 清除 localStorage 记录
            await this.clearLocalStorageRecords(playlistId);

            // 标记为已执行
            await this.markCleanupExecuted(playlistId);

            // 清理定时器引用
            this.cleanupTimers.delete(playlistId);

            console.log(`Successfully cleaned up playlist ${playlistId}`);

            if (this.config.onCleanupComplete) {
                this.config.onCleanupComplete(playlistId);
            }

            // 通知服务端清理完成
            await this.notifyCleanupComplete(playlistId);

        } catch (error) {
            console.error(`Failed to cleanup playlist ${playlistId}:`, error);

            if (this.config.onCleanupFailed) {
                this.config.onCleanupFailed(playlistId, error as Error);
            }

            // 通知服务端清理失败
            await this.notifyCleanupFailed(playlistId, error as Error);

            throw error;
        }
    }

    /**
     * 验证清理条件（P1-1 修复：明确激活时间缺失的处理逻辑）
     */
    private async verifyCleanupConditions(playlistId: number): Promise<boolean> {
        // 1. 检查是否有新的播放列表已激活
        const activePlaylistId = localStorage.getItem('castplay_current_playlist_id');
        if (!activePlaylistId || parseInt(activePlaylistId) === playlistId) {
            console.warn('No active playlist or same as target, skipping cleanup');
            return false;
        }

        // 2. 检查新播放列表是否已激活超过 24 小时
        const activatedAtStr = localStorage.getItem(`castplay_playlist_activated_${activePlaylistId}`);
        if (!activatedAtStr) {
            // P1-1 修复：保守策略 - 如果有疑问，暂不清理
            console.warn(
                `Activation time not found for playlist ${activePlaylistId}, ` +
                'skipping cleanup to prevent accidental deletion'
            );
            return false;
        }

        const activatedAt = parseInt(activatedAtStr);
        const now = Date.now();

        if (now - activatedAt < this.CLEANUP_DELAY_MS) {
            console.warn('New playlist not active for 24 hours yet');
            return false;
        }

        // 3. 检查是否正在切换
        const isSwitching = localStorage.getItem('castplay_is_switching') === 'true';
        if (isSwitching) {
            console.warn('Switch in progress, cannot cleanup');
            return false;
        }

        // 所有条件满足，可以清理
        return true;
    }

    /**
     * 删除缓存文件
     */
    private async deleteCachedFiles(playlistId: number): Promise<void> {
        // 实际实现需要遍历并删除该播放列表的所有文件
        console.log(`Deleting cached files for playlist ${playlistId}`);

        // TODO: 使用 File System Access API 或 IndexedDB 删除文件
    }

    /**
     * 清除 IndexedDB 记录
     */
    private async clearIndexedDBRecords(playlistId: number): Promise<void> {
        console.log(`Clearing IndexedDB records for playlist ${playlistId}`);

        // TODO: 打开 IndexedDB 并删除相关记录
    }

    /**
     * 清除 localStorage 记录
     */
    private async clearLocalStorageRecords(playlistId: number): Promise<void> {
        // 删除所有与该播放列表相关的 key
        const keysToRemove: string[] = [];

        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && key.includes(`playlist_${playlistId}`)) {
                keysToRemove.push(key);
            }
        }

        keysToRemove.forEach(key => localStorage.removeItem(key));
        console.log(`Cleared ${keysToRemove.length} localStorage keys for playlist ${playlistId}`);
    }

    /**
     * 标记清理已执行
     */
    private async markCleanupExecuted(playlistId: number): Promise<void> {
        const schedules = await this.getScheduledCleanups();
        const schedule = schedules.find(s => s.playlistId === playlistId);

        if (schedule) {
            schedule.executed = true;
            schedule.executedAt = Date.now();
            await this.saveScheduledCleanups(schedules);
        }
    }

    /**
     * 通知服务端清理完成
     */
    private async notifyCleanupComplete(playlistId: number): Promise<void> {
        try {
            await fetch('/api/player/devices/notifications', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    device_id: this.config.deviceId,
                    type: NotificationType.DOWNLOAD_SUCCESS, // 复用成功类型
                    playlist_id: playlistId,
                    error_message: 'Old playlist cleaned up successfully after 24 hours'
                })
            });
        } catch (error) {
            console.error('Failed to notify cleanup completion:', error);
        }
    }

    /**
     * 通知服务端清理失败
     */
    private async notifyCleanupFailed(playlistId: number, error: Error): Promise<void> {
        try {
            await fetch('/api/player/devices/notifications', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    device_id: this.config.deviceId,
                    type: 'cleanup_failed', // 新类型
                    playlist_id: playlistId,
                    error_message: error.message
                })
            });
        } catch (notifyError) {
            console.error('Failed to send cleanup failure notification:', notifyError);
        }
    }

    /**
     * 加载已计划的清理任务
     */
    private async loadScheduledCleanups(): Promise<void> {
        try {
            const schedules = await this.getScheduledCleanups();
            const now = Date.now();

            schedules.forEach(schedule => {
                if (!schedule.executed) {
                    if (schedule.scheduledTime <= now) {
                        // 已到期，立即执行
                        this.executeCleanup(schedule.playlistId);
                    } else {
                        // 未到期，设置定时器
                        this.setCleanupTimer(schedule.playlistId, schedule.scheduledTime);
                    }
                }
            });
        } catch (error) {
            console.error('Failed to load scheduled cleanups:', error);
        }
    }

    /**
     * 获取已计划的清理任务
     */
    private async getScheduledCleanups(): Promise<CleanupSchedule[]> {
        try {
            const data = localStorage.getItem('castplay_cleanup_schedules');
            return data ? JSON.parse(data) : [];
        } catch {
            return [];
        }
    }

    /**
     * 保存已计划的清理任务
     */
    private async saveScheduledCleanups(schedules: CleanupSchedule[]): Promise<void> {
        try {
            localStorage.setItem('castplay_cleanup_schedules', JSON.stringify(schedules));
        } catch (error) {
            console.error('Failed to save scheduled cleanups:', error);
        }
    }

    /**
     * 保存单个清理任务
     */
    private async saveScheduledCleanup(schedule: CleanupSchedule): Promise<void> {
        const schedules = await this.getScheduledCleanups();
        const index = schedules.findIndex(s => s.playlistId === schedule.playlistId);

        if (index >= 0) {
            schedules[index] = schedule;
        } else {
            schedules.push(schedule);
        }

        await this.saveScheduledCleanups(schedules);
    }

    /**
     * 取消清理计划
     */
    async cancelCleanup(playlistId: number): Promise<void> {
        // 清除定时器
        const timer = this.cleanupTimers.get(playlistId);
        if (timer) {
            clearTimeout(timer);
            this.cleanupTimers.delete(playlistId);
        }

        // 从列表中移除
        const schedules = await this.getScheduledCleanups();
        const filtered = schedules.filter(s => s.playlistId !== playlistId);
        await this.saveScheduledCleanups(filtered);

        console.log(`Cancelled cleanup for playlist ${playlistId}`);
    }

    /**
     * 获取所有已计划的清理
     */
    async getScheduledCleanupsList(): Promise<CleanupSchedule[]> {
        return await this.getScheduledCleanups();
    }

    /**
     * 清理所有定时器
     */
    dispose(): void {
        this.cleanupTimers.forEach(timer => clearTimeout(timer));
        this.cleanupTimers.clear();
    }
}

// 导出工厂函数
export function createCleanupManager(config: CleanupConfig): CleanupManager {
    return new CleanupManager(config);
}
