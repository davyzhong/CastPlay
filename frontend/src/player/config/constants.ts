/**
 * 播放端配置常量
 * 统一管理心跳间隔、下载超时、存储阈值等配置
 */

// ========== 心跳配置 ==========
export const HEARTBEAT_CONFIG =    {
    /** 心跳间隔（毫秒）- 2 小时 */
    INTERVAL_MS: 2 * 60 * 60 * 1000,
    /** 心跳超时（毫秒） */
    TIMEOUT_MS: 5000,
    /** 最大重试次数 */
    MAX_RETRIES: 3,
    /** 重试延迟（毫秒） */
    RETRY_DELAY_MS: 1000,
} as const;

// ========== 下载配置 ==========
export const DOWNLOAD_CONFIG = {
    /** 下载超时（毫秒）- 30 分钟 */
    TIMEOUT_MS: 30 * 60 * 1000,
    /** 最大并发下载数 */
    MAX_CONCURRENT_DOWNLOADS: 3,
    /** 下载失败最大重试次数 */
    MAX_RETRY_COUNT: 3,
    /** 初始重试延迟（毫秒） */
    INITIAL_RETRY_DELAY_MS: 1000,
    /** 最大重试延迟（毫秒） */
    MAX_RETRY_DELAY_MS: 10000,
    /** 下载进度更新间隔（毫秒） */
    PROGRESS_UPDATE_INTERVAL_MS: 500,
} as const;

// ========== 存储配置 ==========
export const STORAGE_CONFIG = {
    /** 最小剩余空间（字节）- 100MB */
    MIN_FREE_SPACE_BYTES: 100 * 1024 * 1024,
    /** 存储警告阈值（百分比） */
    STORAGE_WARNING_THRESHOLD_PERCENT: 90,
    /** 最大缓存大小（字节）- 5GB */
    MAX_CACHE_SIZE_BYTES: 5 * 1024 * 1024 * 1024,
    /** 旧文件清理阈值（天） */
    OLD_FILE_THRESHOLD_DAYS: 30,
    /** 清理检查间隔（毫秒）- 1 小时 */
    CLEANUP_CHECK_INTERVAL_MS: 60 * 60 * 1000,
} as const;

// ========== 播放配置 ==========
export const PLAYBACK_CONFIG = {
    /** 默认播放速度 */
    DEFAULT_SPEED: 1,
    /** 最小播放速度 */
    MIN_SPEED: 0.5,
    /** 最大播放速度 */
    MAX_SPEED: 2,
    /** 默认循环播放 */
    DEFAULT_LOOP_ENABLED: true,
    /** 播放错误最大重试次数 */
    PLAYBACK_ERROR_MAX_RETRIES: 3,
    /** 播放错误重试延迟（毫秒） */
    PLAYBACK_ERROR_RETRY_DELAY_MS: 2000,
} as const;

// ========== 网络配置 ==========
export const NETWORK_CONFIG = {
    /** API 请求超时（毫秒） */
    API_TIMEOUT_MS: 10000,
    /** WebSocket 重连间隔（毫秒） */
    WS_RECONNECT_INTERVAL_MS: 5000,
    /** WebSocket 最大重连次数 */
    WS_MAX_RECONNECT_ATTEMPTS: 10,
    /** 离线检测间隔（毫秒） */
    OFFLINE_CHECK_INTERVAL_MS: 30000,
    /** 网络恢复后同步延迟（毫秒） */
    ONLINE_SYNC_DELAY_MS: 1000,
} as const;

// ========== 缓存配置 ==========
export const CACHE_CONFIG = {
    /** 缓存名称 */
    CACHE_NAME: 'castplay-media-cache',
    /** IndexedDB 数据库名称 */
    IDB_NAME: 'CastPlayDB',
    /** IndexedDB 版本 */
    IDB_VERSION: 1,
    /** 媒体存储仓库名称 */
    MEDIA_STORE: 'media',
    /** 元数据存储仓库名称 */
    META_STORE: 'metadata',
    /** 最大缓存项数量 */
    MAX_CACHE_ITEMS: 100,
} as const;

// ========== 定时播放配置 ==========
export const SCHEDULE_CONFIG = {
    /** 默认开机时间 */
    DEFAULT_POWER_ON_TIME: '08:00',
    /** 默认关机时间 */
    DEFAULT_POWER_OFF_TIME: '18:00',
    /** 默认工作日（周一到周五） */
    DEFAULT_WEEKDAYS: [0, 1, 2, 3, 4] as const,
    /** 定时检查间隔（毫秒）- 1 分钟 */
    SCHEDULE_CHECK_INTERVAL_MS: 60 * 1000,
} as const;

// ========== 错误上报配置 ==========
export const ERROR_REPORT_CONFIG = {
    /** 是否启用错误上报 */
    ENABLED: true,
    /** 最大重试次数 */
    MAX_RETRIES: 3,
    /** 重试延迟（毫秒） */
    RETRY_DELAY_MS: 5000,
    /** 批量发送大小 */
    BATCH_SIZE: 10,
    /** 刷新间隔（毫秒） */
    FLUSH_INTERVAL_MS: 30000,
} as const;

// ========== UI 配置 ==========
export const UI_CONFIG = {
    /** 设备 ID 显示持续时间（毫秒） */
    DEVICE_ID_DISPLAY_DURATION_MS: 5000,
    /** 加载状态超时（毫秒） */
    LOADING_TIMEOUT_MS: 10000,
    /** Toast 消息持续时间（毫秒） */
    TOAST_DURATION_MS: 3000,
    /** 动画过渡时间（毫秒） */
    TRANSITION_DURATION_MS: 300,
} as const;

// ========== 设备状态配置 ==========
export const DEVICE_STATUS = {
    /** 在线状态 */
    ONLINE: 'online',
    /** 离线状态 */
    OFFLINE: 'offline',
    /** 播放中 */
    PLAYING: 'playing',
    /** 空闲 */
    IDLE: 'idle',
    /** 暂停 */
    PAUSED: 'paused',
} as const;

// ========== 媒体类型 ==========
export const MEDIA_TYPES = {
    /** 视频 */
    VIDEO: 'video',
    /** 图片 */
    IMAGE: 'image',
    /** PPT */
    PPT: 'ppt',
    /** 音频 */
    AUDIO: 'audio',
} as const;

// ========== 日志级别 ==========
export const LOG_LEVELS = {
    DEBUG: 'debug',
    INFO: 'info',
    WARN: 'warn',
    ERROR: 'error',
} as const;

// 导出所有配置
export const PLAYER_CONFIG = {
    heartbeat: HEARTBEAT_CONFIG,
    download: DOWNLOAD_CONFIG,
    storage: STORAGE_CONFIG,
    playback: PLAYBACK_CONFIG,
    network: NETWORK_CONFIG,
    cache: CACHE_CONFIG,
    schedule: SCHEDULE_CONFIG,
    errorReport: ERROR_REPORT_CONFIG,
    ui: UI_CONFIG,
} as const;

export default PLAYER_CONFIG;
