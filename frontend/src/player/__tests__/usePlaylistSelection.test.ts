/**
 * 播放列表选择 Hook 单元测试
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';

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

// Mock playerApi
vi.mock('../../utils/apiClient', () => ({
  playerApi: {
    get: vi.fn(),
  },
}));

// Mock configStorage
vi.mock('../services/ConfigStorage', () => ({
  configStorage: {
    get: vi.fn(),
    set: vi.fn(),
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

describe('usePlaylistSelection', () => {
  let usePlaylistSelection: typeof import('../hooks/usePlaylistSelection').usePlaylistSelection;
  let playerApi: typeof import('../../utils/apiClient').playerApi;
  let configStorage: typeof import('../services/ConfigStorage').configStorage;

  const mockPlaylists = [
    { id: 1, name: 'Playlist 1', media_count: 10, total_size_mb: 100, thumbnail_url: '/thumb1.jpg' },
    { id: 2, name: 'Playlist 2', media_count: 5, total_size_mb: 50, thumbnail_url: '/thumb2.jpg' },
    { id: 3, name: 'Playlist 3', media_count: 15, total_size_mb: 200, thumbnail_url: '/thumb3.jpg' },
  ];

  beforeEach(async () => {
    vi.clearAllMocks();
    localStorageMock.clear();

    // Reset modules
    vi.resetModules();

    // Import fresh modules
    const apiModule = await import('../../utils/apiClient');
    playerApi = apiModule.playerApi;

    const configStorageModule = await import('../services/ConfigStorage');
    configStorage = configStorageModule.configStorage;

    const hookModule = await import('../hooks/usePlaylistSelection');
    usePlaylistSelection = hookModule.usePlaylistSelection;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('初始化状态', () => {
    it('应该在无 deviceId 时返回空状态', () => {
      const { result } = renderHook(() => usePlaylistSelection(null));

      expect(result.current.availablePlaylists).toEqual([]);
      expect(result.current.selectedIds).toEqual([]);
      expect(result.current.isLoading).toBe(false);
    });

    it('应该从 localStorage 加载已保存的选择', () => {
      const savedSelection = {
        selectedIds: [1, 2],
        updatedAt: '2026-01-01T00:00:00Z',
        userModified: true,
      };
      localStorageMock.getItem.mockImplementation((key: string) => {
        if (key === 'castplay_playlist_selection') {
          return JSON.stringify(savedSelection);
        }
        return null;
      });

      const { result } = renderHook(() => usePlaylistSelection('device-123'));

      expect(result.current.selectedIds).toEqual([1, 2]);
    });

    it('应该在首次加载时标记为未完成', () => {
      localStorageMock.getItem.mockReturnValue(null);

      const { result } = renderHook(() => usePlaylistSelection('device-123'));

      expect(result.current.isSelectionComplete).toBe(false);
    });

    it('应该在设置完成后标记为完成', () => {
      localStorageMock.getItem.mockImplementation((key: string) => {
        if (key === 'castplay_setup_completed') {
          return 'true';
        }
        return null;
      });

      const { result } = renderHook(() => usePlaylistSelection('device-123'));

      expect(result.current.isSelectionComplete).toBe(true);
    });
  });

  describe('loadPlaylists', () => {
    it('应该从 API 加载播放列表', async () => {
      (playerApi.get as any).mockResolvedValue({
        playlists: mockPlaylists,
      });
      localStorageMock.getItem.mockReturnValue(null);

      const { result } = renderHook(() => usePlaylistSelection('device-123'));

      await act(async () => {
        await result.current.loadPlaylists();
      });

      expect(result.current.availablePlaylists).toEqual(mockPlaylists);
      expect(result.current.isLoading).toBe(false);
    });

    it('应该在首次加载时默认全选', async () => {
      (playerApi.get as any).mockResolvedValue({
        playlists: mockPlaylists,
      });
      localStorageMock.getItem.mockReturnValue(null);

      const { result } = renderHook(() => usePlaylistSelection('device-123'));

      await act(async () => {
        await result.current.loadPlaylists();
      });

      expect(result.current.selectedIds).toEqual([1, 2, 3]);
    });

    it('应该在加载失败时设置错误', async () => {
      (playerApi.get as any).mockRejectedValue(new Error('Network error'));
      localStorageMock.getItem.mockReturnValue(null);

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation();

      const { result } = renderHook(() => usePlaylistSelection('device-123'));

      await act(async () => {
        await result.current.loadPlaylists();
      });

      expect(result.current.error).toBe('加载播放列表失败');
      expect(consoleSpy).toHaveBeenCalled();

      consoleSpy.mockRestore();
    });

    it('应该在无 deviceId 时不加载', async () => {
      const { result } = renderHook(() => usePlaylistSelection(null));

      await act(async () => {
        await result.current.loadPlaylists();
      });

      expect(playerApi.get).not.toHaveBeenCalled();
    });
  });

  describe('toggleSelection', () => {
    it('应该切换播放列表选择状态', async () => {
      (playerApi.get as any).mockResolvedValue({
        playlists: mockPlaylists,
      });
      localStorageMock.getItem.mockReturnValue(null);

      const { result } = renderHook(() => usePlaylistSelection('device-123'));

      await act(async () => {
        await result.current.loadPlaylists();
      });

      // 初始全选 [1, 2, 3]
      expect(result.current.selectedIds).toEqual([1, 2, 3]);

      // 取消选择 2
      act(() => {
        result.current.toggleSelection(2);
      });

      expect(result.current.selectedIds).toEqual([1, 3]);

      // 重新选择 2
      act(() => {
        result.current.toggleSelection(2);
      });

      expect(result.current.selectedIds).toEqual([1, 3, 2]);
    });

    it('应该阻止取消最后一个播放列表', async () => {
      (playerApi.get as any).mockResolvedValue({
        playlists: mockPlaylists,
      });
      localStorageMock.getItem.mockReturnValue(null);

      const consoleSpy = vi.spyOn(console, 'log').mockImplementation();

      const { result } = renderHook(() => usePlaylistSelection('device-123'));

      await act(async () => {
        await result.current.loadPlaylists();
      });

      // 取消 2 和 3
      act(() => {
        result.current.toggleSelection(2);
        result.current.toggleSelection(3);
      });

      expect(result.current.selectedIds).toEqual([1]);

      // 尝试取消最后一个
      act(() => {
        result.current.toggleSelection(1);
      });

      // 应该仍然是 [1]
      expect(result.current.selectedIds).toEqual([1]);
      expect(consoleSpy).toHaveBeenCalledWith(
        '[usePlaylistSelection] Cannot deselect last playlist'
      );

      consoleSpy.mockRestore();
    });
  });

  describe('selectAll', () => {
    it('应该选择所有播放列表', async () => {
      (playerApi.get as any).mockResolvedValue({
        playlists: mockPlaylists,
      });
      localStorageMock.getItem.mockReturnValue(null);

      const consoleSpy = vi.spyOn(console, 'log').mockImplementation();

      const { result } = renderHook(() => usePlaylistSelection('device-123'));

      await act(async () => {
        await result.current.loadPlaylists();
      });

      // 先取消一些
      act(() => {
        result.current.toggleSelection(2);
        result.current.toggleSelection(3);
      });

      expect(result.current.selectedIds).toEqual([1]);

      // 全选
      act(() => {
        result.current.selectAll();
      });

      expect(result.current.selectedIds).toEqual([1, 2, 3]);

      consoleSpy.mockRestore();
    });
  });

  describe('deselectAll', () => {
    it('应该只保留第一个播放列表', async () => {
      (playerApi.get as any).mockResolvedValue({
        playlists: mockPlaylists,
      });
      localStorageMock.getItem.mockReturnValue(null);

      const consoleSpy = vi.spyOn(console, 'log').mockImplementation();

      const { result } = renderHook(() => usePlaylistSelection('device-123'));

      await act(async () => {
        await result.current.loadPlaylists();
      });

      // 取消全选（保留第一个）
      act(() => {
        result.current.deselectAll();
      });

      expect(result.current.selectedIds).toEqual([1]);

      consoleSpy.mockRestore();
    });
  });

  describe('confirmSelection', () => {
    it('应该保存选择并标记完成', async () => {
      (playerApi.get as any).mockResolvedValue({
        playlists: mockPlaylists,
      });
      localStorageMock.getItem.mockReturnValue(null);

      const consoleSpy = vi.spyOn(console, 'log').mockImplementation();

      const { result } = renderHook(() => usePlaylistSelection('device-123'));

      await act(async () => {
        await result.current.loadPlaylists();
      });

      // 先切换选择
      act(() => {
        result.current.toggleSelection(3); // 取消选择 3，只选择 1 和 2
      });

      // 确保状态更新后再确认选择
      act(() => {
        result.current.confirmSelection();
      });

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'castplay_playlist_selection',
        expect.stringContaining('"selectedIds":[1,2]')
      );
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'castplay_setup_completed',
        'true'
      );
      expect(result.current.isSelectionComplete).toBe(true);

      consoleSpy.mockRestore();
    });

    it('应该在选择的播放列表为空时显示错误', () => {
      localStorageMock.getItem.mockReturnValue(null);

      const { result } = renderHook(() => usePlaylistSelection('device-123'));

      act(() => {
        result.current.confirmSelection();
      });

      expect(result.current.error).toBe('请至少选择一个播放列表');
    });

    it('应该同时保存到 configStorage', async () => {
      (playerApi.get as any).mockResolvedValue({
        playlists: mockPlaylists,
      });
      localStorageMock.getItem.mockReturnValue(null);

      const consoleSpy = vi.spyOn(console, 'log').mockImplementation();

      const { result } = renderHook(() => usePlaylistSelection('device-123'));

      await act(async () => {
        await result.current.loadPlaylists();
      });

      act(() => {
        result.current.confirmSelection();
      });

      expect(configStorage.set).toHaveBeenCalledWith(
        'castplay_playlist_selection',
        expect.objectContaining({
          selectedIds: [1, 2, 3],
          userModified: true,
        })
      );

      consoleSpy.mockRestore();
    });
  });

  describe('skipSelection', () => {
    it('应该选择全部并标记完成', async () => {
      (playerApi.get as any).mockResolvedValue({
        playlists: mockPlaylists,
      });
      localStorageMock.getItem.mockReturnValue(null);

      const consoleSpy = vi.spyOn(console, 'log').mockImplementation();

      const { result } = renderHook(() => usePlaylistSelection('device-123'));

      await act(async () => {
        await result.current.loadPlaylists();
      });

      act(() => {
        result.current.skipSelection();
      });

      expect(result.current.selectedIds).toEqual([1, 2, 3]);
      expect(result.current.isSelectionComplete).toBe(true);

      // 验证 userModified 为 false
      const savedCall = (localStorageMock.setItem as any).mock.calls.find(
        (call: any[]) => call[0] === 'castplay_playlist_selection'
      );
      const savedData = JSON.parse(savedCall[1]);
      expect(savedData.userModified).toBe(false);

      consoleSpy.mockRestore();
    });
  });

  describe('selectedPlaylists', () => {
    it('应该返回选中的播放列表详情', async () => {
      (playerApi.get as any).mockResolvedValue({
        playlists: mockPlaylists,
      });
      localStorageMock.getItem.mockReturnValue(null);

      const { result } = renderHook(() => usePlaylistSelection('device-123'));

      await act(async () => {
        await result.current.loadPlaylists();
      });

      // 取消选择第三个
      act(() => {
        result.current.toggleSelection(3);
      });

      const selected = result.current.selectedPlaylists;

      expect(selected).toHaveLength(2);
      expect(selected.map((p) => p.id)).toEqual([1, 2]);
    });
  });

  describe('自动加载', () => {
    it('应该在有 deviceId 且未完成时自动加载', async () => {
      (playerApi.get as any).mockResolvedValue({
        playlists: mockPlaylists,
      });
      localStorageMock.getItem.mockReturnValue(null);

      renderHook(() => usePlaylistSelection('device-123'));

      await waitFor(() => {
        expect(playerApi.get).toHaveBeenCalled();
      });
    });

    it('应该在已完成选择时不自动加载', async () => {
      (playerApi.get as any).mockResolvedValue({
        playlists: mockPlaylists,
      });
      localStorageMock.getItem.mockImplementation((key: string) => {
        if (key === 'castplay_setup_completed') {
          return 'true';
        }
        return null;
      });

      renderHook(() => usePlaylistSelection('device-123'));

      // 等待一段时间确保没有调用
      await new Promise((resolve) => setTimeout(resolve, 100));

      expect(playerApi.get).not.toHaveBeenCalled();
    });
  });
});
