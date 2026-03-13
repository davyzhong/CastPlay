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
import { usePlaylistSwitch } from './hooks/usePlaylistSwitch';
import { ErrorReporter } from './services/ErrorReporter';
import { DeviceIdDisplay } from './components/DeviceIdDisplay';
import type { PlayerPlaylistItem, PlayerState, PlayerPlaylist } from './types';

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
    setCurrentPlaylist,
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

  // 切换前回调 - 使用 useCallback 稳定化
  const handleBeforeSwitch = useCallback(async (newPlaylist: PlayerPlaylist): Promise<boolean> => {
    console.log('[PlayerCore] About to switch to playlist:', newPlaylist.id);
    // 暂停当前播放
    setIsPlaying(false);
    // 重置播放索引
    setCurrentIndex(0);
    return true;
  }, []);

  // 切换后回调 - 使用 useCallback 稳定化
  const handleAfterSwitch = useCallback((newPlaylist: PlayerPlaylist) => {
    console.log('[PlayerCore] Switched to playlist:', newPlaylist.id);
    // 更新当前播放列表
    setCurrentPlaylist(newPlaylist);
    // 预加载新播放列表媒体
    if (isOnline) {
      preloadPlaylist(newPlaylist.items).catch(console.error);
    }
    // 恢复播放
    if (autoPlay && shouldBePlaying) {
      setIsPlaying(true);
    }
  }, [setCurrentPlaylist, preloadPlaylist, isOnline, autoPlay, shouldBePlaying]);

  // 切换失败回调 - 使用 useCallback 稳定化
  const handleSwitchFailed = useCallback((_error: Error, rollbackPlaylist: PlayerPlaylist | null) => {
    console.error('[PlayerCore] Switch failed:', _error);
    // 如果有备份，恢复到之前的播放列表
    if (rollbackPlaylist) {
      setCurrentPlaylist(rollbackPlaylist);
    }
    // 恢复播放
    if (autoPlay && shouldBePlaying) {
      setIsPlaying(true);
    }
  }, [setCurrentPlaylist, autoPlay, shouldBePlaying]);

  // 获取 WebSocket URL（Android 环境需要从 AndroidBridge 获取服务器地址）
  const getWsUrl = useCallback((): string | null => {
    if (window.AndroidBridge?.getServerUrl) {
      // Android 环境：从 Bridge 获取服务器 URL
      const serverUrl = window.AndroidBridge.getServerUrl();
      if (serverUrl && serverUrl.length > 0) {
        const wsProtocol = serverUrl.startsWith('https') ? 'wss' : 'ws';
        const wsHost = serverUrl.replace(/^https?:\/\//, '');
        if (wsHost) {
          console.log('[PlayerCore] WebSocket URL from AndroidBridge:', `${wsProtocol}://${wsHost}`);
          return `${wsProtocol}://${wsHost}`;
        }
      }
      console.warn('[PlayerCore] AndroidBridge.getServerUrl() returned empty, waiting...');
      return null;
    } else if (window.location.host) {
      // Web 环境：使用当前页面的 host
      const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
      return `${wsProtocol}://${window.location.host}`;
    }
    return null;
  }, []);

  // 播放列表自动切换
  const { switchState, isSwitching } = usePlaylistSwitch({
    deviceId: deviceInfo?.device_id || null,
    wsUrl: getWsUrl(),
    currentPlaylist,
    switchConfig: {
      policy: 'after_download',
      minReadyRatio: 1.0,
      allowPartialSwitch: true,
      onBeforeSwitch: handleBeforeSwitch,
      onAfterSwitch: handleAfterSwitch,
      onSwitchFailed: handleSwitchFailed,
    },
  });

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
    if (autoPlay && shouldBePlaying && currentItems.length > 0 && isRegistered && !isSwitching) {
      play();
    } else if (!shouldBePlaying || isSwitching) {
      pause();
    }
  }, [autoPlay, shouldBePlaying, currentItems.length, isRegistered, isSwitching, play, pause]);

  // 自动切换下一项（视频和PPT由播放器 onEnded 处理，图片使用定时器）
  useEffect(() => {
    if (!isPlaying || !currentItem) {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
      return;
    }

    // 视频和PPT由播放器的 onEnded 事件处理，不设置定时器
    if (currentItem.file_type === 'video' || currentItem.file_type === 'ppt') {
      return;
    }

    // 图片根据播放速度计算实际显示时间
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

  // 渲染（显示设备 ID 和切换状态）
  if (!deviceInfo?.device_id) {
    return null;
  }

  return (
    <>
      <DeviceIdDisplay
        deviceId={deviceInfo.device_id}
      />
      {/* 显示切换状态 */}
      {isSwitching && (
        <div style={{
          position: 'fixed',
          bottom: 10,
          right: 10,
          background: 'rgba(0, 0, 0, 0.7)',
          color: 'white',
          padding: '8px 16px',
          borderRadius: 4,
          fontSize: 12,
        }}>
          {switchState.status === 'downloading' && (
            <span>正在下载播放列表... {switchState.progress}%</span>
          )}
          {switchState.status === 'switching' && (
            <span>正在切换播放列表...</span>
          )}
          {switchState.status === 'pending' && (
            <span>准备切换播放列表...</span>
          )}
        </div>
      )}
    </>
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
