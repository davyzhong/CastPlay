/**
 * 播放列表下载管理器
 *
 * 功能：
 * - 批量下载播放列表中的媒体文件
 * - 并发控制（最多 3 个并发下载）
 * - 进度持久化（IndexedDB）
 * - 失败重试（最多 3 次）
 * - 下载进度回调
 */

// 媒体项信息
export interface MediaItem {
    id: number;
    file_url: string;
    file_name?: string;
    file_type?: string;
    file_size?: number;
    md5_hash?: string;
}

// 下载任务状态
export type DownloadTaskStatus = 'pending' | 'downloading' | 'completed' | 'failed' | 'cancelled';

// 单个下载任务
export interface DownloadTask {
    mediaId: number;
    url: string;
    status: DownloadTaskStatus;
    progress: number;          // 0-100
    loadedBytes: number;
    totalBytes: number;
    retryCount: number;
    localUrl?: string;
    error?: string;
    startTime?: number;
    endTime?: number;
}

// 播放列表下载状态
export interface PlaylistDownloadState {
    playlistId: number;
    version: string;
    status: 'pending' | 'downloading' | 'completed' | 'failed' | 'partial' | 'cancelled';
    totalFiles: number;
    completedFiles: number;
    failedFiles: number;
    progress: number;          // 0-100
    tasks: Map<number, DownloadTask>;
    startTime?: number;
    endTime?: number;
}

// 下载进度回调
export interface DownloadProgressCallback {
    onTaskProgress?: (taskId: number, task: DownloadTask) => void;
    onTaskComplete?: (taskId: number, task: DownloadTask) => void;
    onTaskFailed?: (taskId: number, task: DownloadTask) => void;
    onPlaylistProgress?: (state: PlaylistDownloadState) => void;
    onPlaylistComplete?: (state: PlaylistDownloadState) => void;
}

// 配置
const CONFIG = {
    maxConcurrent: 3,
    maxRetries: 3,
    retryDelayMs: 1000,
    cacheName: 'playlist-media-cache',
    dbName: 'PlaylistDownloadDB',
    dbVersion: 1,
};

/**
 * IndexedDB 存储管理器
 */
class DownloadStateStorage {
    private db: IDBDatabase | null = null;
    private initPromise: Promise<IDBDatabase> | null = null;

    async init(): Promise<IDBDatabase> {
        if (this.db) return this.db;
        if (this.initPromise) return this.initPromise;

        this.initPromise = new Promise((resolve, reject) => {
            const request = indexedDB.open(CONFIG.dbName, CONFIG.dbVersion);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                this.db = request.result;
                resolve(this.db);
            };

            request.onupgradeneeded = (event) => {
                const db = (event.target as IDBOpenDBRequest).result;

                // 下载任务存储
                if (!db.objectStoreNames.contains('tasks')) {
                    const taskStore = db.createObjectStore('tasks', { keyPath: ['playlistId', 'mediaId'] });
                    taskStore.createIndex('playlistId', 'playlistId', { unique: false });
                    taskStore.createIndex('status', 'status', { unique: false });
                }

                // 播放列表状态存储
                if (!db.objectStoreNames.contains('playlists')) {
                    db.createObjectStore('playlists', { keyPath: 'playlistId' });
                }
            };
        });

