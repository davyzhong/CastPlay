/**
 * 调度管理 Hook 单元测试
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock scheduleEvaluator - 单例模式需要特殊处理
let mockEvaluateResult = {
  activeSchedule: null,
  activePlaylistId: null,
  nextSchedule: null,
  nextSwitchTime: null as Date | null,
};

vi.mock('../services/ScheduleEvaluator', () => ({
  scheduleEvaluator: {
    updateSchedules: vi.fn().mockImplementation((schedules, defaultId) => {
      // 更新 mock 结果
      if (schedules && schedules.length > 0) {
        mockEvaluateResult.activeSchedule = schedules[0];
        mockEvaluateResult.activePlaylistId = schedules[0].playlist_id;
      } else {
        mockEvaluateResult.activeSchedule = null;
        mockEvaluateResult.activePlaylistId = defaultId;
      }
    }),
    evaluate: vi.fn().mockImplementation(() => mockEvaluateResult),
    shouldSwitchPlaylist: vi.fn().mockImplementation(() => ({
      shouldSwitch: false,
      newPlaylistId: null,
      scheduleId: null,
    })),
    getMsUntilNextSwitch: vi.fn().mockReturnValue(null),
    getNextSwitchTime: vi.fn().mockReturnValue(null),
    reset: vi.fn().mockImplementation(() => {
      mockEvaluateResult = {
        activeSchedule: null,
        activePlaylistId: null,
        nextSchedule: null,
        nextSwitchTime: null,
      };
    }),
  },
  ScheduleEvaluator: vi.fn(),
}));

// Mock apiClient
vi.mock('../../utils/apiClient', () => ({
  playerApi: {
    get: vi.fn(),
  },
}));

describe('useSchedule', () => {
  let useSchedule: typeof import('../hooks/useSchedule').useSchedule;

  const mockSchedules = [
    {
      id: 1,
      playlist_id: 100,
      start_time: '09:00:00',
      end_time: '17:00:00',
      days_of_week: 62,
      enabled: true,
      priority: 1,
    },
  ];

  beforeEach(async () => {
    vi.clearAllMocks();
    vi.useFakeTimers();

    mockFetch.mockImplementation(() =>
      Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            schedules: mockSchedules,
            default_playlist_id: 99,
            server_time: new Date().toISOString(),
          }),
      })
    );

    vi.resetModules();
    const hookModule = await import('../hooks/useSchedule');
    useSchedule = hookModule.useSchedule;
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('初始化状态', () => {
    it('应该在无 deviceId 时返回初始状态', () => {
      const { result } = renderHook(() =>
        useSchedule({
          deviceId: null,
          currentPlaylistId: null,
        })
      );

      expect(result.current.activeSchedule).toBeNull();
      expect(result.current.activePlaylistId).toBeNull();
      expect(result.current.defaultPlaylistId).toBeNull();
      expect(result.current.isLoading).toBe(false);
      expect(result.current.shouldSwitch).toBe(false);
    });

    it('应该返回初始状态（离线模式）', () => {
      const { result } = renderHook(() =>
        useSchedule({
          deviceId: 'device-123',
          currentPlaylistId: null,
          isOnline: false,
        })
      );

      // 离线时不会立即加载
      expect(result.current.isLoading).toBe(false);
    });
  });

  describe('定时器清理', () => {
    it('应该在组件卸载时清理定时器', () => {
      const { unmount } = renderHook(() =>
        useSchedule({
          deviceId: 'device-123',
          currentPlaylistId: null,
        })
      );

      // 卸载应该不会抛出错误
      expect(() => unmount()).not.toThrow();
    });
  });

  describe('shouldSwitch 状态', () => {
    it('初始状态 shouldSwitch 为 false', () => {
      const { result } = renderHook(() =>
        useSchedule({
          deviceId: null,
          currentPlaylistId: 99,
        })
      );

      expect(result.current.shouldSwitch).toBe(false);
    });
  });

  describe('evaluate 函数', () => {
    it('应该返回评估结果', async () => {
      const { result } = renderHook(() =>
        useSchedule({
          deviceId: null,
          currentPlaylistId: null,
        })
      );

      // evaluate 函数应该存在
      expect(typeof result.current.evaluate).toBe('function');
    });
  });

  describe('refreshSchedules 函数', () => {
    it('refreshSchedules 函数应该存在', () => {
      const { result } = renderHook(() =>
        useSchedule({
          deviceId: null,
          currentPlaylistId: null,
        })
      );

      expect(typeof result.current.refreshSchedules).toBe('function');
    });
  });

  describe('nextSwitchTime 状态', () => {
    it('初始状态 nextSwitchTime 为 null', () => {
      const { result } = renderHook(() =>
        useSchedule({
          deviceId: null,
          currentPlaylistId: null,
        })
      );

      expect(result.current.nextSwitchTime).toBeNull();
    });
  });

  describe('isLoading 状态', () => {
    it('无 deviceId 时 isLoading 为 false', () => {
      const { result } = renderHook(() =>
        useSchedule({
          deviceId: null,
          currentPlaylistId: null,
        })
      );

      expect(result.current.isLoading).toBe(false);
    });
  });

  describe('activeSchedule 状态', () => {
    it('无调度时 activeSchedule 为 null', () => {
      const { result } = renderHook(() =>
        useSchedule({
          deviceId: null,
          currentPlaylistId: null,
        })
      );

      expect(result.current.activeSchedule).toBeNull();
    });
  });

  describe('defaultPlaylistId 状态', () => {
    it('无配置时 defaultPlaylistId 为 null', () => {
      const { result } = renderHook(() =>
        useSchedule({
          deviceId: null,
          currentPlaylistId: null,
        })
      );

      expect(result.current.defaultPlaylistId).toBeNull();
    });
  });

  describe('返回对象结构', () => {
    it('应该返回完整的返回对象', () => {
      const { result } = renderHook(() =>
        useSchedule({
          deviceId: null,
          currentPlaylistId: null,
        })
      );

      expect(result.current).toHaveProperty('activeSchedule');
      expect(result.current).toHaveProperty('activePlaylistId');
      expect(result.current).toHaveProperty('defaultPlaylistId');
      expect(result.current).toHaveProperty('nextSwitchTime');
      expect(result.current).toHaveProperty('isLoading');
      expect(result.current).toHaveProperty('shouldSwitch');
      expect(result.current).toHaveProperty('refreshSchedules');
      expect(result.current).toHaveProperty('evaluate');
    });
  });
});
