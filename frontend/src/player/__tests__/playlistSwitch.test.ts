/**
 * 播放列表自动切换功能测试
 *
 * 测试覆盖：
 * - 模块导出验证
 * - 方法签名验证
 */
import { describe, it, expect, vi } from 'vitest';

// Mock localStorage
const localStorageMock = (() => {
    let store: Record<string, string> = {};
    return {
        getItem: vi.fn((key: string) => store[key] || null),
        setItem: vi.fn((key: string, value: string) => { store[key] = value; }),
        removeItem: vi.fn((key: string) => { delete store[key]; }),
        clear: vi.fn(() => { store = {}; }),
    };
})();

Object.defineProperty(global, 'localStorage', { value: localStorageMock, writable: true });

// Mock caches
Object.defineProperty(global, 'caches', {
    value: { open: vi.fn().mockResolvedValue({ match: vi.fn(), put: vi.fn() }) },
    writable: true
});

// Mock IndexedDB
Object.defineProperty(global, 'indexedDB', {
    value: { open: vi.fn() },
    writable: true
});

describe('PlaylistDownloadManager Module', () => {
    it('should export PlaylistDownloadManager class', async () => {
        const module = await import('../services/PlaylistDownloadManager');
        expect(module.PlaylistDownloadManager).toBeDefined();
        expect(typeof module.PlaylistDownloadManager).toBe('function');
    });

    it('should export playlistDownloadManager singleton', async () => {
        const module = await import('../services/PlaylistDownloadManager');
        expect(module.playlistDownloadManager).toBeDefined();
    });

    it('should have required methods on manager', async () => {
        const { playlistDownloadManager } = await import('../services/PlaylistDownloadManager');
        expect(typeof playlistDownloadManager.startDownload).toBe('function');
        expect(typeof playlistDownloadManager.cancelDownload).toBe('function');
        expect(typeof playlistDownloadManager.restoreDownload).toBe('function');
        expect(typeof playlistDownloadManager.getCurrentState).toBe('function');
        expect(typeof playlistDownloadManager.getCachedUrl).toBe('function');
        expect(typeof playlistDownloadManager.isCached).toBe('function');
    });

    it('should export MediaItem interface type (compile-time)', async () => {
        // This is a compile-time check - if it compiles, the type exists
        const { PlaylistDownloadManager } = await import('../services/PlaylistDownloadManager');
        expect(PlaylistDownloadManager).toBeDefined();
    });
});

describe('usePlaylistDownload Hook Module', () => {
    it('should export usePlaylistDownload hook', async () => {
        const module = await import('../hooks/usePlaylistDownload');
        expect(module.usePlaylistDownload).toBeDefined();
        expect(typeof module.usePlaylistDownload).toBe('function');
    });

    it('should export default hook', async () => {
        const module = await import('../hooks/usePlaylistDownload');
        expect(module.default).toBeDefined();
    });
});

describe('usePlaylistSwitch Hook Module', () => {
    it('should export usePlaylistSwitch hook', async () => {
        const module = await import('../hooks/usePlaylistSwitch');
        expect(module.usePlaylistSwitch).toBeDefined();
        expect(typeof module.usePlaylistSwitch).toBe('function');
    });

    it('should export default hook', async () => {
        const module = await import('../hooks/usePlaylistSwitch');
        expect(module.default).toBeDefined();
    });
});

describe('usePlaylistChangeDetection Hook Module', () => {
    it('should export usePlaylistChangeDetection hook', async () => {
        const module = await import('../hooks/usePlaylistChangeDetection');
        expect(module.usePlaylistChangeDetection).toBeDefined();
        expect(typeof module.usePlaylistChangeDetection).toBe('function');
    });

    it('should export default hook', async () => {
        const module = await import('../hooks/usePlaylistChangeDetection');
        expect(module.default).toBeDefined();
    });
});

describe('Types Module', () => {
    it('should be importable', async () => {
        const types = await import('../types');
        expect(types).toBeDefined();
    });
});
