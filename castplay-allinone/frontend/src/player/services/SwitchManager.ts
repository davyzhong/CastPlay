/**
 * 播放列表切换管理器
 * 负责在适当时机自动切换到新播放列表
 */
import { DownloadState, NotificationType } from '../services/DownloadManager';

export interface SwitchConfig {
    deviceId: string;
    onSwitchStart?: () => void;
    onSwitchComplete?: () => void;
    onSwitchFailed?: (error: Error) => void;
}

export enum SwitchStatus {
    IDLE = 'idle',
    WAITING_PLAYLIST_END = 'waiting_playlist_end',
    SWITCHING = 'switching',
    COMPLETED = 'completed',
    FAILED = 'failed'
}

export class SwitchManager {
    private config: SwitchConfig;
    private status: SwitchStatus = SwitchStatus.IDLE;
    private targetPlaylistId: number | null = null;
    private currentPlaylistId: number | null = null;
    private isPlaying: boolean = false;
    private switchTimer: NodeJS.Timeout | null = null;

    constructor(config: SwitchConfig) {
        this.config = config;
    }

    /**
     * 计划切换
     * @param newPlaylistId 新播放列表 ID
     * @param currentPlaylistId 当前播放列表 ID
     */
    async scheduleSwitch(newPlaylistId: number, currentPlaylistId: number): Promise<void> {
        if (this.status === SwitchStatus.SWITCHING) {
            console.warn('Already switching, ignoring new request');
            return;
        }

        this.targetPlaylistId = newPlaylistId;
        this.currentPlaylistId = currentPlaylistId;
        this.status = SwitchStatus.WAITING_PLAYLIST_END;

        console.log(`Schedule switch from playlist ${currentPlaylistId} to ${newPlaylistId}`);

        // 等待当前播放列表结束
        this.waitForPlaylistEnd();
    }

    /**
     * 等待播放列表结束
     */
    private waitForPlaylistEnd(): void {
        const checkInterval = setInterval(() => {
            if (!this.isPlaying) {
                // 播放已结束，可以切换
                clearInterval(checkInterval);
                this.executeSwitch();
            }
        }, 5000); // 每 5 秒检查一次

        // 保存定时器引用以便清理
        this.switchTimer = checkInterval as unknown as NodeJS.Timeout;
    }

    /**
     * 执行切换
     */
    private async executeSwitch(): Promise<void> {
        this.status = SwitchStatus.SWITCHING;

        if (this.config.onSwitchStart) {
            this.config.onSwitchStart();
        }

        try {
            // 更新当前播放列表 ID
            await this.updateCurrentPlaylist(this.targetPlaylistId!);

            // 淡入淡出动画（可选）
            await this.playTransitionAnimation();

            // 标记为已完成
            this.status = SwitchStatus.COMPLETED;

            console.log(`Successfully switched to playlist ${this.targetPlaylistId}`);

            if (this.config.onSwitchComplete) {
                this.config.onSwitchComplete();
            }

            // 启动清理定时器（24 小时后清理旧列表）
            this.scheduleCleanup(this.currentPlaylistId!);

        } catch (error) {
            console.error('Failed to switch playlist:', error);
            this.status = SwitchStatus.FAILED;

            if (this.config.onSwitchFailed) {
                this.config.onSwitchFailed(error as Error);
            }

            // 推送通知到服务端
            await this.notifySwitchFailed(error as Error);
        } finally {
            // 清理定时器
            if (this.switchTimer) {
                clearInterval(this.switchTimer);
                this.switchTimer = null;
            }
        }
    }

    /**
     * 更新当前播放列表（P0-2 修复：添加事务一致性）
     */
    private async updateCurrentPlaylist(playlistId: number): Promise<void> {
        const oldPlaylistId = localStorage.getItem('castplay_current_playlist_id');

        try {
            // 先通知服务端，成功后再更新本地
            await fetch('/api/player/heartbeat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    device_id: this.config.deviceId,
                    current_playlist_id: playlistId,
                    status: 'idle'
                })
            });

            // 服务端成功后再更新本地
            localStorage.setItem('castplay_current_playlist_id', playlistId.toString());
            localStorage.setItem(
                `castplay_playlist_activated_${playlistId}`,
                Date.now().toString()
            );

        } catch (error) {
            console.error('Failed to notify server about playlist switch:', error);

            // 回滚：恢复旧的播放列表 ID
            if (oldPlaylistId) {
                localStorage.setItem('castplay_current_playlist_id', oldPlaylistId);
            }

            throw error; // 重新抛出错误，让上层处理
        }
    }

    /**
     * 播放过渡动画
     */
    private async playTransitionAnimation(): Promise<void> {
        // 实际实现可以使用 CSS 动画或淡入淡出
        return new Promise(resolve => {
            // 模拟 500ms 动画
            setTimeout(resolve, 500);
        });
    }

    /**
     * 计划清理旧播放列表
     */
    private scheduleCleanup(oldPlaylistId: number): void {
        const cleanupDelay = 24 * 60 * 60 * 1000; // 24 小时

        setTimeout(async () => {
            await this.executeCleanup(oldPlaylistId);
        }, cleanupDelay);
    }

    /**
     * 执行清理
     */
    private async executeCleanup(oldPlaylistId: number): Promise<void> {
        console.log(`Cleaning up old playlist: ${oldPlaylistId}`);

        // TODO: 实际清理逻辑
        // 1. 删除文件
        // 2. 清除缓存
        // 3. 更新数据库

        // 通知服务端清理完成
        try {
            await fetch('/api/player/devices/notifications', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    device_id: this.config.deviceId,
                    type: NotificationType.DOWNLOAD_SUCCESS, // 复用成功类型
                    playlist_id: oldPlaylistId,
                    error_message: 'Old playlist cleaned up successfully'
                })
            });
        } catch (error) {
            console.error('Failed to notify cleanup completion:', error);
        }
    }

    /**
     * 通知切换失败
     */
    private async notifySwitchFailed(error: Error): Promise<void> {
        try {
            await fetch('/api/player/devices/notifications', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    device_id: this.config.deviceId,
                    type: NotificationType.SWITCH_FAILED,
                    playlist_id: this.targetPlaylistId || 0,
                    error_message: error.message
                })
            });
        } catch (notifyError) {
            console.error('Failed to send switch failure notification:', notifyError);
        }
    }

    /**
     * 设置播放状态
     */
    setPlayingStatus(isPlaying: boolean): void {
        this.isPlaying = isPlaying;

        // 如果正在等待切换且播放结束
        if (this.status === SwitchStatus.WAITING_PLAYLIST_END && !isPlaying) {
            this.waitForPlaylistEnd();
        }
    }

    /**
     * 获取当前状态
     */
    getStatus(): SwitchStatus {
        return this.status;
    }

    /**
     * 是否正在切换
     */
    isSwitching(): boolean {
        return this.status === SwitchStatus.SWITCHING;
    }

    /**
     * 取消切换
     */
    cancel(): void {
        if (this.switchTimer) {
            clearInterval(this.switchTimer);
            this.switchTimer = null;
        }

        this.status = SwitchStatus.IDLE;
        this.targetPlaylistId = null;

        console.log('Switch cancelled');
    }

    /**
     * 获取目标播放列表 ID
     */
    getTargetPlaylistId(): number | null {
        return this.targetPlaylistId;
    }
}

// 导出工厂函数
export function createSwitchManager(config: SwitchConfig): SwitchManager {
    return new SwitchManager(config);
}
