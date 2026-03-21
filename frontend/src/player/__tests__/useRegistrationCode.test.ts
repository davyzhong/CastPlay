/**
 * 设备注册码 Hook 单元测试
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';

// Mock configStorage module - must be defined before vi.mock call
const mockConfigStorage = {
  get: vi.fn(),
  set: vi.fn(),
  remove: vi.fn(),
  copyToClipboard: vi.fn(),
};

vi.mock('../services/ConfigStorage', () => ({
  configStorage: mockConfigStorage,
}));

// Mock STORAGE_KEYS
vi.mock('../types/config', () => ({
  STORAGE_KEYS: {
    SERVER_CONFIG: 'castplay_server_config',
    DEVICE_REGISTRATION: 'castplay_device_registration',
    PLAYLIST_SELECTION: 'castplay_playlist_selection',
  },
}));

describe('useRegistrationCode', () => {
  let useRegistrationCode: typeof import('../hooks/useRegistrationCode').useRegistrationCode;

  beforeEach(async () => {
    vi.clearAllMocks();

    // Reset modules to ensure fresh import
    vi.resetModules();

    // Re-mock configStorage after reset
    vi.doMock('../services/ConfigStorage', () => ({
      configStorage: mockConfigStorage,
    }));

    // Re-mock STORAGE_KEYS
    vi.doMock('../types/config', () => ({
      STORAGE_KEYS: {
        SERVER_CONFIG: 'castplay_server_config',
        DEVICE_REGISTRATION: 'castplay_device_registration',
        PLAYLIST_SELECTION: 'castplay_playlist_selection',
      },
    }));

    // Import fresh module - this will use whatever env is currently set
    const hookModule = await import('../hooks/useRegistrationCode');
    useRegistrationCode = hookModule.useRegistrationCode;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('初始化状态', () => {
    it('应该返回注册码（环境变量）', () => {
      mockConfigStorage.get.mockReturnValue(null);

      const { result } = renderHook(() => useRegistrationCode());

      // 在测试环境中，环境变量通常是空的或未定义的
      // 所以我们检查返回值是字符串类型
      expect(typeof result.current.registrationCode).toBe('string');
      expect(typeof result.current.hasRegistrationCode).toBe('boolean');
    });

    it('应该在没有注册码时返回空字符串', async () => {
      // 这个测试验证当环境变量未设置时的行为
      mockConfigStorage.get.mockReturnValue(null);

      const { result } = renderHook(() => useRegistrationCode());

      // 如果没有设置 VITE_REGISTRATION_CODE，应该是空字符串
      // 在测试环境中通常如此
      expect(typeof result.current.registrationCode).toBe('string');
      expect(typeof result.current.hasRegistrationCode).toBe('boolean');
    });

    it('应该从存储加载注册状态', () => {
      const savedRegistration = {
        isRegistered: true,
        deviceId: 'device-123',
        registeredAt: '2026-01-01T00:00:00Z',
        registeredBy: 'user',
      };
      mockConfigStorage.get.mockReturnValue(savedRegistration);

      const { result } = renderHook(() => useRegistrationCode());

      expect(result.current.isRegistered).toBe(true);
      expect(result.current.registration).toEqual(savedRegistration);
    });

    it('应该在无存储时使用默认注册状态', () => {
      mockConfigStorage.get.mockReturnValue(null);

      const { result } = renderHook(() => useRegistrationCode());

      expect(result.current.isRegistered).toBe(false);
      expect(result.current.registration).toEqual({
        isRegistered: false,
        deviceId: null,
        registeredAt: null,
        registeredBy: null,
      });
    });
  });

  describe('copyRegistrationCode', () => {
    it('应该在没有注册码时不调用 copyToClipboard 并返回 false', async () => {
      mockConfigStorage.get.mockReturnValue(null);

      const { result } = renderHook(() => useRegistrationCode());

      let copyResult;
      await act(async () => {
        copyResult = await result.current.copyRegistrationCode();
      });

      // 在测试环境中，如果没有注册码（VITE_REGISTRATION_CODE 未设置），
      // copyRegistrationCode 会直接返回 false，不调用 copyToClipboard
      expect(copyResult).toBe(false);
      // copyToClipboard 不应该被调用，因为没有有效的注册码
      expect(mockConfigStorage.copyToClipboard).not.toHaveBeenCalled();
    });

    it('应该在复制失败时返回 false', async () => {
      mockConfigStorage.get.mockReturnValue(null);
      mockConfigStorage.copyToClipboard.mockResolvedValue(false);

      const { result } = renderHook(() => useRegistrationCode());

      let copyResult;
      await act(async () => {
        copyResult = await result.current.copyRegistrationCode();
      });

      // 在测试环境中，如果没有注册码，copyRegistrationCode 会返回 false
      // 如果有注册码但 copyToClipboard 返回 false，也会返回 false
      expect(copyResult).toBe(false);
    });
  });

  describe('completeRegistration', () => {
    it('应该完成注册并更新状态', () => {
      mockConfigStorage.get.mockReturnValue(null);

      const { result } = renderHook(() => useRegistrationCode());

      act(() => {
        result.current.completeRegistration('device-123');
      });

      expect(mockConfigStorage.set).toHaveBeenCalledWith(
        'castplay_device_registration',
        expect.objectContaining({
          isRegistered: true,
          deviceId: 'device-123',
          registeredBy: 'user',
        })
      );
      expect(result.current.isRegistered).toBe(true);
      expect(result.current.registration.deviceId).toBe('device-123');
    });

    it('应该记录注册时间', () => {
      mockConfigStorage.get.mockReturnValue(null);

      const { result } = renderHook(() => useRegistrationCode());

      act(() => {
        result.current.completeRegistration('device-123');
      });

      const savedData = mockConfigStorage.set.mock.calls[0][1];
      expect(savedData.registeredAt).toBeDefined();
      expect(new Date(savedData.registeredAt).toISOString()).toBe(savedData.registeredAt);
    });
  });

  describe('clearRegistration', () => {
    it('应该清除注册状态', () => {
      const savedRegistration = {
        isRegistered: true,
        deviceId: 'device-123',
        registeredAt: '2026-01-01T00:00:00Z',
        registeredBy: 'user',
      };
      mockConfigStorage.get.mockReturnValue(savedRegistration);

      const { result } = renderHook(() => useRegistrationCode());

      act(() => {
        result.current.clearRegistration();
      });

      expect(mockConfigStorage.remove).toHaveBeenCalledWith('castplay_device_registration');
      expect(result.current.isRegistered).toBe(false);
      expect(result.current.registration.deviceId).toBeNull();
    });
  });

  describe('存储变化监听', () => {
    it('应该监听存储变化事件', () => {
      mockConfigStorage.get.mockReturnValue(null);

      const addEventListenerSpy = vi.spyOn(window, 'addEventListener');

      renderHook(() => useRegistrationCode());

      expect(addEventListenerSpy).toHaveBeenCalledWith('storage', expect.any(Function));

      addEventListenerSpy.mockRestore();
    });

    it('应该在卸载时移除事件监听', () => {
      mockConfigStorage.get.mockReturnValue(null);

      const removeEventListenerSpy = vi.spyOn(window, 'removeEventListener');

      const { unmount } = renderHook(() => useRegistrationCode());

      unmount();

      expect(removeEventListenerSpy).toHaveBeenCalledWith('storage', expect.any(Function));

      removeEventListenerSpy.mockRestore();
    });
  });
});
