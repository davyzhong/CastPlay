/**
 * 存储空间检查器
 *
 * 功能：
 * - 检查可用存储空间
 * - 估算所需空间
 * - 提供存储警告
 */

// 存储信息
export interface StorageInfo {
    quota: number;         // 总配额（字节）
    usage: number;         // 已使用（字节）
    available: number;     // 可用空间（字节）
    usagePercentage: number; // 使用百分比
}

// 存储检查结果
export interface StorageCheckResult {
    canDownload: boolean;  // 是否可以下载
    requiredSpace: number; // 所需空间（字节）
    availableSpace: number; // 可用空间（字节）
    warning?: string;      // 警告信息
    recommendation?: string; // 建议
}

// 配置
const STORAGE_CONFIG = {
    // 最低保留空间（100MB）
    MIN_FREE_SPACE: 100 * 1024 * 1024,
    // 警告阈值（90%）
    WARNING_THRESHOLD: 0.9,
    // 单个文件预估额外开销（10%）
    FILE_OVERHEAD: 1.1,
};

class StorageChecker {
    private cachedInfo: StorageInfo | null = null;
    private lastCheckTime: number = 0;
    private cacheTTL: number = 60000; // 1分钟缓存

    /**
     * 获取存储信息
     */
    async getStorageInfo(): Promise<StorageInfo> {
        // 检查缓存
        if (this.cachedInfo && Date.now() - this.lastCheckTime < this.cacheTTL) {
            return this.cachedInfo;
        }

        try {
            if (navigator.storage && navigator.storage.estimate) {
                const estimate = await navigator.storage.estimate();

                const quota = estimate.quota || 0;
                const usage = estimate.usage || 0;
                const available = quota - usage;
                const usagePercentage = quota > 0 ? (usage / quota) * 100 : 0;

                this.cachedInfo = {
                    quota,
                    usage,
                    available,
                    usagePercentage,
                };

                this.lastCheckTime = Date.now();
                return this.cachedInfo;
            }
        } catch (error) {
            console.error('[StorageChecker] Failed to get storage info:', error);
        }

        // 返回默认值
        return {
            quota: 0,
            usage: 0,
            available: 0,
            usagePercentage: 0,
        };
    }

    /**
     * 估算所需空间
     */
    estimateRequiredSpace(files: Array<{ file_size?: number }>): number {
        const totalSize = files.reduce((sum, file) => {
            return sum + (file.file_size || 0);
        }, 0);

        // 加上开销
        return Math.ceil(totalSize * STORAGE_CONFIG.FILE_OVERHEAD);
    }

    /**
     * 检查是否有足够空间
     */
    async checkSpace(files: Array<{ file_size?: number }>): Promise<StorageCheckResult> {
        const storageInfo = await this.getStorageInfo();
        const requiredSpace = this.estimateRequiredSpace(files);
        const availableSpace = storageInfo.available;

        // 计算下载后的剩余空间
        const remainingAfterDownload = availableSpace - requiredSpace;

        // 检查是否低于最低保留空间
        const canDownload = remainingAfterDownload >= STORAGE_CONFIG.MIN_FREE_SPACE;

        let warning: string | undefined;
        let recommendation: string | undefined;

        if (!canDownload) {
            warning = `存储空间不足。需要 ${(requiredSpace / 1024 / 1024).toFixed(1)}MB，可用 ${(availableSpace / 1024 / 1024).toFixed(1)}MB`;
            recommendation = '请清理旧缓存或删除不需要的播放列表';
        } else if (storageInfo.usagePercentage >= STORAGE_CONFIG.WARNING_THRESHOLD * 100) {
            warning = `存储空间使用率已达 ${storageInfo.usagePercentage.toFixed(1)}%`;
            recommendation = '建议清理旧缓存以释放空间';
        }

        return {
            canDownload,
            requiredSpace,
            availableSpace,
            warning,
            recommendation,
        };
    }

    /**
     * 格式化存储大小
     */
    formatBytes(bytes: number): string {
        if (bytes === 0) return '0 B';

        const units = ['B', 'KB', 'MB', 'GB', 'TB'];
        const k = 1024;
        const i = Math.floor(Math.log(bytes) / Math.log(k));

        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + units[i];
    }

    /**
     * 清除缓存
     */
    clearCache(): void {
        this.cachedInfo = null;
        this.lastCheckTime = 0;
    }
}

// 单例导出
export const storageChecker = new StorageChecker();