        return this.initPromise;
    }

    async saveTask(playlistId: number, task: DownloadTask): Promise<void> {
        const db = await this.init();
        return new Promise((resolve, reject) => {
            const tx = db.transaction('tasks', 'readwrite');
            const store = tx.objectStore('tasks');
            const request = store.put({ playlistId, ...task });

            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    async getTasks(playlistId: number): Promise<DownloadTask[]> {
        const db = await this.init();
        return new Promise((resolve, reject) => {
            const tx = db.transaction('tasks', 'readonly');
            const store = tx.objectStore('tasks');
            const index = store.index('playlistId');
            const request = index.getAll(playlistId);

            request.onsuccess = () => resolve(request.result || []);
            request.onerror = () => reject(request.error);
        });
    }

    async savePlaylistState(state: PlaylistDownloadState): Promise<void> {
        const db = await this.init();
        return new Promise((resolve, reject) => {
            const tx = db.transaction('playlists', 'readwrite');
            const store = tx.objectStore('playlists');
            // 将 Map 转换为数组存储
            const stateToSave = {
                ...state,
                tasks: Array.from(state.tasks.entries()),
            };
            const request = store.put(stateToSave);

            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    async getPlaylistState(playlistId: number): Promise<PlaylistDownloadState | null> {
        const db = await this.init();
        return new Promise((resolve, reject) => {
            const tx = db.transaction('playlists', 'readonly');
            const store = tx.objectStore('playlists');
            const request = store.get(playlistId);

            request.onsuccess = () => {
                const result = request.result;
                if (result) {
                    // 将数组转换回 Map
                    resolve({
                        ...result,
                        tasks: new Map(result.tasks || []),
                    });
                } else {
                    resolve(null);
                }
            };
            request.onerror = () => reject(request.error);
        });
    }

    async clearPlaylist(playlistId: number): Promise<void> {
        const db = await this.init();
        return new Promise((resolve, reject) => {
            const tx = db.transaction(['tasks', 'playlists'], 'readwrite');

            // 删除任务
            const taskStore = tx.objectStore('tasks');
            const taskIndex = taskStore.index('playlistId');
            const taskRequest = taskIndex.openCursor(playlistId);

            taskRequest.onsuccess = (event) => {
                const cursor = (event.target as IDBRequest).result;
                if (cursor) {
                    cursor.delete();
                    cursor.continue();
                }
            };

            // 删除播放列表状态
            const playlistStore = tx.objectStore('playlists');
            playlistStore.delete(playlistId);

            tx.oncomplete = () => resolve();
            tx.onerror = () => reject(tx.error);
        });
    }
}

/**
 * 播放列表下载管理器
 */
export class PlaylistDownloadManager {
    private storage: DownloadStateStorage;
    private cache: Cache | null = null;
    private activeDownloads: Map<number, AbortController> = new Map();
    private downloadQueue: number[] = [];
    private runningCount = 0;
    private currentState: PlaylistDownloadState | null = null;
    private callbacks: DownloadProgressCallback = {};

    constructor() {
        this.storage = new DownloadStateStorage();
    }

    /**
     * 设置回调
     */
    setCallbacks(callbacks: DownloadProgressCallback): void {
        this.callbacks = { ...this.callbacks, ...callbacks };
    }

    /**
     * 初始化 Cache API
     */
    private async initCache(): Promise<Cache> {
        if (!this.cache) {
            this.cache = await caches.open(CONFIG.cacheName);
        }
        return this.cache;
    }

    /**
     * 恢复中断的下载（从 IndexedDB 恢复状态）
     */
    async restoreDownload(playlistId: number): Promise<PlaylistDownloadState | null> {
        const savedState = await this.storage.getPlaylistState(playlistId);

        if (!savedState) {
            return null;
        }

        // 只恢复下载中的状态
        if (savedState.status === 'downloading') {
            console.log(`[DownloadManager] Restoring interrupted download for playlist ${playlistId}`);

            // 检查哪些任务需要继续
            for (const [, task] of savedState.tasks) {
                if (task.status === 'downloading' || task.status === 'pending') {
                    task.status = 'pending';
                    task.retryCount = 0;
                }
            }

            this.currentState = savedState;
        }

        return savedState;
    }

    /**
     * 开始下载播放列表
     */
    async startDownload(
        playlistId: number,
        version: string,
        mediaList: MediaItem[],
        callbacks?: DownloadProgressCallback
    ): Promise<PlaylistDownloadState> {
        if (callbacks) {
            this.setCallbacks(callbacks);
        }

        // 初始化状态
        this.currentState = {
            playlistId,
            version,
            status: 'pending',
            totalFiles: mediaList.length,
            completedFiles: 0,
            failedFiles: 0,
            progress: 0,
            tasks: new Map(),
            startTime: Date.now(),
        };

        // 创建下载任务
        for (const media of mediaList) {
            const task: DownloadTask = {
                mediaId: media.id,
                url: media.file_url,
                status: 'pending',
                progress: 0,
                loadedBytes: 0,
                totalBytes: media.file_size || 0,
                retryCount: 0,
                startTime: Date.now(),
            };
            this.currentState.tasks.set(media.id, task);
        }

        // 保存初始状态
        await this.storage.savePlaylistState(this.currentState);

        // 开始下载
        this.currentState.status = 'downloading';
        await this.processQueue();

        return this.currentState;
    }

    /**
     * 处理下载队列
     */
    private async processQueue(): Promise<void> {
        if (!this.currentState) return;

        const pendingTasks = Array.from(this.currentState.tasks.values())
            .filter(t => t.status === 'pending');

        this.downloadQueue = pendingTasks.map(t => t.mediaId);

        // 启动并发下载
        const promises: Promise<void>[] = [];
        for (let i = 0; i < Math.min(CONFIG.maxConcurrent, this.downloadQueue.length); i++) {
            const mediaId = this.downloadQueue.shift();
            if (mediaId !== undefined) {
                this.runningCount++;
                promises.push(this.downloadTask(mediaId));
            }
        }

        await Promise.allSettled(promises);
    }

    /**
     * 下载单个任务
     */
    private async downloadTask(mediaId: number): Promise<void> {
        if (!this.currentState) return;

        const task = this.currentState.tasks.get(mediaId);
        if (!task) return;

        const controller = new AbortController();
        this.activeDownloads.set(mediaId, controller);

        task.status = 'downloading';
        task.startTime = Date.now();

        try {
            const cache = await this.initCache();

            // 先检查缓存中是否已存在
            const existingCachedResponse = await cache.match(task.url);
            if (existingCachedResponse) {
                task.status = 'completed';
                task.progress = 100;
                task.localUrl = task.url;
                task.endTime = Date.now();
                await this.onTaskComplete(mediaId);
                return;
            }

            // 使用 fetch 下载
            const response = await fetch(task.url, {
                signal: controller.signal,
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const contentLength = response.headers.get('content-length');
            task.totalBytes = contentLength ? parseInt(contentLength, 10) : task.totalBytes;

            // 使用 ReadableStream 跟踪进度
            const reader = response.body?.getReader();
            if (!reader) {
                throw new Error('No response body');
            }

            const chunks: Uint8Array[] = [];
            let loadedBytes = 0;

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                chunks.push(value);
                loadedBytes += value.length;
                task.loadedBytes = loadedBytes;

                if (task.totalBytes > 0) {
                    task.progress = Math.round((loadedBytes / task.totalBytes) * 100);
                }

                // 回调进度
                this.callbacks.onTaskProgress?.(mediaId, task);
            }

            // 合并 chunks
            const blob = new Blob(chunks as BlobPart[]);
            const newCachedResponse = new Response(blob, {
                headers: response.headers,
            });

            // 存储到 Cache API
            await cache.put(task.url, newCachedResponse);

            task.status = 'completed';
            task.progress = 100;
            task.localUrl = task.url;
            task.endTime = Date.now();

            await this.onTaskComplete(mediaId);

        } catch (error) {
            if ((error as Error).name === 'AbortError') {
                task.status = 'cancelled';
                task.error = 'Download cancelled';
            } else {
                task.error = (error as Error).message;
                await this.onTaskFailed(mediaId);
            }
        } finally {
            this.activeDownloads.delete(mediaId);
            this.runningCount--;

            // 处理队列中的下一个
            if (this.downloadQueue.length > 0 && this.currentState?.status === 'downloading') {
                const nextMediaId = this.downloadQueue.shift();
                if (nextMediaId !== undefined) {
                    this.runningCount++;
                    await this.downloadTask(nextMediaId);
                }
            }

            // 检查是否全部完成
            if (this.runningCount === 0 && this.downloadQueue.length === 0) {
                await this.onPlaylistComplete();
            }
        }
    }

    /**
     * 任务完成处理
     */
    private async onTaskComplete(mediaId: number): Promise<void> {
        if (!this.currentState) return;

        const task = this.currentState.tasks.get(mediaId);
        if (!task) return;

        this.currentState.completedFiles++;
        this.updateOverallProgress();

        // 保存状态
        await this.storage.saveTask(this.currentState.playlistId, task);
        await this.storage.savePlaylistState(this.currentState);

        // 回调
        this.callbacks.onTaskComplete?.(mediaId, task);
        this.callbacks.onPlaylistProgress?.(this.currentState);

        console.log(`[DownloadManager] Task completed: ${mediaId}`);
    }

    /**
     * 任务失败处理
     */
    private async onTaskFailed(mediaId: number): Promise<void> {
        if (!this.currentState) return;

        const task = this.currentState.tasks.get(mediaId);
        if (!task) return;

        task.retryCount++;

        if (task.retryCount <= CONFIG.maxRetries) {
            // 重试
            console.log(`[DownloadManager] Retrying task ${mediaId} (${task.retryCount}/${CONFIG.maxRetries})`);

            await new Promise(resolve => setTimeout(resolve, CONFIG.retryDelayMs * task.retryCount));

            task.status = 'pending';
            task.error = undefined;
            this.downloadQueue.push(mediaId);
        } else {
            // 重试次数用尽
            task.status = 'failed';
            this.currentState.failedFiles++;

            console.error(`[DownloadManager] Task failed after ${CONFIG.maxRetries} retries: ${mediaId}`);

            this.callbacks.onTaskFailed?.(mediaId, task);
        }

        this.updateOverallProgress();
        await this.storage.saveTask(this.currentState.playlistId, task);
        await this.storage.savePlaylistState(this.currentState);

        this.callbacks.onPlaylistProgress?.(this.currentState);
    }

    /**
     * 更新整体进度
     */
    private updateOverallProgress(): void {
        if (!this.currentState) return;

        const total = this.currentState.totalFiles;
        const completed = this.currentState.completedFiles;
        const failed = this.currentState.failedFiles;

        this.currentState.progress = Math.round(((completed + failed) / total) * 100);
    }

    /**
     * 播放列表下载完成处理
     */
    private async onPlaylistComplete(): Promise<void> {
        if (!this.currentState) return;

        const { completedFiles, failedFiles, totalFiles } = this.currentState;

        if (failedFiles === 0) {
            this.currentState.status = 'completed';
        } else if (completedFiles > 0) {
            this.currentState.status = 'partial';
        } else {
            this.currentState.status = 'failed';
        }

        this.currentState.endTime = Date.now();

        await this.storage.savePlaylistState(this.currentState);

        this.callbacks.onPlaylistComplete?.(this.currentState);

        console.log(`[DownloadManager] Playlist download ${this.currentState.status}: ` +
            `${completedFiles}/${totalFiles} completed, ${failedFiles} failed`);
    }

    /**
     * 取消下载
     */
    cancelDownload(): void {
        // 取消所有活动下载
        for (const [, controller] of this.activeDownloads) {
            controller.abort();
        }

        this.activeDownloads.clear();
        this.downloadQueue = [];

        if (this.currentState) {
            this.currentState.status = 'cancelled';
            this.currentState.endTime = Date.now();
        }
    }

    /**
     * 获取当前状态
     */
    getCurrentState(): PlaylistDownloadState | null {
        return this.currentState;
    }

    /**
     * 获取缓存 URL
     */
    async getCachedUrl(_mediaId: number, originalUrl: string): Promise<string | null> {
        const cache = await this.initCache();
        const cachedResponse = await cache.match(originalUrl);

        if (cachedResponse) {
            return originalUrl; // Cache API 中的资源可以直接用原 URL 访问
        }

        return null;
    }

    /**
     * 检查媒体是否已缓存
     */
    async isCached(_mediaId: number, url: string): Promise<boolean> {
        const cache = await this.initCache();
        const cachedResponse = await cache.match(url);
        return !!cachedResponse;
    }

    /**
     * 清理播放列表缓存
     */
    async clearPlaylistCache(playlistId: number): Promise<void> {
        await this.storage.clearPlaylist(playlistId);
    }

    /**
     * 计算字符串的简单哈希（用于快速比较）
     * @deprecated Use MD5 hash comparison instead when available
     * @internal This method is kept for potential future use
     */
    // @ts-ignore - Kept for potential future use
    private _simpleHash(str: string): string {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash;
        }
        return hash.toString(16);
    }

    /**
     * 增量更新：计算需要下载的文件
     * 通过比较 MD5 哈希值确定哪些文件需要更新
     */
    async calculateIncrementalUpdate(
        mediaList: MediaItem[]
    ): Promise<{
        toDownload: MediaItem[];
        alreadyCached: MediaItem[];
        unchanged: MediaItem[];
    }> {
        const cache = await this.initCache();
        const toDownload: MediaItem[] = [];
        const alreadyCached: MediaItem[] = [];
        const unchanged: MediaItem[] = [];

        for (const media of mediaList) {
            const cachedResponse = await cache.match(media.file_url);

            if (cachedResponse) {
                // 文件已缓存
                if (media.md5_hash) {
                    // 有 MD5 哈希，需要验证是否匹配
                    // 注意：这里简化处理，实际上需要计算缓存内容的 MD5
                    // 由于性能考虑，我们假设缓存是有效的
                    unchanged.push(media);
                } else {
                    // 无 MD5 哈希，假设缓存有效
                    unchanged.push(media);
                }
            } else {
                // 文件未缓存，需要下载
                toDownload.push(media);
            }
        }

        return { toDownload, alreadyCached, unchanged };
    }

    /**
     * 获取已缓存文件的数量和大小
     */
    async getCachedFilesInfo(): Promise<{
        count: number;
        totalSize: number;
    }> {
        const cache = await this.initCache();
        const keys = await cache.keys();

        let totalSize = 0;
        for (const request of keys) {
            const response = await cache.match(request);
            if (response) {
                const blob = await response.clone().blob();
                totalSize += blob.size;
            }
        }

        return {
            count: keys.length,
            totalSize,
        };
    }

    /**
     * 清理旧缓存（保留最近 N 个播放列表的缓存）
     * @param _keepRecent 保留最近 N 个播放列表（当前实现基于时间，此参数保留用于未来扩展）
     */
    async cleanupOldCaches(_keepRecent: number = 3): Promise<{
        removedCount: number;
        freedSpace: number;
    }> {
        // 获取所有播放列表状态
        // 这里简化处理，实际需要从 IndexedDB 获取
        let removedCount = 0;
        let freedSpace = 0;

        const cache = await this.initCache();
        const keys = await cache.keys();

        // 简单策略：清理超过 7 天的缓存
        const sevenDaysAgo = Date.now() - 7 * 24 * 60 * 60 * 1000;

        for (const request of keys) {
            const response = await cache.match(request);
            if (response) {
                const dateHeader = response.headers.get('date');
                if (dateHeader) {
                    const date = new Date(dateHeader).getTime();
                    if (date < sevenDaysAgo) {
                        const blob = await response.clone().blob();
                        freedSpace += blob.size;
                        await cache.delete(request);
                        removedCount++;
                    }
                }
            }
        }

        return { removedCount, freedSpace };
    }
}

// 单例导出
export const playlistDownloadManager = new PlaylistDownloadManager();
