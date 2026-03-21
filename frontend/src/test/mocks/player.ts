/**
 * Player API Mock
 */
import { vi } from 'vitest'

// 模拟设备数据
export const mockDevices = [
  {
    id: 1,
    device_id: 'test-device-001',
    device_name: '测试设备1',
    timezone: 'Asia/Shanghai',
    status: 'online',
    last_online: '2026-03-05T10:00:00',
  },
  {
    id: 2,
    device_id: 'test-device-002',
    device_name: '测试设备2',
    timezone: 'Asia/Shanghai',
    status: 'offline',
    last_online: '2026-03-05T09:00:00',
  },
]

// 模拟播放列表数据
export const mockPlaylists = [
  {
    id: 1,
    name: '测试播放列表1',
    updated_at: '2026-03-05T10:00:00',
    items: [
      {
        id: 1,
        media_id: 101,
        file_name: 'test-image.jpg',
        file_type: 'image',
        file_url: '/api/player/media/101/download',
        display_order: 1,
        display_duration: 10,
        file_size: 1024000,
        md5_hash: 'abc123',
      },
      {
        id: 2,
        media_id: 102,
        file_name: 'test-video.mp4',
        file_type: 'video',
        file_url: '/api/player/media/102/download',
        display_order: 2,
        display_duration: 30,
        file_size: 10240000,
        md5_hash: 'def456',
      },
    ],
  },
]

// 模拟初始化响应
export const mockInitResponse = {
  device: {
    id: 1,
    device_id: 'test-device-001',
    device_name: '测试设备',
    timezone: 'Asia/Shanghai',
    mac_address: 'AA:BB:CC:DD:EE:FF',
    ip_address: '192.168.1.100',
    registration_code: 'REG123456',
    playback_speed: 1,
  },
  playlists: mockPlaylists,
  schedule: {
    power_on_time: '09:00',
    power_off_time: '18:00',
    is_enabled: true,
    weekdays: [1, 2, 3, 4, 5],
    timezone: 'Asia/Shanghai',
  },
  websocket_url: 'ws://localhost:8000/ws/test-device-001',
}

// API 函数 Mock
export const registerDevice = vi.fn().mockResolvedValue({
  id: 1,
  device_id: 'new-test-device',
  device_name: '新测试设备',
})

export const playerInit = vi.fn().mockResolvedValue(mockInitResponse)

export const reportPlayerStatus = vi.fn().mockResolvedValue({
  message: 'Status reported successfully',
})

export const getDeviceList = vi.fn().mockResolvedValue({
  items: mockDevices,
  total: 2,
})

export const getAllPlaylists = vi.fn().mockResolvedValue({
  items: mockPlaylists.map(p => ({
    id: p.id,
    name: p.name,
    updated_at: p.updated_at,
  })),
  total: 1,
})

export const getPlaylistDetail = vi.fn().mockImplementation((id: number) => {
  const playlist = mockPlaylists.find(p => p.id === id)
  return Promise.resolve(playlist || { items: [] })
})

export const checkPlaylistVersion = vi.fn().mockResolvedValue({
  needs_update: false,
  server_version: '2026-03-05T10:00:00',
  local_version: '2026-03-05T10:00:00',
})

export const getMediaDownloadUrl = vi.fn().mockImplementation((mediaId: number) => {
  return `/api/player/media/${mediaId}/download`
})

export const getConvertedMediaUrl = vi.fn().mockImplementation((mediaId: number) => {
  return `/api/player/media/${mediaId}/converted`
})
