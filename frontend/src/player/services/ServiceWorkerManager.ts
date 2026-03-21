/**
 * Service Worker 管理器
 * 负责注册、更新和管理 Service Worker
 */
import { ErrorReporter } from './ErrorReporter';

interface CacheStatus {
    caches: Record<string, number>;
    totalSize: number;
}

interface ServiceWorkerManagerConfig {
    swPath: string;
    scope: string;
    updateInterval: number;
}

const DEFAULT_CONFIG: ServiceWorkerManagerConfig = {
    swPath: '/sw.js',
    scope: '/',
    updateInterval: 60 * 60 * 1000  // 1 小时检查一次更新
};

class ServiceWorkerManager {
    private registration: ServiceWorkerRegistration | null = null;
    private config: ServiceWorkerManagerConfig;
    private updateCheckTimer: ReturnType<typeof setInterval> | null = null;

    constructor(config: Partial<ServiceWorkerManagerConfig> = {}) {
        this.config = { ...DEFAULT_CONFIG, ...config };
    }

    /**
     * 注册 Service Worker
     */
    async register(): Promise<boolean> {
        if (!('serviceWorker' in navigator)) {
            console.log('[SWManager] Service Worker not supported');
            return false;
        }

        try {
            this.registration = await navigator.serviceWorker.register(
                this.config.swPath,
                { scope: this.config.scope }
            );

            console.log('[SWManager] Service Worker registered:', this.registration.scope);

            // 监听更新
            this.setupUpdateListeners();

            // 启动定期更新检查
            this.startUpdateCheck();

            return true;
        } catch (error) {
            console.error('[SWManager] Registration failed:', error);
            ErrorReporter.report('cache_error', `Service Worker registration failed: ${error}`);
            return false;
        }
    }

    /**
     * 设置更新监听器
     */
    private setupUpdateListeners(): void {
        if (!this.registration) return;

        // 检测新版本安装
        this.registration.addEventListener('updatefound', () => {
            const newWorker = this.registration?.installing;
            if (!newWorker) return;

            newWorker.addEventListener('statechange', () => {
                if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                    console.log('[SWManager] New version available');
                    this.notifyUpdateAvailable();
                }
            });
        });

        // 监听控制器变化
        navigator.serviceWorker.addEventListener('controllerchange', () => {
            console.log('[SWManager] Controller changed, reloading...');
            window.location.reload();
        });
    }

    /**
     * 通知有新版本可用
     */
    private notifyUpdateAvailable(): void {
        // 可以触发自定义事件或显示通知
        window.dispatchEvent(new CustomEvent('sw-update-available'));

        // 提示用户更新
        if (confirm('新版本可用，是否立即更新？')) {
            this.applyUpdate();
        }
    }

    /**
     * 应用更新
     */
    async applyUpdate(): Promise<void> {
        if (!this.registration?.waiting) {
            console.log('[SWManager] No waiting worker to activate');
            return;
        }

        // 通知等待中的 Service Worker 跳过等待
        this.registration.waiting.postMessage({ type: 'SKIP_WAITING' });
    }

    /**
     * 启动定期更新检查
     */
    private startUpdateCheck(): void {
        if (this.updateCheckTimer) {
            clearInterval(this.updateCheckTimer);
        }

        this.updateCheckTimer = setInterval(() => {
            this.checkForUpdate();
        }, this.config.updateInterval);
    }

    /**
     * 检查更新
     */
    async checkForUpdate(): Promise<boolean> {
        if (!this.registration) return false;

        try {
            await this.registration.update();
            console.log('[SWManager] Update check completed');
            return true;
        } catch (error) {
            console.error('[SWManager] Update check failed:', error);
            return false;
        }
    }

    /**
     * 缓存媒体文件
     */
    async cacheMediaFiles(urls: string[]): Promise<void> {
        if (!this.registration?.active) {
            console.warn('[SWManager] Service Worker not active');
            return;
        }

        return new Promise((resolve, reject) => {
            const messageChannel = new MessageChannel();

            messageChannel.port1.onmessage = (event) => {
                if (event.data.success) {
                    resolve();
                } else {
                    reject(new Error(event.data.error));
                }
            };

            this.registration?.active?.postMessage(
                { type: 'CACHE_MEDIA', urls },
                [messageChannel.port2]
            );
        });
    }

    /**
     * 清理媒体缓存
     */
    async clearMediaCache(): Promise<void> {
        if (!this.registration?.active) {
            console.warn('[SWManager] Service Worker not active');
            return;
        }

        return new Promise((resolve, reject) => {
            const messageChannel = new MessageChannel();

            messageChannel.port1.onmessage = (event) => {
                if (event.data.success) {
                    resolve();
                } else {
                    reject(new Error(event.data.error));
                }
            };

            this.registration?.active?.postMessage(
                { type: 'CLEAR_MEDIA_CACHE' },
                [messageChannel.port2]
            );
        });
    }

    /**
     * 获取缓存状态
     */
    async getCacheStatus(): Promise<CacheStatus | null> {
        if (!this.registration?.active) {
            return null;
        }

        return new Promise((resolve) => {
            const messageChannel = new MessageChannel();

            messageChannel.port1.onmessage = (event) => {
                resolve(event.data);
            };

            this.registration?.active?.postMessage(
                { type: 'GET_CACHE_STATUS' },
                [messageChannel.port2]
            );
        });
    }

    /**
     * 注销 Service Worker
     */
    async unregister(): Promise<boolean> {
        if (!this.registration) return false;

        try {
            const result = await this.registration.unregister();
            console.log('[SWManager] Service Worker unregistered');
            this.registration = null;

            if (this.updateCheckTimer) {
                clearInterval(this.updateCheckTimer);
                this.updateCheckTimer = null;
            }

            return result;
        } catch (error) {
            console.error('[SWManager] Unregister failed:', error);
            return false;
        }
    }

    /**
     * 获取当前注册状态
     */
    getRegistration(): ServiceWorkerRegistration | null {
        return this.registration;
    }

    /**
     * 检查是否已注册
     */
    isRegistered(): boolean {
        return this.registration !== null;
    }

    /**
     * 检查是否支持 Service Worker
     */
    static isSupported(): boolean {
        return 'serviceWorker' in navigator;
    }
}

// 导出单例
export const serviceWorkerManager = new ServiceWorkerManager();
export default serviceWorkerManager;
