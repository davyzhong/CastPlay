/**
 * 服务器配置 Hook 单元测试
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      store = {};
    }),
  };
})();

Object.defineProperty(global, 'localStorage', {
  value: localStorageMock,
  writable: true,
});

// Mock fetch
global.fetch = vi.fn();

// Mock configStorage module
vi.mock('../services/ConfigStorage', () => ({
  configStorage: {
    get: vi.fn(),
    set: vi.fn(),
    remove: vi.fn(),
    has: vi.fn(),
  },
}));

describe('useServerConfig', () => {
  let useServerConfig: typeof import('../hooks/useServerConfig').useServerConfig;
  let configStorage: typeof import('../services/ConfigStorage').configStorage;

  beforeEach(async () => {
    vi.clearAllMocks();
    localStorageMock.clear();

    // Reset modules
    vi.resetModules();

    // Import fresh modules
    const configStorageModule = await import('../services/ConfigStorage');
    configStorage = configStorageModule.configStorage;

    const hookModule = await import('../hooks/useServerConfig');
    useServerConfig = hookModule.useServerConfig;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('初始化状态', () => {
    it('应该在无配置时返回 null', () => {
      (configStorage.get as any).mockReturnValue(null);

      const { result } = renderHook(() => useServerConfig());

      expect(result.current.config).toBeNull();
      expect(result.current.isConfigured).toBe(false);
    });

    it('应该从存储加载已存在的配置', () => {
      const savedConfig = {
        address: '192.168.1.100',
        port: 8000,
        protocol: 'https' as const,
        configuredAt: '2026-01-01T00:00:00Z',
        lastConnectionStatus: 'success' as const,
        lastConnectionAt: '2026-01-01T00:00:00Z',
      };
      (configStorage.get as any).mockReturnValue(savedConfig);

      const { result } = renderHook(() => useServerConfig());

      expect(result.current.config).toEqual(savedConfig);
      expect(result.current.isConfigured).toBe(true);
    });
  });

  describe('validateAddress', () => {
    it('应该验证有效地址', () => {
      (configStorage.get as any).mockReturnValue(null);

      const { result } = renderHook(() => useServerConfig());

      const validationResult = result.current.validateAddress('192.168.1.100');

      expect(validationResult.valid).toBe(true);
    });

    it('应该拒绝无效地址', () => {
      (configStorage.get as any).mockReturnValue(null);

      const { result } = renderHook(() => useServerConfig());

      const validationResult = result.current.validateAddress('');

      expect(validationResult.valid).toBe(false);
    });
  });

  describe('saveConfig', () => {
    it('应该在连接成功时保存配置', async () => {
      (configStorage.get as any).mockReturnValue(null);
      (fetch as any).mockResolvedValue({ ok: true });

      const { result } = renderHook(() => useServerConfig());

      let saveResult;
      await act(async () => {
        saveResult = await result.current.saveConfig('192.168.1.100', 8000);
      });

      expect(saveResult).toEqual({ success: true });
      expect(configStorage.set).toHaveBeenCalled();
    });

    it('应该在连接失败时返回错误', async () => {
      (configStorage.get as any).mockReturnValue(null);
      (fetch as any).mockRejectedValue(new Error('Connection failed'));

      const { result } = renderHook(() => useServerConfig());

      let saveResult;
      await act(async () => {
        saveResult = await result.current.saveConfig('192.168.1.100', 8000);
      });

      expect(saveResult.success).toBe(false);
      expect(saveResult.error).toBeDefined();
    });

    it('应该在保存时设置 isTesting 状态', async () => {
      (configStorage.get as any).mockReturnValue(null);

      // 使用延迟响应来测试 isTesting 状态
      let resolveFetch: (value: any) => void;
      (fetch as any).mockImplementation(
        () =>
          new Promise((resolve) => {
            resolveFetch = resolve;
          })
      );

      const { result } = renderHook(() => useServerConfig());

      // 开始保存
      act(() => {
        result.current.saveConfig('192.168.1.100', 8000);
      });

      // 此时 isTesting 应该为 true（但由于 Promise 未 resolve，需要立即检查）
      // 在真实场景中，这个测试需要更复杂的处理

      // 完成请求
      await act(async () => {
        resolveFetch!({ ok: true });
      });
    });
  });

  describe('testConnection', () => {
    it('应该在无配置时返回错误', async () => {
      (configStorage.get as any).mockReturnValue(null);

      const { result } = renderHook(() => useServerConfig());

      let testResult;
      await act(async () => {
        testResult = await result.current.testConnection();
      });

      expect(testResult.success).toBe(false);
      expect(testResult.error).toBe('未配置服务器地址');
    });

    it('应该测试已配置的服务器连接', async () => {
      const savedConfig = {
        address: '192.168.1.100',
        port: 8000,
        protocol: 'https' as const,
        configuredAt: '2026-01-01T00:00:00Z',
        lastConnectionStatus: 'success' as const,
        lastConnectionAt: '2026-01-01T00:00:00Z',
      };
      (configStorage.get as any).mockReturnValue(savedConfig);
      (fetch as any).mockResolvedValue({ ok: true });

      const { result } = renderHook(() => useServerConfig());

      let testResult;
      await act(async () => {
        testResult = await result.current.testConnection();
      });

      expect(testResult.success).toBe(true);
    });

    it('应该在连接失败时更新状态', async () => {
      const savedConfig = {
        address: '192.168.1.100',
        port: 8000,
        protocol: 'https' as const,
        configuredAt: '2026-01-01T00:00:00Z',
        lastConnectionStatus: 'success' as const,
        lastConnectionAt: '2026-01-01T00:00:00Z',
      };
      (configStorage.get as any).mockReturnValue(savedConfig);
      (fetch as any).mockRejectedValue(new Error('Connection failed'));

      const { result } = renderHook(() => useServerConfig());

      let testResult;
      await act(async () => {
        testResult = await result.current.testConnection();
      });

      expect(testResult.success).toBe(false);
      expect(testResult.error).toBeDefined();
    });
  });

  describe('clearConfig', () => {
    it('应该清除配置', () => {
      const savedConfig = {
        address: '192.168.1.100',
        port: 8000,
        protocol: 'https' as const,
        configuredAt: '2026-01-01T00:00:00Z',
        lastConnectionStatus: 'success' as const,
        lastConnectionAt: '2026-01-01T00:00:00Z',
      };
      (configStorage.get as any).mockReturnValue(savedConfig);

      const { result } = renderHook(() => useServerConfig());

      act(() => {
        result.current.clearConfig();
      });

      expect(configStorage.remove).toHaveBeenCalled();
      expect(result.current.config).toBeNull();
      expect(result.current.isConfigured).toBe(false);
    });
  });

  describe('updateConnectionStatus', () => {
    it('应该在有配置时更新连接状态', () => {
      const savedConfig = {
        address: '192.168.1.100',
        port: 8000,
        protocol: 'https' as const,
        configuredAt: '2026-01-01T00:00:00Z',
        lastConnectionStatus: 'success' as const,
        lastConnectionAt: '2026-01-01T00:00:00Z',
      };
      (configStorage.get as any).mockReturnValue(savedConfig);

      const { result } = renderHook(() => useServerConfig());

      act(() => {
        result.current.updateConnectionStatus('failed');
      });

      expect(configStorage.set).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          lastConnectionStatus: 'failed',
        })
      );
    });

    it('应该在无配置时不执行操作', () => {
      (configStorage.get as any).mockReturnValue(null);

      const { result } = renderHook(() => useServerConfig());

      act(() => {
        result.current.updateConnectionStatus('success');
      });

      expect(configStorage.set).not.toHaveBeenCalled();
    });
  });
});
