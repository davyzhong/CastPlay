/**
 * 下载管理器单元测试
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { DownloadManager, DownloadState, NotificationType } from '../services/DownloadManager';

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock navigator.storage
Object.defineProperty(global.navigator, 'storage', {
  value: {
    estimate: vi.fn().mockResolvedValue({ quota: 1024 * 1024 * 1024, usage: 0 }),
  },
  writable: true,
});

describe('DownloadManager', () => {
  let downloadManager: DownloadManager;

  const createTask = (overrides: Partial<Parameters<typeof DownloadManager.prototype.addTask>[0]> = {}) => ({
    id: `task-${Date.now()}-${Math.random()}`,
    url: 'https://example.com/media/test.mp4',
    targetPath: '/data/media/test.mp4',
    mediaType: 'video/mp4',
    priority: 2,
    playlistId: 1,
    retryCount: 0,
    ...overrides,
  });

  beforeEach(() => {
    vi.clearAllMocks();
    mockFetch.mockReset();

    // Mock fetch 返回成功响应（模拟）
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
    });

    downloadManager = new DownloadManager('device-123');
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('构造函数', () => {
    it('应该创建下载管理器实例', () => {
      expect(downloadManager).toBeInstanceOf(DownloadManager);
    });
  });

  describe('getState', () => {
    it('应该返回当前状态', () => {
      const state = downloadManager.getState();
      expect(Object.values(DownloadState)).toContain(state);
    });

    it('初始状态应该是 IDLE', () => {
      const state = downloadManager.getState();
      expect(state).toBe(DownloadState.IDLE);
    });
  });

  describe('getQueueLength', () => {
    it('应该返回队列长度', () => {
      const length = downloadManager.getQueueLength();
      expect(typeof length).toBe('number');
      expect(length).toBeGreaterThanOrEqual(0);
    });
  });

  describe('getActiveDownloads', () => {
    it('应该返回活跃下载数', () => {
      const count = downloadManager.getActiveDownloads();
      expect(typeof count).toBe('number');
      expect(count).toBeGreaterThanOrEqual(0);
    });
  });

  describe('checkStorageSpace', () => {
    it('应该在存储空间充足时返回 true', async () => {
      const result = await downloadManager.checkStorageSpace(100); // 100MB
      expect(result).toBe(true);
    });

    it('应该在存储空间不足时返回 false', async () => {
      Object.defineProperty(global.navigator, 'storage', {
        value: {
          estimate: vi.fn().mockResolvedValue({ quota: 50 * 1024 * 1024, usage: 40 * 1024 * 1024 }),
        },
        writable: true,
      });

      const result = await downloadManager.checkStorageSpace(100);
      expect(result).toBe(false);
    });

    it('应该在 storage API 不可用时返回 false', async () => {
      Object.defineProperty(global.navigator, 'storage', {
        value: undefined,
        writable: true,
      });

      const result = await downloadManager.checkStorageSpace(100);
      expect(result).toBe(false);
    });
  });

  describe('cleanupAllTempFiles', () => {
    it('应该清理所有临时文件而不抛出错误', async () => {
      // 不应该抛出错误
      await expect(downloadManager.cleanupAllTempFiles()).resolves.not.toThrow();
    });
  });

  describe('getAllTempFiles', () => {
    it('应该返回临时文件数组', async () => {
      const files = await downloadManager.getAllTempFiles();
      expect(Array.isArray(files)).toBe(true);
    });
  });
});

describe('DownloadState 枚举', () => {
  it('应该包含 IDLE 状态', () => {
    expect(DownloadState.IDLE).toBe('idle');
  });

  it('应该包含 DOWNLOADING 状态', () => {
    expect(DownloadState.DOWNLOADING).toBe('downloading');
  });

  it('应该包含 COMPLETED 状态', () => {
    expect(DownloadState.COMPLETED).toBe('completed');
  });

  it('应该包含 FAILED 状态', () => {
    expect(DownloadState.FAILED).toBe('failed');
  });

  it('应该包含所有状态', () => {
    expect(DownloadState.IDLE).toBe('idle');
    expect(DownloadState.CHECKING).toBe('checking');
    expect(DownloadState.DOWNLOADING).toBe('downloading');
    expect(DownloadState.VERIFYING).toBe('verifying');
    expect(DownloadState.WAITING_SWITCH).toBe('waiting_switch');
    expect(DownloadState.SWITCHING).toBe('switching');
    expect(DownloadState.COMPLETED).toBe('completed');
    expect(DownloadState.FAILED).toBe('failed');
    expect(DownloadState.RETRYING).toBe('retrying');
  });
});

describe('NotificationType 枚举', () => {
  it('应该包含 DOWNLOAD_SUCCESS 类型', () => {
    expect(NotificationType.DOWNLOAD_SUCCESS).toBe('download_success');
  });

  it('应该包含 DOWNLOAD_FAILED 类型', () => {
    expect(NotificationType.DOWNLOAD_FAILED).toBe('download_failed');
  });

  it('应该包含 INSUFFICIENT_STORAGE 类型', () => {
    expect(NotificationType.INSUFFICIENT_STORAGE).toBe('insufficient_storage');
  });

  it('应该包含 SWITCH_FAILED 类型', () => {
    expect(NotificationType.SWITCH_FAILED).toBe('switch_failed');
  });

  it('应该包含所有通知类型', () => {
    expect(NotificationType.DOWNLOAD_SUCCESS).toBe('download_success');
    expect(NotificationType.DOWNLOAD_FAILED).toBe('download_failed');
    expect(NotificationType.INSUFFICIENT_STORAGE).toBe('insufficient_storage');
    expect(NotificationType.SWITCH_FAILED).toBe('switch_failed');
  });
});

describe('DownloadManager - 多次实例化', () => {
  it('应该可以创建多个独立的实例', () => {
    const manager1 = new DownloadManager('device-1');
    const manager2 = new DownloadManager('device-2');

    expect(manager1).toBeInstanceOf(DownloadManager);
    expect(manager2).toBeInstanceOf(DownloadManager);
    expect(manager1).not.toBe(manager2);
  });
});
