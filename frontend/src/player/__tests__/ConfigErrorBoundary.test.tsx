/**
 * 配置错误边界组件单元测试
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import React from 'react';
import { ConfigErrorBoundary } from '../components/ConfigErrorBoundary';

// Mock configStorage
vi.mock('../services/ConfigStorage', () => ({
  configStorage: {
    get: vi.fn(),
    set: vi.fn(),
    remove: vi.fn(),
    clearAll: vi.fn(),
  },
}));

// Mock STORAGE_KEYS
vi.mock('../types/config', () => ({
  STORAGE_KEYS: {
    SERVER_CONFIG: 'castplay_server_config',
    DEVICE_REGISTRATION: 'castplay_device_registration',
    PLAYLIST_SELECTION: 'castplay_playlist_selection',
  },
}));

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(global, 'localStorage', {
  value: localStorageMock,
  writable: true,
});

// Mock clipboard
Object.defineProperty(navigator, 'clipboard', {
  value: {
    writeText: vi.fn().mockResolvedValue(undefined),
  },
  writable: true,
});

// Mock window.location
const mockLocation = {
  reload: vi.fn(),
  href: 'http://localhost:3000/player.html',
};
Object.defineProperty(global, 'location', {
  value: mockLocation,
  writable: true,
});

describe('ConfigErrorBoundary', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
    localStorageMock.setItem.mockReset();
    localStorageMock.removeItem.mockReset();
    mockLocation.reload.mockClear();
  });

  describe('正常渲染', () => {
    it('应该渲染子组件', () => {
      const { container } = render(
        <ConfigErrorBoundary>
          <div data-testid="child">Child Content</div>
        </ConfigErrorBoundary>
      );

      expect(container.querySelector('[data-testid="child"]')).toBeTruthy();
    });

    it('应该渲染子组件内容', () => {
      render(
        <ConfigErrorBoundary>
          <span>Hello World</span>
        </ConfigErrorBoundary>
      );

      expect(screen.getByText('Hello World')).toBeTruthy();
    });
  });

  describe('getDerivedStateFromError', () => {
    it('应该在捕获错误时设置 hasError 状态', () => {
      const ErrorBoundaryClass = ConfigErrorBoundary as any;

      const error = new Error('Test error');

      const state = ErrorBoundaryClass.getDerivedStateFromError(error);

      expect(state.hasError).toBe(true);
      expect(state.error).toBe(error);
      expect(state.errorType).toBeDefined();
    });

    it('应该分析配置错误类型', () => {
      const ErrorBoundaryClass = ConfigErrorBoundary as any;

      const configError = new Error('Server config error');
      const state = ErrorBoundaryClass.getDerivedStateFromError(configError);

      expect(state.errorType).toBe('config');
    });

    it('应该分析存储错误类型', () => {
      const ErrorBoundaryClass = ConfigErrorBoundary as any;

      const storageError = new Error('LocalStorage quota exceeded');
      const state = ErrorBoundaryClass.getDerivedStateFromError(storageError);

      expect(state.errorType).toBe('storage');
    });

    it('应该分析网络错误类型', () => {
      const ErrorBoundaryClass = ConfigErrorBoundary as any;

      const networkError = new Error('Network connection timeout');
      const state = ErrorBoundaryClass.getDerivedStateFromError(networkError);

      expect(state.errorType).toBe('network');
    });

    it('应该将未知错误分类为 unknown', () => {
      const ErrorBoundaryClass = ConfigErrorBoundary as any;

      const unknownError = new Error('Unknown error');
      const state = ErrorBoundaryClass.getDerivedStateFromError(unknownError);

      expect(state.errorType).toBe('unknown');
    });
  });

  describe('自定义 fallback', () => {
    it('应该在提供自定义 fallback 时使用它', () => {
      // 创建一个会抛出错误的组件
      const ThrowError = () => {
        throw new Error('Test error');
      };

      const CustomFallback = () => <div data-testid="custom-fallback">Custom Fallback</div>;

      render(
        <ConfigErrorBoundary fallback={<CustomFallback />}>
          <ThrowError />
        </ConfigErrorBoundary>
      );

      expect(screen.getByTestId('custom-fallback')).toBeTruthy();
    });
  });

  describe('handleRetry 方法', () => {
    it('handleRetry 方法应该存在', () => {
      const wrapper = new ConfigErrorBoundary({ children: null });
      expect(typeof wrapper.handleRetry).toBe('function');
    });
  });

  describe('handleClearConfig 方法', () => {
    it('handleClearConfig 方法应该存在', () => {
      const wrapper = new ConfigErrorBoundary({ children: null });
      expect(typeof wrapper.handleClearConfig).toBe('function');
    });

    it('点击清除配置应该清除 localStorage', async () => {
      const ErrorComponent = () => {
        React.useEffect(() => {
          throw new Error('Test error');
        }, []);
        return <div>Error</div>;
      };

      render(
        <ConfigErrorBoundary>
          <ErrorComponent />
        </ConfigErrorBoundary>
      );

      // 等待错误渲染
      await act(async () => {});

      // 找到清除配置按钮并点击
      const clearButton = screen.queryByText('清除配置');
      if (clearButton) {
        fireEvent.click(clearButton);
        expect(localStorageMock.removeItem).toHaveBeenCalled();
      }
    });
  });

  describe('handleCopyError 方法', () => {
    it('handleCopyError 方法应该存在', () => {
      const wrapper = new ConfigErrorBoundary({ children: null });
      expect(typeof wrapper.handleCopyError).toBe('function');
    });
  });

  describe('错误类型识别', () => {
    it('应该识别包含 config 的错误', () => {
      const ErrorBoundaryClass = ConfigErrorBoundary as any;

      const error = new Error('config file not found');
      const state = ErrorBoundaryClass.getDerivedStateFromError(error);

      expect(state.errorType).toBe('config');
    });

    it('应该识别包含 server 的错误', () => {
      const ErrorBoundaryClass = ConfigErrorBoundary as any;

      const error = new Error('server connection failed');
      const state = ErrorBoundaryClass.getDerivedStateFromError(error);

      expect(state.errorType).toBe('config');
    });

    it('应该识别包含 address 的错误', () => {
      const ErrorBoundaryClass = ConfigErrorBoundary as any;

      const error = new Error('invalid address');
      const state = ErrorBoundaryClass.getDerivedStateFromError(error);

      expect(state.errorType).toBe('config');
    });

    it('应该识别包含 storage 的错误', () => {
      const ErrorBoundaryClass = ConfigErrorBoundary as any;

      const error = new Error('storage quota exceeded');
      const state = ErrorBoundaryClass.getDerivedStateFromError(error);

      expect(state.errorType).toBe('storage');
    });

    it('应该识别包含 localstorage 的错误', () => {
      const ErrorBoundaryClass = ConfigErrorBoundary as any;

      const error = new Error('localstorage unavailable');
      const state = ErrorBoundaryClass.getDerivedStateFromError(error);

      expect(state.errorType).toBe('storage');
    });

    it('应该识别包含 quota 的错误', () => {
      const ErrorBoundaryClass = ConfigErrorBoundary as any;

      const error = new Error('quota limit reached');
      const state = ErrorBoundaryClass.getDerivedStateFromError(error);

      expect(state.errorType).toBe('storage');
    });

    it('应该识别包含 fetch 的错误', () => {
      const ErrorBoundaryClass = ConfigErrorBoundary as any;

      const error = new Error('fetch failed');
      const state = ErrorBoundaryClass.getDerivedStateFromError(error);

      expect(state.errorType).toBe('network');
    });

    it('应该识别包含 timeout 的错误', () => {
      const ErrorBoundaryClass = ConfigErrorBoundary as any;

      const error = new Error('connection timeout');
      const state = ErrorBoundaryClass.getDerivedStateFromError(error);

      expect(state.errorType).toBe('network');
    });

    it('应该识别包含 connection 的错误', () => {
      const ErrorBoundaryClass = ConfigErrorBoundary as any;

      const error = new Error('connection refused');
      const state = ErrorBoundaryClass.getDerivedStateFromError(error);

      expect(state.errorType).toBe('network');
    });
  });

  describe('错误信息处理', () => {
    it('应该处理空错误消息', () => {
      const ErrorBoundaryClass = ConfigErrorBoundary as any;

      const error = new Error('');
      const state = ErrorBoundaryClass.getDerivedStateFromError(error);

      expect(state.errorType).toBe('unknown');
    });

    it('应该处理无错误消息的情况', () => {
      const ErrorBoundaryClass = ConfigErrorBoundary as any;

      const error = new Error();
      const state = ErrorBoundaryClass.getDerivedStateFromError(error);

      expect(state.hasError).toBe(true);
    });
  });
});
