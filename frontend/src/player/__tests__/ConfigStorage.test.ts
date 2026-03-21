/**
 * 配置存储抽象层单元测试
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

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
    get length() {
      return Object.keys(store).length;
    },
    key: vi.fn((index: number) => Object.keys(store)[index] || null),
  };
})();

Object.defineProperty(global, 'localStorage', {
  value: localStorageMock,
  writable: true,
});

// Mock navigator.clipboard
const clipboardMock = {
  writeText: vi.fn().mockResolvedValue(undefined),
};
Object.defineProperty(navigator, 'clipboard', {
  value: clipboardMock,
  writable: true,
});

// Mock document.execCommand
document.execCommand = vi.fn().mockReturnValue(true);

describe('ConfigStorage (Web)', () => {
  let ConfigStorage: typeof import('../services/ConfigStorage').ConfigStorage;
  let configStorage: import('../services/ConfigStorage').configStorage;

  beforeEach(async () => {
    vi.clearAllMocks();
    localStorageMock.clear();

    // Reset singleton
    const module = await import('../services/ConfigStorage');
    ConfigStorage = module.ConfigStorage;
    // Access private static instance to reset
    (ConfigStorage as any).instance = undefined;
    configStorage = ConfigStorage.getInstance();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('getInstance', () => {
    it('应该返回单例实例', () => {
      const instance1 = ConfigStorage.getInstance();
      const instance2 = ConfigStorage.getInstance();
      expect(instance1).toBe(instance2);
    });
  });

  describe('getPlatform', () => {
    it('应该在 Web 环境返回 web', () => {
      expect(configStorage.getPlatform()).toBe('web');
    });
  });

  describe('get', () => {
    it('应该读取并解析 JSON 配置', () => {
      const testData = { name: 'test', value: 123 };
      localStorageMock.getItem.mockReturnValue(JSON.stringify(testData));

      const result = configStorage.get<{ name: string; value: number }>('test-key');

      expect(result).toEqual(testData);
      expect(localStorageMock.getItem).toHaveBeenCalledWith('test-key');
    });

    it('应该在值不存在时返回 null', () => {
      localStorageMock.getItem.mockReturnValue(null);

      const result = configStorage.get('nonexistent-key');

      expect(result).toBeNull();
    });

    it('应该在 JSON 解析失败时返回 null', () => {
      localStorageMock.getItem.mockReturnValue('invalid-json');

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation();
      const result = configStorage.get('invalid-key');

      expect(result).toBeNull();
      expect(consoleSpy).toHaveBeenCalled();
      consoleSpy.mockRestore();
    });

    it('应该在空字符串时返回 null', () => {
      localStorageMock.getItem.mockReturnValue('');

      const result = configStorage.get('empty-key');

      expect(result).toBeNull();
    });
  });

  describe('set', () => {
    it('应该保存对象为 JSON 字符串', () => {
      const testData = { name: 'test', value: 123 };

      configStorage.set('test-key', testData);

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'test-key',
        JSON.stringify(testData)
      );
    });

    it('应该保存数组', () => {
      const testData = [1, 2, 3];

      configStorage.set('array-key', testData);

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'array-key',
        JSON.stringify(testData)
      );
    });

    it('应该保存原始值', () => {
      configStorage.set('string-key', 'test-string');
      configStorage.set('number-key', 42);
      configStorage.set('boolean-key', true);

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'string-key',
        '"test-string"'
      );
      expect(localStorageMock.setItem).toHaveBeenCalledWith('number-key', '42');
      expect(localStorageMock.setItem).toHaveBeenCalledWith('boolean-key', 'true');
    });
  });

  describe('remove', () => {
    it('应该删除指定键', () => {
      configStorage.remove('test-key');

      expect(localStorageMock.removeItem).toHaveBeenCalledWith('test-key');
    });
  });

  describe('has', () => {
    it('应该在键存在时返回 true', () => {
      localStorageMock.getItem.mockReturnValue('{"test":"value"}');

      expect(configStorage.has('existing-key')).toBe(true);
    });

    it('应该在键不存在时返回 false', () => {
      localStorageMock.getItem.mockReturnValue(null);

      expect(configStorage.has('nonexistent-key')).toBe(false);
    });

    it('应该在值为空字符串时返回 false', () => {
      localStorageMock.getItem.mockReturnValue('');

      expect(configStorage.has('empty-key')).toBe(false);
    });
  });

  describe('clearAll', () => {
    it('应该清除所有配置键', () => {
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation();

      configStorage.clearAll();

      // 检查是否调用了 removeItem（内部会调用多次）
      expect(localStorageMock.removeItem).toHaveBeenCalled();
      expect(consoleSpy).toHaveBeenCalledWith('[ConfigStorage] Cleared all config');

      consoleSpy.mockRestore();
    });
  });

  describe('copyToClipboard', () => {
    it('应该使用 navigator.clipboard 在 Web 环境复制文本', async () => {
      const result = await configStorage.copyToClipboard('test-text');

      expect(clipboardMock.writeText).toHaveBeenCalledWith('test-text');
      expect(result).toBe(true);
    });

    it('应该在 clipboard API 失败时使用 execCommand 降级方案', async () => {
      clipboardMock.writeText.mockRejectedValueOnce(new Error('Clipboard failed'));

      // Mock document methods
      const textarea = document.createElement('textarea');
      vi.spyOn(document, 'createElement').mockReturnValue(textarea);
      vi.spyOn(document.body, 'appendChild').mockImplementation(() => textarea);
      vi.spyOn(document.body, 'removeChild').mockImplementation(() => textarea);

      const result = await configStorage.copyToClipboard('test-text');

      expect(document.execCommand).toHaveBeenCalledWith('copy');
      expect(result).toBe(true);
    });

    it('应该在所有复制方法都失败时返回 false', async () => {
      clipboardMock.writeText.mockRejectedValueOnce(new Error('Clipboard failed'));
      (document.execCommand as any).mockReturnValueOnce(false);

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation();

      const textarea = document.createElement('textarea');
      vi.spyOn(document, 'createElement').mockReturnValue(textarea);
      vi.spyOn(document.body, 'appendChild').mockImplementation(() => textarea);
      vi.spyOn(document.body, 'removeChild').mockImplementation(() => textarea);

      const result = await configStorage.copyToClipboard('test-text');

      expect(result).toBe(false);

      consoleSpy.mockRestore();
    });
  });
});

describe('ConfigStorage (Android)', () => {
  // Mock AndroidBridge
  const androidBridgeMock = {
    getConfig: vi.fn(),
    setConfig: vi.fn(),
    copyToClipboard: vi.fn().mockReturnValue(true),
  };

  beforeEach(async () => {
    vi.clearAllMocks();
    localStorageMock.clear();

    // Set up AndroidBridge before importing
    (window as any).AndroidBridge = androidBridgeMock;

    // Reset modules and re-import
    vi.resetModules();
  });

  afterEach(() => {
    delete (window as any).AndroidBridge;
    vi.restoreAllMocks();
  });

  describe('getPlatform', () => {
    it('应该在 Android 环境返回 android', async () => {
      const { ConfigStorage } = await import('../services/ConfigStorage');
      // Reset singleton
      (ConfigStorage as any).instance = undefined;

      const configStorage = ConfigStorage.getInstance();
      expect(configStorage.getPlatform()).toBe('android');
    });
  });

  describe('get (Android)', () => {
    it('应该从 AndroidBridge 读取配置', async () => {
      const testData = { name: 'test', value: 123 };
      androidBridgeMock.getConfig.mockReturnValue(JSON.stringify(testData));

      const { ConfigStorage } = await import('../services/ConfigStorage');
      (ConfigStorage as any).instance = undefined;

      const configStorage = ConfigStorage.getInstance();
      const result = configStorage.get<{ name: string; value: number }>('test-key');

      expect(result).toEqual(testData);
      expect(androidBridgeMock.getConfig).toHaveBeenCalledWith('test-key');
    });

    it('应该使用缓存避免重复读取', async () => {
      const testData = { name: 'test' };
      androidBridgeMock.getConfig.mockReturnValue(JSON.stringify(testData));

      const { ConfigStorage } = await import('../services/ConfigStorage');
      (ConfigStorage as any).instance = undefined;

      const configStorage = ConfigStorage.getInstance();
      configStorage.get('test-key');
      configStorage.get('test-key');

      expect(androidBridgeMock.getConfig).toHaveBeenCalledTimes(1);
    });

    it('应该在 AndroidBridge 返回空字符串时返回 null', async () => {
      androidBridgeMock.getConfig.mockReturnValue('');

      const { ConfigStorage } = await import('../services/ConfigStorage');
      (ConfigStorage as any).instance = undefined;

      const configStorage = ConfigStorage.getInstance();
      const result = configStorage.get('empty-key');

      expect(result).toBeNull();
    });
  });

  describe('set (Android)', () => {
    it('应该保存到 AndroidBridge', async () => {
      const testData = { name: 'test' };

      const { ConfigStorage } = await import('../services/ConfigStorage');
      (ConfigStorage as any).instance = undefined;

      const configStorage = ConfigStorage.getInstance();
      configStorage.set('test-key', testData);

      expect(androidBridgeMock.setConfig).toHaveBeenCalledWith(
        'test-key',
        JSON.stringify(testData)
      );
    });
  });

  describe('remove (Android)', () => {
    it('应该通过设置空字符串删除', async () => {
      const { ConfigStorage } = await import('../services/ConfigStorage');
      (ConfigStorage as any).instance = undefined;

      const configStorage = ConfigStorage.getInstance();
      configStorage.remove('test-key');

      expect(androidBridgeMock.setConfig).toHaveBeenCalledWith('test-key', '');
    });
  });

  describe('copyToClipboard (Android)', () => {
    it('应该使用 AndroidBridge 复制文本', async () => {
      const { ConfigStorage } = await import('../services/ConfigStorage');
      (ConfigStorage as any).instance = undefined;

      const configStorage = ConfigStorage.getInstance();
      const result = await configStorage.copyToClipboard('test-text');

      expect(androidBridgeMock.copyToClipboard).toHaveBeenCalledWith('test-text');
      expect(result).toBe(true);
    });
  });
});
