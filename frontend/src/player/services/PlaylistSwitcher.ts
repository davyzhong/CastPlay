/**
 * 播放列表切换器（简化版）
 * 合并了原有的 SwitchManager 和 CleanupManager 功能
 */
import { ErrorReporter } from './ErrorReporter';

export interface SwitcherConfig {
    deviceId: string;
    onSwitchStart?: () => void;
    onSwitchComplete?: () => void;
    onSwitchFailed?: (error: Error) => void;
}

export enum SwitcherStatus {
    IDLE = 'idle',
    SWITCHING = 'switching',
    COMPLETED = 'completed',
    FAILED = 'failed'
}

// 清理延迟（毫秒）- 24 小时
const CLEANUP_DELAY_MS = 24 * 60 * 60 * 1000;

/**
 * 播放列表切换器
 * 负责播放列表切换和旧列表清理
 */
export class PlaylistSwitcher {
    private config: SwitcherConfig;
    private status: SwitcherStatus = SwitcherStatus.IDLE;

    constructor(config: SwitcherConfig) {
        this.config = config;
    }

    /**
     * 切换到新播放列表
     */
    async switchTo(newPlaylistId: number): Promise<void> {
        if (this.status === SwitcherStatus.SWITCHING) {
            console.warn('Already switching, ignoring request');
            return;
        }

        const oldPlaylistId = this.getCurrentPlaylistId();

        if (oldPlaylistId === newPlaylistId) {
            console.log('Same playlist, no switch needed');
            return;
        }

        this.status = SwitcherStatus.SWITCHING;
        // Track the new playlist being switched to
        console.log(`Setting target playlist to: ${newPlaylistId}`);

        console.log(`Switching playlist: ${oldPlaylistId} -> ${newPlaylistId}`);

        this.config.onSwitchStart?.();

        try {
            // 1. 通知服务端
            await this.notifyServer(newPlaylistId);

            // 2. 更新本地状态
            this.updateLocalState(newPlaylistId);

            // 3. 计划清理旧播放列表
            if (oldPlaylistId) {
                this.scheduleCleanup(oldPlaylistId);
            }

            this.status = SwitcherStatus.COMPLETED;
            console.log(`Switch completed: playlist ${newPlaylistId}`);

            this.config.onSwitchComplete?.();

        } catch (error) {
            console.error('Switch failed:', error);
            this.status = SwitcherStatus.FAILED;

            this.config.onSwitchFailed?.(error as Error);

            ErrorReporter.report('switch_failed', `Failed to switch to playlist ${newPlaylistId}: ${(error as Error).message}`, {
                playlistId: newPlaylistId
            });
        }
    }

    /**
     * 通知服务端
     */
    private async notifyServer(playlistId: number): Promise<void> {
        const response = await fetch('/api/player/heartbeat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                device_id: this.config.deviceId,
                current_playlist_id: playlistId,
                status: 'idle'
            })
        });

        if (!response.ok) {
            throw new Error(`Server returned ${response.status}`);
        }
    }

    /**
     * 更新本地状态
     */
    private updateLocalState(playlistId: number): void {
        localStorage.setItem('castplay_current_playlist_id', playlistId.toString());
        localStorage.setItem(`castplay_playlist_activated_${playlistId}`, Date.now().toString());
    }

    /**
     * 获取当前播放列表 ID
     */
    private getCurrentPlaylistId(): number | null {
        const id = localStorage.getItem('castplay_current_playlist_id');
        return id ? parseInt(id) : null;
    }

    /**
     * 计划清理旧播放列表
     */
    private scheduleCleanup(playlistId: number): void {
        const scheduledTime = Date.now() + CLEANUP_DELAY_MS;

        // 保存计划
        const schedules = this.getScheduledCleanups();
        schedules.push({
            playlistId,
            scheduledTime,
            executed: false
        });
        localStorage.setItem('castplay_cleanup_schedules', JSON.stringify(schedules));

        console.log(`Scheduled cleanup for playlist ${playlistId} at ${new Date(scheduledTime).toISOString()}`);

        // 设置定时器
        setTimeout(() => {
            this.executeCleanup(playlistId);
        }, CLEANUP_DELAY_MS);
    }

    /**
     * 执行清理
     */
    private async executeCleanup(playlistId: number): Promise<void> {
        console.log(`Cleaning up playlist ${playlistId}`);

        // 验证条件
        if (!this.canCleanup(playlistId)) {
            console.log(`Cannot cleanup playlist ${playlistId}, conditions not met`);
            return;
        }

        try {
            // 清理 localStorage
            this.clearPlaylistStorage(playlistId);

            // 标记已执行
            this.markCleanupExecuted(playlistId);

            console.log(`Cleanup completed for playlist ${playlistId}`);

        } catch (error) {
            console.error(`Cleanup failed for playlist ${playlistId}:`, error);
        }
    }

    /**
     * 验证是否可以清理
     */
    private canCleanup(playlistId: number): boolean {
        // 检查当前播放列表是否是另一个
        const currentId = this.getCurrentPlaylistId();
        if (!currentId || currentId === playlistId) {
            return false;
        }

        // 检查新播放列表是否已激活超过 24 小时
        const activatedAtStr = localStorage.getItem(`castplay_playlist_activated_${currentId}`);
        if (!activatedAtStr) {
            return false;
        }

        const activatedAt = parseInt(activatedAtStr);
        return (Date.now() - activatedAt) >= CLEANUP_DELAY_MS;
    }

    /**
     * 清理播放列表相关的 localStorage
     */
    private clearPlaylistStorage(playlistId: number): void {
        const keysToRemove: string[] = [];

        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && key.includes(`playlist_${playlistId}`)) {
                keysToRemove.push(key);
            }
        }

        keysToRemove.forEach(key => localStorage.removeItem(key));
        console.log(`Cleared ${keysToRemove.length} localStorage keys`);
    }

    /**
     * 获取已计划的清理
     */
    private getScheduledCleanups(): Array<{
        playlistId: number;
        scheduledTime: number;
        executed: boolean;
    }> {
        try {
            const data = localStorage.getItem('castplay_cleanup_schedules');
            return data ? JSON.parse(data) : [];
        } catch {
            return [];
        }
    }

    /**
     * 标记清理已执行
     */
    private markCleanupExecuted(playlistId: number): void {
        const schedules = this.getScheduledCleanups();
        const schedule = schedules.find(s => s.playlistId === playlistId);

        if (schedule) {
            schedule.executed = true;
            localStorage.setItem('castplay_cleanup_schedules', JSON.stringify(schedules));
        }
    }

    /**
     * 获取当前状态
     */
    getStatus(): SwitcherStatus {
        return this.status;
    }

    /**
     * 是否正在切换
     */
    isSwitching(): boolean {
        return this.status === SwitcherStatus.SWITCHING;
    }

    /**
     * 取消切换
     */
    cancel(): void {
        this.status = SwitcherStatus.IDLE;
    }
}

// 导出工厂函数
export function createPlaylistSwitcher(config: SwitcherConfig): PlaylistSwitcher {
    return new PlaylistSwitcher(config);
}

// 导出单例
let instance: PlaylistSwitcher | null = null;

export function getPlaylistSwitcher(config?: SwitcherConfig): PlaylistSwitcher {
    if (!instance && config) {
        instance = new PlaylistSwitcher(config);
    }
    return instance!;
}
