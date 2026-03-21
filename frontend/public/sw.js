/**
 * CastPlay Service Worker
 * 提供静态资源缓存和离线访问支持
 */

const CACHE_NAME = 'castplay-player-v1';
const STATIC_CACHE_NAME = 'castplay-static-v1';
const MEDIA_CACHE_NAME = 'castplay-media-v1';

// 需要缓存的静态资源
const STATIC_ASSETS = [
    '/',
    '/index.html',
    '/player',
    '/manifest.json',
];

// 安装事件 - 缓存静态资源
self.addEventListener('install', (event) => {
    console.log('[SW] Installing Service Worker');
    event.waitUntil(
        caches.open(STATIC_CACHE_NAME)
            .then((cache) => {
                console.log('[SW] Caching static assets');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => self.skipWaiting())
            .catch((error) => {
                console.error('[SW] Failed to cache static assets:', error);
            })
    );
});

// 激活事件 - 清理旧缓存
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating Service Worker');
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames
                        .filter((name) => {
                            return name !== STATIC_CACHE_NAME &&
                                   name !== MEDIA_CACHE_NAME &&
                                   name !== CACHE_NAME;
                        })
                        .map((name) => {
                            console.log('[SW] Deleting old cache:', name);
                            return caches.delete(name);
                        })
                );
            })
            .then(() => self.clients.claim())
    );
});

// 请求拦截 - 缓存优先策略（静态资源），网络优先策略（API）
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // 只处理同源请求
    if (url.origin !== location.origin) {
        return;
    }

    // API 请求 - 网络优先
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(networkFirst(request));
        return;
    }

    // 媒体文件 - 网络优先，带缓存
    if (isMediaFile(url.pathname)) {
        event.respondWith(networkFirstWithCache(request));
        return;
    }

    // 静态资源 - 缓存优先
    event.respondWith(cacheFirst(request));
});

/**
 * 缓存优先策略
 */
async function cacheFirst(request) {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
        return cachedResponse;
    }

    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            const cache = await caches.open(STATIC_CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    } catch (error) {
        console.error('[SW] Fetch failed for:', request.url, error);
        // 返回离线页面（如果存在）
        return caches.match('/offline.html');
    }
}

/**
 * 网络优先策略
 */
async function networkFirst(request) {
    try {
        const networkResponse = await fetch(request);
        return networkResponse;
    } catch (error) {
        console.log('[SW] Network failed, trying cache for:', request.url);
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        // 返回错误响应
        return new Response(JSON.stringify({ error: 'Offline', message: 'Network unavailable' }), {
            status: 503,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

/**
 * 网络优先策略（带缓存）
 */
async function networkFirstWithCache(request) {
    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            const cache = await caches.open(MEDIA_CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    } catch (error) {
        console.log('[SW] Network failed for media, trying cache:', request.url);
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        return new Response('Media not available offline', { status: 503 });
    }
}

/**
 * 判断是否为媒体文件
 */
function isMediaFile(pathname) {
    const mediaExtensions = ['.mp4', '.webm', '.mp3', '.wav', '.jpg', '.jpeg', '.png', '.gif', '.webp'];
    return mediaExtensions.some(ext => pathname.toLowerCase().endsWith(ext));
}

// 消息处理
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }

    if (event.data && event.data.type === 'CACHE_MEDIA') {
        const { urls } = event.data;
        cacheMediaFiles(urls);
    }

    if (event.data && event.data.type === 'CLEAR_MEDIA_CACHE') {
        clearMediaCache();
    }

    if (event.data && event.data.type === 'GET_CACHE_STATUS') {
        getCacheStatus().then((status) => {
            event.ports[0].postMessage(status);
        });
    }
});

/**
 * 缓存媒体文件
 */
async function cacheMediaFiles(urls) {
    const cache = await caches.open(MEDIA_CACHE_NAME);
    for (const url of urls) {
        try {
            const response = await fetch(url);
            if (response.ok) {
                await cache.put(url, response);
                console.log('[SW] Cached media:', url);
            }
        } catch (error) {
            console.error('[SW] Failed to cache media:', url, error);
        }
    }
}

/**
 * 清理媒体缓存
 */
async function clearMediaCache() {
    await caches.delete(MEDIA_CACHE_NAME);
    console.log('[SW] Media cache cleared');
}

/**
 * 获取缓存状态
 */
async function getCacheStatus() {
    const cacheNames = await caches.keys();
    const status = {
        caches: {},
        totalSize: 0
    };

    for (const name of cacheNames) {
        const cache = await caches.open(name);
        const keys = await cache.keys();
        status.caches[name] = keys.length;
    }

    return status;
}

// 后台同步（如果支持）
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-heartbeat') {
        event.waitUntil(syncHeartbeat());
    }
});

/**
 * 同步心跳
 */
async function syncHeartbeat() {
    try {
        const heartbeatData = await getStoredHeartbeatData();
        if (heartbeatData) {
            await fetch('/api/player/heartbeat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(heartbeatData)
            });
            clearStoredHeartbeatData();
        }
    } catch (error) {
        console.error('[SW] Sync heartbeat failed:', error);
    }
}

/**
 * 获取存储的心跳数据（从 IndexedDB）
 */
async function getStoredHeartbeatData() {
    // 简化实现，实际应使用 IndexedDB
    return null;
}

/**
 * 清除存储的心跳数据
 */
async function clearStoredHeartbeatData() {
    // 简化实现
}

console.log('[SW] Service Worker loaded');
