/**
 * 真实播放端页面
 * 用于实际设备播放，全屏无 UI
 */
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useDeviceRegistration } from '../player/useDeviceRegistration';
import { usePlaylistSync } from '../player/usePlaylistSync';
import { useOfflineMode } from '../player/useOfflineMode';
import { useHeartbeat } from '../player/hooks/useHeartbeat';
import { ErrorReporter } from '../player/services/ErrorReporter';
import type { PlayerPlaylistItem } from '../player/types';

const PlayerPage: React.FC = () => {
  // 设备注册
  const { deviceInfo, isRegistered, register } = useDeviceRegistration();

  // 离线模式
  const { isOnline } = useOfflineMode();

  // 播放列表同步（包含平滑切换支持）
  const { currentPlaylist, pendingUpdate, applyPendingUpdate } = usePlaylistSync(
    deviceInfo?.device_id || null,
    isOnline
  );

  // 播放状态
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  // 当前播放项
  const items = currentPlaylist?.items || [];
  const currentItem = items[currentIndex] || null;

  // 心跳上报
  useHeartbeat(
    deviceInfo?.device_id || null,
    currentPlaylist?.id || null,
    currentItem?.media_id || null,
    isPlaying ? 'playing' : 'idle'
  );

  // 调试信息
  useEffect(() => {
    console.log('[PlayerPage] State:', JSON.stringify({
      isRegistered,
      deviceId: deviceInfo?.device_id,
      playlistId: currentPlaylist?.id,
      playlistName: currentPlaylist?.name,
      itemCount: items.length,
      currentIndex,
      isPlaying,
      isOnline,
      pendingUpdate
    }));
  }, [isRegistered, deviceInfo, currentPlaylist, items.length, currentIndex, isPlaying, isOnline, pendingUpdate]);

  // 初始化错误上报
  useEffect(() => {
    if (deviceInfo?.device_id) {
      ErrorReporter.setDeviceId(deviceInfo.device_id);
    }
  }, [deviceInfo?.device_id]);

  // 自动注册
  useEffect(() => {
    if (!isRegistered) {
      register().catch(console.error);
    }
  }, [isRegistered, register]);

  // 自动播放
  useEffect(() => {
    if (currentPlaylist && items.length > 0 && isRegistered) {
      setIsPlaying(true);
    }
  }, [currentPlaylist, items.length, isRegistered]);

  // 播放下一项（支持平滑切换）
  const playNext = useCallback(() => {
    // 检查是否有待处理的播放列表更新（平滑切换）
    if (pendingUpdate) {
      console.log('[PlayerPage] Applying pending playlist update (smooth transition)');
      applyPendingUpdate();
      setCurrentIndex(0); // 从新播放列表的第一项开始
      return;
    }

    if (items.length === 0) return;

    if (currentIndex < items.length - 1) {
      setCurrentIndex(currentIndex + 1);
    } else {
      setCurrentIndex(0); // 循环播放
    }
  }, [currentIndex, items.length, pendingUpdate, applyPendingUpdate]);

  // 图片自动切换
  useEffect(() => {
    if (!isPlaying || !currentItem) {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
      return;
    }

    // 视频由 onEnded 处理
    if (currentItem.file_type === 'video') {
      return;
    }

    // 图片定时切换
    const duration = (currentItem.display_duration || 10) * 1000;
    timerRef.current = setTimeout(playNext, duration);

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, [isPlaying, currentItem, playNext]);

  // 获取媒体 URL
  const getMediaUrl = (item: PlayerPlaylistItem): string => {
    if (item.file_url) {
      // 如果是完整 URL，直接返回
      if (item.file_url.startsWith('http')) {
        return item.file_url;
      }
      // 如果已经以 /api 开头，直接返回
      if (item.file_url.startsWith('/api')) {
        return item.file_url;
      }
      // 否则添加 /api 前缀
      return `/api${item.file_url}`;
    }
    return `/api/player/media/${item.media_id}/download`;
  };

  // 视频播放结束
  const handleVideoEnded = useCallback(() => {
    playNext();
  }, [playNext]);

  // 渲染媒体
  const renderMedia = () => {
    if (!currentItem) {
      return (
        <div style={styles.placeholder}>
          <p>等待播放列表...</p>
          <p style={styles.deviceId}>
            设备 ID: {deviceInfo?.device_id || '注册中...'}
          </p>
        </div>
      );
    }

    const mediaUrl = getMediaUrl(currentItem);
    const fileType = currentItem.file_type;

    if (fileType === 'video') {
      return (
        <video
          ref={videoRef}
          src={mediaUrl}
          autoPlay
          muted
          onEnded={handleVideoEnded}
          style={styles.media}
          onError={(e) => {
            console.error('Video playback error:', e);
            ErrorReporter.reportPlaybackError(
              `Video playback failed: ${currentItem.file_name}`,
              currentItem.media_id
            );
            playNext();
          }}
        />
      );
    }

    if (fileType === 'image') {
      return (
        <img
          src={mediaUrl}
          alt={currentItem.file_name || 'media'}
          style={styles.media}
          onError={(e) => {
            console.error('Image load error:', e);
            playNext();
          }}
        />
      );
    }

    // PPT 已转换为视频，按视频处理
    if (fileType === 'ppt') {
      return (
        <video
          ref={videoRef}
          src={mediaUrl}
          autoPlay
          muted
          onEnded={handleVideoEnded}
          style={styles.media}
          onError={(e) => {
            console.error('PPT video playback error:', e);
            playNext();
          }}
        />
      );
    }

    // 不支持的类型，跳过
    console.warn('Unsupported media type:', fileType);
    playNext();
    return null;
  };

  return (
    <div style={styles.container}>
      {renderMedia()}

      {/* 右下角信息浮层（低可视度） */}
      <div style={styles.infoOverlay}>
        {currentPlaylist?.name && (
          <div style={styles.playlistName} title="当前播放列表">
            📋 {currentPlaylist.name}
          </div>
        )}
        {deviceInfo?.registration_code && (
          <div style={styles.deviceIdOverlay} title="设备注册码">
            {deviceInfo.registration_code}
          </div>
        )}
      </div>

      {/* 离线指示器 */}
      {!isOnline && (
        <div style={styles.offlineIndicator}>
          离线模式
        </div>
      )}

      {/* 待更新指示器（播放列表更新将在当前项播放完成后生效） */}
      {pendingUpdate && (
        <div style={styles.pendingIndicator}>
          ⏳ 播放列表更新中...
        </div>
      )}
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    width: '100vw',
    height: '100vh',
    backgroundColor: '#000',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    overflow: 'hidden',
    margin: 0,
    padding: 0,
  },
  media: {
    maxWidth: '100%',
    maxHeight: '100%',
    objectFit: 'contain',
  },
  placeholder: {
    color: '#666',
    textAlign: 'center',
    fontSize: '24px',
  },
  deviceId: {
    fontSize: '14px',
    marginTop: '20px',
    color: '#999',
    fontFamily: 'monospace',
  },
  deviceIdOverlay: {
    color: 'rgba(255,255,255,0.3)',
    fontSize: '12px',
    fontFamily: 'monospace',
  },
  playlistName: {
    color: 'rgba(255,255,255,0.3)',
    fontSize: '12px',
    fontFamily: 'monospace',
    marginBottom: '4px',
  },
  infoOverlay: {
    position: 'absolute',
    bottom: '10px',
    right: '10px',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'flex-end',
    gap: '2px',
    padding: '8px 12px',
    backgroundColor: 'rgba(0,0,0,0.5)',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  offlineIndicator: {
    position: 'absolute',
    top: '10px',
    left: '10px',
    color: '#ff9800',
    fontSize: '14px',
    padding: '5px 10px',
    backgroundColor: 'rgba(0,0,0,0.7)',
    borderRadius: '4px',
  },
  pendingIndicator: {
    position: 'absolute',
    top: '10px',
    right: '10px',
    color: '#4fc3f7',
    fontSize: '14px',
    padding: '5px 10px',
    backgroundColor: 'rgba(0,0,0,0.7)',
    borderRadius: '4px',
  },
};

export default PlayerPage;
