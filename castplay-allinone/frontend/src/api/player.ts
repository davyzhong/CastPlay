/**
 * 播放端 API（供测试页面使用）
 * 这些 API 不需要认证，模拟 Android 播放端调用
 */
import axios from 'axios';

// 通用 axios 实例（不需要认证拦截器）
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 播放端专用 axios 实例
const playerApi = axios.create({
  baseURL: '/api/player',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface DeviceInfo {
  id: number;
  device_id: string;
  device_name: string;
  timezone: string;
  registration_code?: string;
}

export interface PlaylistItem {
  id: number;
  media_id: number;
  file_name: string;
  file_type: string;
  file_url: string;
  display_order: number;
  display_duration: number;
  file_size: number;
  md5_hash: string;
}

export interface PlayerPlaylist {
  id: number;
  name: string;
  version: string;
  is_system?: boolean;
  items: PlaylistItem[];
}

export interface DeviceSchedule {
  power_on_time: string | null;
  power_off_time: string | null;
  is_enabled: boolean;
  weekdays: number[];
  timezone: string;
}

export interface PlayerInitResponse {
  device: DeviceInfo;
  playlists: PlayerPlaylist[];
  schedule: DeviceSchedule | null;
  websocket_url: string;
}

// 设备注册（使用 devices API）
export const registerDevice = async (deviceId: string, deviceType: string = 'web_browser') => {
  const response = await api.post('/devices/register', {
    device_id: deviceId,
    device_name: 'Default Device', // 让后端根据 device_type 生成正确的名称
    device_type: deviceType,
  });
  return response.data;
};

export interface DeviceRegistrationResponse {
  id: number;
  device_id: string;
  device_name: string;
  registration_code: string;
  timezone: string;
  status: string;
  last_online: string;
}

// 播放端初始化
export const playerInit = async (deviceId: string): Promise<PlayerInitResponse> => {
  const response = await playerApi.post('/init', { device_id: deviceId });
  return response.data;
};

// 检查播放列表版本
export const checkPlaylistVersion = async (playlistId: number, version: string) => {
  const response = await playerApi.post(`/playlist/${playlistId}/check`, { version });
  return response.data;
};

// 获取媒体下载 URL
export const getMediaDownloadUrl = (mediaId: number) => {
  return `/api/player/media/${mediaId}/download`;
};

// 获取转换后的媒体 URL（PPT）
export const getConvertedMediaUrl = (mediaId: number) => {
  return `/api/player/media/${mediaId}/converted`;
};

// 上报播放状态
export const reportPlayerStatus = async (deviceId: string, status: string) => {
  const response = await playerApi.post('/status', {
    device_id: deviceId,
    player_status: status,
  });
  return response.data;
};

// 获取设备列表（用于选择设备）
export const getDeviceList = async () => {
  const response = await api.get('/devices/', { params: { limit: 100 } });
  return response.data;
};

// 获取所有播放列表（用于测试，从管理 API 获取）
export const getAllPlaylists = async () => {
  const response = await api.get('/playlists/', { params: { limit: 100 } });
  return response.data;
};

// 获取播放列表详情（包含媒体项）
export const getPlaylistDetail = async (playlistId: number) => {
  const response = await api.get(`/playlists/${playlistId}`);
  return response.data;
};
