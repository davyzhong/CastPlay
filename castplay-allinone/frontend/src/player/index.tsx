/**
 * 播放器模块入口
 * 导出所有播放器相关的组件、Hooks 和类型
 */

// 组件
export { PlayerCore } from './PlayerCore';
export type { PlayerCoreControl } from './PlayerCore';

// Hooks
export { useDeviceRegistration } from './useDeviceRegistration';
export type { UseDeviceRegistrationReturn } from './useDeviceRegistration';

export { usePlaylistSync } from './usePlaylistSync';
export type { UsePlaylistSyncReturn } from './usePlaylistSync';

export { useMediaCache } from './useMediaCache';
export type { UseMediaCacheReturn } from './useMediaCache';

export { useOfflineMode } from './useOfflineMode';
export type { UseOfflineModeReturn } from './useOfflineMode';

export { usePlaybackScheduler } from './usePlaybackScheduler';
export type { UsePlaybackSchedulerReturn } from './usePlaybackScheduler';

// 类型
export type {
  AndroidBridge,
  PlayerDeviceInfo,
  PlayerPlaylistItem,
  PlayerPlaylist,
  PlayerSchedule,
  PlayerInitResponse,
  CacheStatus,
  CachedMediaInfo,
  PlayerState,
  PlayerWsMessage,
} from './types';
