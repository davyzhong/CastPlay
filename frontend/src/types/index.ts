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
  slide_duration?: number
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
export interface ApiResponse<T = unknown> {
  message?: string
  data?: T
  error?: string
}

// 登录响应类型
export interface LoginResponse {
  access_token: string
  token_type: string
  user?: User
}

// 错误响应类型
export interface ErrorResponse {
  detail: string | { msg: string; type: string; loc: (string | number)[] }[]
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

// 播放列表调度类型
export interface PlaylistSchedule {
  id: number
  device_id: number
  playlist_id: number
  playlist_name?: string
  start_time: string  // HH:MM:SS
  end_time: string    // HH:MM:SS
  days_of_week: number  // 位掩码 1-127
  days_display: string[]  // ["Mon", "Tue", ...]
  enabled: boolean
  priority: number
  conflicts: ScheduleConflict[]
  created_at: string
  updated_at: string
}

export interface ScheduleConflict {
  schedule_id: number
  playlist_name: string
  overlap: string
}

export interface ScheduleCreateParams {
  device_id: number
  playlist_id: number
  start_time: string  // HH:MM:SS
  end_time: string    // HH:MM:SS
  days_of_week?: number  // 默认 127 (每天)
  enabled?: boolean
  priority?: number
}

export interface ScheduleUpdateParams {
  device_id?: number
  playlist_id?: number
  start_time?: string
  end_time?: string
  days_of_week?: number
  enabled?: boolean
  priority?: number
}

export interface ScheduleListResponse {
  schedules: PlaylistSchedule[]
  total: number
}

export interface ActiveScheduleResponse {
  active_playlist_id: number | null
  schedule_id: number | null
  schedule_name: string | null
}

// 播放端调度数据（用于离线评估）
export interface PlayerScheduleData {
  id: number
  playlist_id: number
  start_time: string
  end_time: string
  days_of_week: number
  enabled: boolean
  priority: number
}

export interface PlayerSchedulesResponse {
  schedules: PlayerScheduleData[]
  default_playlist_id: number | null
  server_time: string
  timezone: string
}

// 星期常量
export const DAY_OF_WEEK = {
  MONDAY: 1,
  TUESDAY: 2,
  WEDNESDAY: 4,
  THURSDAY: 8,
  FRIDAY: 16,
  SATURDAY: 32,
  SUNDAY: 64,
  WEEKDAYS: 31,   // Mon-Fri
  WEEKENDS: 96,   // Sat-Sun
  ALL_WEEK: 127,  // All days
} as const

export const DAY_NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'] as const
