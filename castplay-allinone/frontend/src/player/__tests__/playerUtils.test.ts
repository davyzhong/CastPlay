/**
 * 播放端工具函数和 Hooks 单元测试
 */
import { DeviceIdManager } from '../utils/deviceId';
import { renderHook, waitFor } from '@testing-library/react';
import { useHeartbeat, HEARTBEAT_INTERVAL_MS, HEARTBEAT_TIMEOUT_MS } from '../hooks/useHeartbeat';
import { usePlaylistVersionCheck } from '../hooks/usePlaylistVersionCheck';
import axios from 'axios';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock localStorage
const localStorageMock = (() => {
    let store: Record<string, string> = {};
    return {
        getItem: jest.fn((key: string) => store[key] || null),
        setItem: jest.fn((key: string, value: string) => {
            store[key] = value;
        }),
        clear: jest.fn(() => {
            store = {};
        }),
        removeItem: jest.fn((key: string) => {
            delete store[key];
        })
    };
})();

Object.defineProperty(window, 'localStorage', {
    value: localStorageMock
});

// Mock crypto.randomUUID
const mockUUID = '12345678-1234-4123-8234-123456789abc';
const mockRandomUUID = jest.fn(() => mockUUID);
Object.defineProperty(global.crypto, 'randomUUID', {
    value: mockRandomUUID,
    writable: true,
    configurable: true
});

// Mock sendBeacon
const mockSendBeacon = jest.fn(() => true);
Object.defineProperty(navigator, 'sendBeacon', {
    value: mockSendBeacon,
    writable: true,
    configurable: true
});

// Mock setInterval and clearTimeout for faster tests
jest.useFakeTimers();

describe('DeviceIdManager', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        localStorageMock.clear();
    });

    describe('getDeviceId', () => {
        it('应该生成新的 UUID 当 localStorage 为空时', async () => {
            const deviceId = await DeviceIdManager.getDeviceId();

            expect(deviceId).toBe(mockUUID);
            expect(localStorageMock.setItem).toHaveBeenCalledWith(
                'castplay_device_id',
                mockUUID
            );
        });

        it('应该从 localStorage 读取已存在的设备 ID', async () => {
            const existingId = 'existing-device-id';
            localStorageMock.getItem.mockReturnValue(existingId);

            const deviceId = await DeviceIdManager.getDeviceId();

            expect(deviceId).toBe(existingId);
            expect(localStorageMock.setItem).not.toHaveBeenCalled();
        });

        it('应该缓存设备 ID 避免重复生成', async () => {
            await DeviceIdManager.getDeviceId();
            await DeviceIdManager.getDeviceId();
            await DeviceIdManager.getDeviceId();

            expect(localStorageMock.setItem).toHaveBeenCalledTimes(1);
            expect(mockRandomUUID).toHaveBeenCalledTimes(1);
        });

        it('应该在内存中缓存实例', async () => {
            const firstCall = await DeviceIdManager.getDeviceId();
            const secondCall = await DeviceIdManager.getDeviceId();

            expect(firstCall).toBe(secondCall);
        });
    });

    describe('generateUUIDv4', () => {
        it('应该使用 crypto.randomUUID() 当可用时', () => {
            // @ts-ignore - 访问私有方法进行测试
            const uuid = DeviceIdManager.generateUUIDv4();
            expect(uuid).toBe(mockUUID);
            expect(mockRandomUUID).toHaveBeenCalled();
        });

        it('应该降级到手动生成 UUID 当 crypto 不可用时', () => {
            // 临时禁用 crypto
            const originalCrypto = global.crypto;
            // @ts-ignore
            global.crypto = undefined;

            // @ts-ignore - 访问私有方法
            const uuid = DeviceIdManager.generateUUIDv4();

            // 验证 UUID 格式
            expect(uuid).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i);

            // 恢复 crypto
            global.crypto = originalCrypto;
        });
    });

    describe('reset', () => {
        it('应该生成新的设备 ID 并覆盖旧的', async () => {
            const oldId = await DeviceIdManager.getDeviceId();
            const newId = DeviceIdManager.reset();

            expect(oldId).not.toBe(newId);
            expect(localStorageMock.setItem).toHaveBeenCalledTimes(2);
        });

        it('应该更新内存中的实例', () => {
            const newId = DeviceIdManager.reset();

            expect(DeviceIdManager['instance']).toBe(newId);
        });
    });
});

