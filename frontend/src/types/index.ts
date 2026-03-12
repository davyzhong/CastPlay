/**
 * 类型定义
 */

// 用户类型
export interface User {
  id: number
  username: string
  email?: string
  full_name?: string
  is_active: boolean
  is_superuser: boolean
  created_at: string
}

// 设备类型
export interface Device {
  id: number
  device_id: string
  device_name: string
  timezone: string
  last_online?: string
  status: 'online' | 'offline'
  // 新增字段
  mac_address?: string
  ip_address?: string
  registration_code?: string
  is_disabled?: boolean
  created_at: string
  updated_at: string
}

export interface DeviceSchedule {
  id: number
  device_id: number
  power_on_time: string
  power_off_time: string
  is_enabled: boolean
  weekdays: number[]
  created_at: string
  updated_at: string
}

// 媒体文件类型
export interface MediaFile {
  id: number
  file_name: string
  file_type: 'image' | 'video' | 'ppt'
  file_path: string
  file_size?: number
  converted_path?: string
  thumbnail_path?: string
  md5_hash?: string
  status: 'ready' | 'processing' | 'failed'
  duration?: number
  created_at: string
  updated_at?: string
}

// 播放列表类型
export interface Playlist {
  id: number
  name: string
  description?: string
  is_system?: boolean
  item_count: number
  device_count: number
  devices?: DeviceAssignment[]
  created_at: string
  updated_at: string
}

export interface PlaylistItem {
  id: number
  media_id: number
  file_name: string
  file_type: string
  display_order: number
  display_duration: number
  created_at: string
}

export interface PlaylistDetail {
  id: number
  name: string
  description?: string
  is_system?: boolean
  items: PlaylistItem[]
  devices: DeviceAssignment[]
  created_at: string
  updated_at: string
}

export interface DeviceAssignment {
  id: number
  device_id: number
  device_name: string
  device_status: string
  is_active: boolean
  assigned_at: string
}

// 设备播放列表关联
export interface DevicePlaylist {
  assignment_id: number
  playlist_id: number
  playlist_name: string
  is_active: boolean
  item_count: number
  assigned_at: string
}

// API 响应类型
export interface ApiResponse<T = any> {
  message?: string
  data?: T
  error?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
  pages: number
}

// WebSocket 事件类型
export interface WebSocketMessage {
  event: 'playlist_update' | 'schedule_update' | 'force_sync' | 'reboot' | 'heartbeat_ack'
  device_id?: number
  action?: string
  timestamp?: string
}
