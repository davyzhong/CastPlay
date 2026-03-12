/**
 * 播放器类型定义
 */

// Android Bridge 接口
export interface AndroidBridge {
  getMacAddress(): string;
  getIPAddress(): string;
  getDeviceId(): string;
  getRegistrationCode(): string;
  downloadMedia(url: string, mediaId: string): void;
  getDownloadProgress(mediaId: string): number;
  isMediaCached(mediaId: string): boolean;
  getCachedMediaPath(mediaId: string): string;
  getLocalTimezone(): string;
  showToast(message: string): void;
}

// 扩展 Window 接口
declare global {
  interface Window {
    AndroidBridge?: AndroidBridge;
  }
}

// 设备信息
export interface PlayerDeviceInfo {
  id: number;
  device_id: string;
  device_name: string;
  timezone: string;
  mac_address?: string;
  ip_address?: string;
  registration_code?: string;
  playback_speed: number;
}

// 播放列表项（增强版，支持嵌套 media 对象）
export interface PlayerPlaylistItem {
  id: number;
  media_id: number;
  file_name: string;
  file_type: 'image' | 'video' | 'ppt';
  file_url: string;
  display_order: number;
  display_duration: number;
  file_size?: number;
  md5_hash?: string;
  // 嵌套 media 对象（来自详情 API）
  media?: {
    id: number;
    file_name: string;
    file_type: string;
    file_url: string;
    file_size: number;
    md5_hash?: string;
  };
}

// 播放列表
export interface PlayerPlaylist {
  id: number;
  name: string;
  version: string;
  is_system?: boolean;
  is_active?: boolean;
  description?: string;
  item_count?: number;
  items: PlayerPlaylistItem[];
}

// 定时配置
export interface PlayerSchedule {
  power_on_time: string | null;
  power_off_time: string | null;
  is_enabled: boolean;
  weekdays: number[];
  timezone: string;
}

// 初始化响应
export interface PlayerInitResponse {
  device: PlayerDeviceInfo;
  playlists: PlayerPlaylist[];
  schedule: PlayerSchedule | null;
  websocket_url: string;
}

// 缓存状态
export type CacheStatus = 'pending' | 'downloading' | 'completed' | 'failed';

// 缓存媒体信息
export interface CachedMediaInfo {
  media_id: number;
  local_path: string;
  status: CacheStatus;
  progress: number;
}

// 播放器状态
export interface PlayerState {
  isPlaying: boolean;
  currentIndex: number;
  playbackSpeed: number;
  loopEnabled: boolean;
  isOnline: boolean;
  currentPlaylist: PlayerPlaylist | null;
}

// WebSocket 消息
export interface PlayerWsMessage {
  event: 'playlist_update' | 'schedule_update' | 'config_update' | 'force_sync';
  device_id?: number;
  playlist_id?: number;
  data?: unknown;
  timestamp?: string;
}