describe('useHeartbeat', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        mockedAxios.post.mockResolvedValue({ data: { acknowledged: true } });
    });

    afterEach(() => {
        jest.clearAllTimers();
    });

    it('应该在有 deviceId 时立即发送心跳', () => {
        const deviceId = 'test-device';

        renderHook(() =>
            useHeartbeat(deviceId, 1, 100, 'playing')
        );

        expect(mockedAxios.post).toHaveBeenCalledTimes(1);
        expect(mockedAxios.post).toHaveBeenCalledWith(
            '/api/player/heartbeat',
            {
                device_id: deviceId,
                current_playlist_id: 1,
                last_media_id: 100,
                status: 'playing'
            },
            { timeout: HEARTBEAT_TIMEOUT_MS }
        );
    });

    it('应该在无 deviceId 时不发送心跳', () => {
        renderHook(() =>
            useHeartbeat(null, 1, 100, 'playing')
        );

        expect(mockedAxios.post).not.toHaveBeenCalled();
    });

    it('应该每 2 小时自动发送心跳', () => {
        const deviceId = 'test-device';

        renderHook(() =>
            useHeartbeat(deviceId, 1, 100, 'playing')
        );

        // 快进 2 小时
        jest.advanceTimersByTime(HEARTBEAT_INTERVAL_MS);

        // 初始 1 次 + 定时 1 次 = 2 次
        expect(mockedAxios.post).toHaveBeenCalledTimes(2);
    });

    it('应该在依赖变化时重新创建 sendHeartbeat 函数', () => {
        const deviceId = 'test-device';

        const { rerender } = renderHook(
            ({ playlistId, mediaId, status }) =>
                useHeartbeat(deviceId, playlistId, mediaId, status),
            {
                initialProps: { playlistId: 1, mediaId: 100, status: 'playing' }
            }
        );

        // 更新依赖
        rerender({ playlistId: 2, mediaId: 200, status: 'paused' });

        // 清除定时器后重新计时
        jest.advanceTimersByTime(HEARTBEAT_INTERVAL_MS);

        // 验证新的参数被使用
        expect(mockedAxios.post).toHaveBeenCalledWith(
            '/api/player/heartbeat',
            expect.objectContaining({
                current_playlist_id: 2,
                last_media_id: 200,
                status: 'paused'
            }),
            expect.anything()
        );
    });

    it('应该在页面关闭前使用 sendBeacon 发送离线心跳', () => {
        const deviceId = 'test-device';

        renderHook(() =>
            useHeartbeat(deviceId, 1, 100, 'playing')
        );

        // 模拟 beforeunload 事件
        const event = new Event('beforeunload');
        window.dispatchEvent(event);

        expect(mockSendBeacon).toHaveBeenCalledWith(
            '/api/player/heartbeat',
            expect.any(Blob)
        );
    });

    it('应该在心跳失败时静默处理不抛出异常', async () => {
        mockedAxios.post.mockRejectedValue(new Error('Network error'));
        const consoleSpy = jest.spyOn(console, 'debug').mockImplementation();

        const deviceId = 'test-device';

        expect(() => {
            renderHook(() =>
                useHeartbeat(deviceId, 1, 100, 'playing')
            );
        }).not.toThrow();

        // 等待异步操作完成
        await waitFor(() => {
            expect(consoleSpy).toHaveBeenCalledWith(
                'Heartbeat failed (offline):',
                expect.any(Error)
            );
        });

        consoleSpy.mockRestore();
    });
});

describe('usePlaylistVersionCheck', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        mockedAxios.post.mockResolvedValue({ data: { needs_update: false } });
    });

    afterEach(() => {
        jest.clearAllTimers();
    });

    it('应该在启动时立即检查版本', () => {
        const deviceId = 'test-device';
        const playlistId = 1;
        const version = '2026-01-01T00:00:00Z';

        renderHook(() =>
            usePlaylistVersionCheck(deviceId, playlistId, version)
        );

        expect(mockedAxios.post).toHaveBeenCalledTimes(1);
        expect(mockedAxios.post).toHaveBeenCalledWith(
            `/api/player/playlist/${playlistId}/check`,
            { version },
            expect.anything()
        );
    });

    it('应该在无 deviceId 时不检查版本', () => {
        renderHook(() =>
            usePlaylistVersionCheck(null, 1, '2026-01-01T00:00:00Z')
        );

        expect(mockedAxios.post).not.toHaveBeenCalled();
    });

    it('应该在无 playlistId 时不检查版本', () => {
        renderHook(() =>
            usePlaylistVersionCheck('test-device', null, '2026-01-01T00:00:00Z')
        );

        expect(mockedAxios.post).not.toHaveBeenCalled();
    });

    it('应该每 30 分钟轮询检查版本', () => {
        const deviceId = 'test-device';
        const playlistId = 1;
        const version = '2026-01-01T00:00:00Z';

        renderHook(() =>
            usePlaylistVersionCheck(deviceId, playlistId, version)
        );

        // 快进 30 分钟
        jest.advanceTimersByTime(30 * 60 * 1000);

        // 初始 1 次 + 定时 1 次 = 2 次
        expect(mockedAxios.post).toHaveBeenCalledTimes(2);
    });

    it('应该在需要更新时返回 needsUpdate=true', async () => {
        mockedAxios.post.mockResolvedValue({ data: { needs_update: true } });

        const { result } = renderHook(() =>
            usePlaylistVersionCheck('test-device', 1, 'old-version')
        );

        // 等待异步更新
        await waitFor(() => {
            expect(result.current.needsUpdate).toBe(true);
        });
    });

    it('应该在不需要更新时返回 needsUpdate=false', async () => {
        mockedAxios.post.mockResolvedValue({ data: { needs_update: false } });

        const { result } = renderHook(() =>
            usePlaylistVersionCheck('test-device', 1, 'current-version')
        );

        // 等待异步更新
        await waitFor(() => {
            expect(result.current.needsUpdate).toBe(false);
        });
    });

    it('应该在版本检查失败时静默处理', async () => {
        mockedAxios.post.mockRejectedValue(new Error('Network error'));
        const consoleSpy = jest.spyOn(console, 'debug').mockImplementation();

        expect(() => {
            renderHook(() =>
                usePlaylistVersionCheck('test-device', 1, 'version')
            );
        }).not.toThrow();

        await waitFor(() => {
            expect(consoleSpy).toHaveBeenCalledWith(
                'Version check failed (offline):',
                expect.any(Error)
            );
        });

        consoleSpy.mockRestore();
    });
});

describe('常量导出', () => {
    it('应该导出心跳间隔常量', () => {
        expect(HEARTBEAT_INTERVAL_MS).toBe(2 * 60 * 60 * 1000); // 2 小时
    });

    it('应该导出心跳超时常量', () => {
        expect(HEARTBEAT_TIMEOUT_MS).toBe(5000); // 5 秒
    });
});
