/**
 * 播放器核心组件
 * 整合设备注册、播放列表同步、媒体缓存、离线模式、定时播放
 */
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useDeviceRegistration } from './useDeviceRegistration';
import { usePlaylistSync } from './usePlaylistSync';
import { useMediaCache } from './useMediaCache';
import { useOfflineMode } from './useOfflineMode';
import { usePlaybackScheduler } from './usePlaybackScheduler';
import { useHeartbeat } from './hooks/useHeartbeat';
import { ErrorReporter } from './services/ErrorReporter';
import { DeviceIdDisplay } from './components/DeviceIdDisplay';
import type { PlayerPlaylistItem, PlayerState } from './types';

interface PlayerCoreProps {
  onStateChange?: (state: PlayerState) => void;
  onMediaChange?: (item: PlayerPlaylistItem | null) => void;
  autoPlay?: boolean;
  defaultSpeed?: number;
}

export const PlayerCore: React.FC<PlayerCoreProps> = (props: PlayerCoreProps) => {
  const {
    onStateChange,
    onMediaChange,
    autoPlay = true,
    defaultSpeed = 1,
  } = props;

  // 设备注册
  const {
    deviceInfo,
    isRegistered,
    isLoading: isRegistering,
    register,
  } = useDeviceRegistration();

  // 离线模式
  const { isOnline } = useOfflineMode();

  // 播放列表同步
  const {
    currentPlaylist,
  } = usePlaylistSync(deviceInfo?.device_id || null, isOnline);

  // 媒体缓存
  const {
    preloadPlaylist,
  } = useMediaCache(isOnline);

  // 定时播放
  const {
    shouldPlay: shouldBePlaying,
  } = usePlaybackScheduler(
    currentPlaylist ? null : null, // 从初始化响应获取
    deviceInfo?.timezone
  );

  // 播放器状态
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [playbackSpeed] = useState(defaultSpeed);
  const [loopEnabled] = useState(true);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // 当前播放项
  const currentItems = currentPlaylist?.items || [];
  const currentItem = currentItems[currentIndex] || null;

  // 心跳上报（使用 2 小时间隔的 useHeartbeat hook）
  useHeartbeat(
    deviceInfo?.device_id || null,
    currentPlaylist?.id || null,
    currentItem?.media_id || null,
    isPlaying ? 'playing' : 'idle'
  );

  // 更新外部状态
  useEffect(() => {
    onStateChange?.({
      isPlaying,
      currentIndex,
      playbackSpeed,
      loopEnabled,
      isOnline,
      currentPlaylist,
    });
  }, [isPlaying, currentIndex, playbackSpeed, loopEnabled, isOnline, currentPlaylist, onStateChange]);

  useEffect(() => {
    onMediaChange?.(currentItem);
  }, [currentItem, onMediaChange]);

  // 自动注册
  useEffect(() => {
    if (!isRegistered && !isRegistering) {
      register().catch(console.error);
    }
  }, [isRegistered, isRegistering, register]);

  // 初始化错误上报服务
  useEffect(() => {
    if (deviceInfo?.device_id) {
      ErrorReporter.init(deviceInfo.device_id);
    }
    return () => {
      ErrorReporter.stop();
    };
  }, [deviceInfo?.device_id]);

  // 预加载播放列表媒体
  useEffect(() => {
    if (currentPlaylist && isOnline) {
      preloadPlaylist(currentPlaylist.items).catch(console.error);
    }
  }, [currentPlaylist, isOnline, preloadPlaylist]);

  // 播放控制
  const play = useCallback(() => {
    if (currentItems.length === 0) return;
    setIsPlaying(true);
  }, [currentItems.length]);

  const pause = useCallback(() => {
    setIsPlaying(false);
  }, []);

  const next = useCallback(() => {
    if (currentItems.length === 0) return;
    if (currentIndex < currentItems.length - 1) {
      setCurrentIndex(currentIndex + 1);
    } else if (loopEnabled) {
      setCurrentIndex(0);
    } else {
      setIsPlaying(false);
    }
  }, [currentIndex, currentItems.length, loopEnabled]);

  // 自动播放
  useEffect(() => {
    if (autoPlay && shouldBePlaying && currentItems.length > 0 && isRegistered) {
      play();
    } else if (!shouldBePlaying) {
      pause();
    }
  }, [autoPlay, shouldBePlaying, currentItems.length, isRegistered, play, pause]);

  // 自动切换下一项
  useEffect(() => {
    if (!isPlaying || !currentItem) {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
      return;
    }

    // 根据播放速度计算实际显示时间
    const duration = (currentItem.display_duration * 1000) / playbackSpeed;

    timerRef.current = setTimeout(() => {
      next();
    }, duration);

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, [isPlaying, currentItem, playbackSpeed, next]);

  // 渲染（显示设备 ID）
  if (!deviceInfo?.device_id) {
    return null;
  }

  return (
    <DeviceIdDisplay
      deviceId={deviceInfo.device_id}
    />
  );
};

// 导出播放器控制接口
export interface PlayerCoreControl {
  play: () => void;
  pause: () => void;
  stop: () => void;
  next: () => void;
  prev: () => void;
  goToIndex: (index: number) => void;
  setSpeed: (speed: number) => void;
  setLoop: (enabled: boolean) => void;
  isPlaying: boolean;
  currentIndex: number;
  currentItem: PlayerPlaylistItem | null;
  playbackSpeed: number;
  loopEnabled: boolean;
  isOnline: boolean;
  isRegistered: boolean;
  deviceInfo: ReturnType<typeof useDeviceRegistration>['deviceInfo'];
  currentPlaylist: ReturnType<typeof usePlaylistSync>['currentPlaylist'];
  getMediaUrl: (item: PlayerPlaylistItem) => string;
}
