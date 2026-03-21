/**
 * 播放列表自动切换 Hook
 *
 * 功能：
 * - 监听播放列表变更（通过 usePlaylistChangeDetection）
 * - 自动下载新播放列表内容（通过 usePlaylistDownload）
 * - 下载完成后自动切换
 * - 支持失败回滚
 * - 通知后端切换完成
 * - 存储空间检查
 * - 增量更新支持
 * - 事件日志记录
 */
import { useState, useCallback, useRef, useEffect, useMemo } from 'react';
import axios from 'axios';
import { usePlaylistChangeDetection, PlaylistUpdateInfo } from './usePlaylistChangeDetection';
import { usePlaylistDownload } from './usePlaylistDownload';
import { storageChecker } from '../services/StorageChecker';
import { switchEventLogger } from '../services/SwitchEventLogger';
import { playlistDownloadManager } from '../services/PlaylistDownloadManager';
import type { PlayerPlaylist } from '../types';

// 切换状态
export type SwitchStatus = 'idle' | 'pending' | 'downloading' | 'ready' | 'switching' | 'completed' | 'failed';

// 切换策略
export type SwitchPolicy = 'immediate' | 'after_download' | 'scheduled';

// 切换配置
export interface SwitchConfig {
    // 切换策略
    policy: SwitchPolicy;
    // 最小就绪比例（0-1），下载达到此比例后可以切换
    minReadyRatio: number;
    // 下载超时时间（毫秒）
    downloadTimeout: number;
    // 是否允许部分切换（部分文件下载失败时仍切换）
    allowPartialSwitch: boolean;
    // 切换前回调
    onBeforeSwitch?: (newPlaylist: PlayerPlaylist) => Promise<boolean>;
    // 切换后回调
    onAfterSwitch?: (newPlaylist: PlayerPlaylist) => void;
    // 切换失败回调
    onSwitchFailed?: (error: Error, rollbackPlaylist: PlayerPlaylist | null) => void;
}

// 切换状态详情
export interface SwitchState {
    status: SwitchStatus;
    targetPlaylistId: number | null;
    targetVersion: string | null;
    progress: number;
    completedFiles: number;
    totalFiles: number;
    failedFiles: number;
    error: string | null;
    startTime: number | null;
}

// Hook 配置
export interface UsePlaylistSwitchConfig {
    deviceId: string | null;
    wsUrl?: string | null;
    currentPlaylist: PlayerPlaylist | null;
    switchConfig?: Partial<SwitchConfig>;
}

// Hook 返回值
export interface UsePlaylistSwitchReturn {
    // 状态
    switchState: SwitchState;
    isSwitching: boolean;
    canSwitch: boolean;

    // 方法
    startSwitch: (playlistId: number) => Promise<void>;
    cancelSwitch: () => void;
    confirmSwitch: () => void;
    rollback: () => Promise<void>;
}

// 默认配置
const DEFAULT_SWITCH_CONFIG: SwitchConfig = {
    policy: 'after_download',
    minReadyRatio: 1.0, // 100% 下载完成才切换
    downloadTimeout: 30 * 60 * 1000, // 30 分钟
    allowPartialSwitch: false,
};

export const usePlaylistSwitch = (
    config: UsePlaylistSwitchConfig
): UsePlaylistSwitchReturn => {
    const {
        deviceId,
        wsUrl,
        currentPlaylist,
        switchConfig: userSwitchConfig,
    } = config;

    // 使用 ref 存储回调，避免依赖数组变化
    const callbacksRef = useRef({
        onBeforeSwitch: userSwitchConfig?.onBeforeSwitch,
        onAfterSwitch: userSwitchConfig?.onAfterSwitch,
        onSwitchFailed: userSwitchConfig?.onSwitchFailed,
    });

    // 更新 callbacks ref（不触发重渲染）
    callbacksRef.current = {
        onBeforeSwitch: userSwitchConfig?.onBeforeSwitch,
        onAfterSwitch: userSwitchConfig?.onAfterSwitch,
        onSwitchFailed: userSwitchConfig?.onSwitchFailed,
    };

    // 只使用原始值作为依赖，避免对象重建导致的无限循环
    const switchConfig = useMemo(() => ({
        policy: userSwitchConfig?.policy ?? DEFAULT_SWITCH_CONFIG.policy,
        minReadyRatio: userSwitchConfig?.minReadyRatio ?? DEFAULT_SWITCH_CONFIG.minReadyRatio,
        downloadTimeout: userSwitchConfig?.downloadTimeout ?? DEFAULT_SWITCH_CONFIG.downloadTimeout,
        allowPartialSwitch: userSwitchConfig?.allowPartialSwitch ?? DEFAULT_SWITCH_CONFIG.allowPartialSwitch,
    }), [
        userSwitchConfig?.policy,
        userSwitchConfig?.minReadyRatio,
        userSwitchConfig?.downloadTimeout,
        userSwitchConfig?.allowPartialSwitch,
    ]);

    // 状态
    const [switchState, setSwitchState] = useState<SwitchState>({
        status: 'idle',
        targetPlaylistId: null,
        targetVersion: null,
        progress: 0,
        completedFiles: 0,
        totalFiles: 0,
        failedFiles: 0,
        error: null,
        startTime: null,
    });

    // 备份的播放列表（用于回滚）
    const backupPlaylistRef = useRef<PlayerPlaylist | null>(null);
    // 目标播放列表数据
    const targetPlaylistRef = useRef<PlayerPlaylist | null>(null);
    // 下载超时定时器
    const downloadTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    // 下载 Hook
    const {
        status: downloadStatus,
        progress: downloadProgress,
        completedFiles,
        totalFiles,
        failedFiles,
        startDownload,
        cancelDownload,
    } = usePlaylistDownload();

    /**
     * 获取播放列表详情
     */
    const fetchPlaylistDetails = useCallback(async (playlistId: number): Promise<PlayerPlaylist | null> => {
        try {
            const response = await axios.get<PlayerPlaylist>(`/api/player/playlist/${playlistId}`);
            return response.data;
        } catch (error) {
            console.error('[usePlaylistSwitch] Failed to fetch playlist:', error);
            return null;
        }
    }, []);

    /**
     * 通知后端切换完成
     */
    const notifyBackendSwitchComplete = useCallback(async (playlistId: number, version: string) => {
        try {
            // 检查是否是 Android 环境
            if (window.AndroidBridge) {
                window.AndroidBridge.reportSwitchComplete(playlistId.toString(), version);
            }

            // 同时通过 HTTP API 通知
            await axios.post('/api/player/playlist/switch-complete', {
                device_id: deviceId,
                playlist_id: playlistId,
                version: version,
                timestamp: new Date().toISOString(),
            });
        } catch (error) {
            console.error('[usePlaylistSwitch] Failed to notify backend:', error);
        }
    }, [deviceId]);

    /**
     * 执行播放列表切换
     */
    const performSwitch = useCallback(async () => {
        const targetPlaylist = targetPlaylistRef.current;
        if (!targetPlaylist) {
            console.error('[usePlaylistSwitch] No target playlist to switch to');
            return;
        }

        setSwitchState(prev => ({ ...prev, status: 'switching' }));
        switchEventLogger.logSwitchStarted(targetPlaylist.id, targetPlaylist.version);

        try {
            // 调用切换前回调（使用 ref 避免依赖变化）
            if (callbacksRef.current.onBeforeSwitch) {
                const canProceed = await callbacksRef.current.onBeforeSwitch(targetPlaylist);
                if (!canProceed) {
                    throw new Error('Switch cancelled by onBeforeSwitch callback');
                }
            }

            // 备份当前播放列表（用于回滚）
            if (currentPlaylist) {
                backupPlaylistRef.current = { ...currentPlaylist };
            }

            // 通知后端切换完成
            await notifyBackendSwitchComplete(targetPlaylist.id, targetPlaylist.version);

            // 保存到本地存储
            localStorage.setItem('last_playlist_id', targetPlaylist.id.toString());
            localStorage.setItem('cached_playlists', JSON.stringify([targetPlaylist]));

            // 更新状态
            setSwitchState(prev => ({
                ...prev,
                status: 'completed',
                progress: 100,
            }));

            // 记录切换完成
            switchEventLogger.logSwitchCompleted(targetPlaylist.id, targetPlaylist.version);

            // 调用切换后回调（使用 ref 避免依赖变化）
            if (callbacksRef.current.onAfterSwitch) {
                callbacksRef.current.onAfterSwitch(targetPlaylist);
            }

            console.log('[usePlaylistSwitch] Switch completed:', targetPlaylist.id);

            // 清理超时定时器
            if (downloadTimeoutRef.current) {
                clearTimeout(downloadTimeoutRef.current);
                downloadTimeoutRef.current = null;
            }

        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            console.error('[usePlaylistSwitch] Switch failed:', errorMessage);

            // 记录切换失败
            switchEventLogger.logSwitchFailed(targetPlaylist.id, errorMessage);

            setSwitchState(prev => ({
                ...prev,
                status: 'failed',
                error: errorMessage,
            }));

            // 调用失败回调（使用 ref 避免依赖变化）
            if (callbacksRef.current.onSwitchFailed) {
                callbacksRef.current.onSwitchFailed(
                    error instanceof Error ? error : new Error(errorMessage),
                    backupPlaylistRef.current
                );
            }
        }
    }, [currentPlaylist, notifyBackendSwitchComplete]);

    /**
     * 检查是否可以切换
     */
    const checkCanSwitch = useCallback((): boolean => {
        if (switchState.status !== 'downloading' && switchState.status !== 'ready') {
            return false;
        }

        const { completedFiles: completed, totalFiles: total, failedFiles: failed } = switchState;
        const readyRatio = total > 0 ? completed / total : 0;

        // 检查是否达到最小就绪比例
        if (readyRatio >= switchConfig.minReadyRatio) {
            return true;
        }

        // 检查是否允许部分切换
        if (switchConfig.allowPartialSwitch && failed > 0) {
            const successRatio = total > 0 ? (completed + failed) / total : 0;
            return successRatio >= switchConfig.minReadyRatio;
        }

        return false;
    }, [switchState, switchConfig]);

    /**
     * 开始切换流程
     */
    const startSwitch = useCallback(async (playlistId: number) => {
        console.log('[usePlaylistSwitch] Starting switch to playlist:', playlistId);

        // 记录切换检测事件
        switchEventLogger.logSwitchDetected(playlistId, 'unknown');

        // 重置状态
        setSwitchState({
            status: 'pending',
            targetPlaylistId: playlistId,
            targetVersion: null,
            progress: 0,
            completedFiles: 0,
            totalFiles: 0,
            failedFiles: 0,
            error: null,
            startTime: Date.now(),
        });

        try {
            // 获取播放列表详情
            const playlist = await fetchPlaylistDetails(playlistId);
            if (!playlist) {
                throw new Error('Failed to fetch playlist details');
            }

            // 更新日志中的版本信息
            switchEventLogger.logSwitchDetected(playlistId, playlist.version);

            targetPlaylistRef.current = playlist;

            setSwitchState(prev => ({
                ...prev,
                targetVersion: playlist.version,
                totalFiles: playlist.items.length,
            }));

            // 检查存储空间
            const spaceCheck = await storageChecker.checkSpace(playlist.items);
            if (!spaceCheck.canDownload) {
                const error = spaceCheck.warning || 'Insufficient storage space';
                switchEventLogger.logError(error, { playlistId, availableSpace: spaceCheck.availableSpace });
                throw new Error(error);
            }

            if (spaceCheck.warning) {
                console.warn('[usePlaylistSwitch] Storage warning:', spaceCheck.warning);
            }

            // 增量更新：计算需要下载的文件
            const { toDownload, unchanged } = await playlistDownloadManager.calculateIncrementalUpdate(
                playlist.items.map(item => ({
                    id: item.media_id,
                    file_url: item.file_url,
                    md5_hash: item.md5_hash,
                }))
            );

            console.log(`[usePlaylistSwitch] Incremental update: ${toDownload.length} to download, ${unchanged.length} unchanged`);

            // 如果所有文件都已缓存，直接切换
            if (toDownload.length === 0) {
                console.log('[usePlaylistSwitch] All files cached, switching immediately');
                await performSwitch();
                return;
            }

            // 设置下载超时
            downloadTimeoutRef.current = setTimeout(() => {
                console.warn('[usePlaylistSwitch] Download timeout');
                switchEventLogger.logDownloadFailed(playlistId, 'Download timeout');
                setSwitchState(prev => ({
                    ...prev,
                    status: 'failed',
                    error: 'Download timeout',
                }));
            }, switchConfig.downloadTimeout);

            // 记录下载开始
            switchEventLogger.logDownloadStarted(playlistId, playlist.version, toDownload.length);

            // 只下载需要更新的文件
            const mediaList: Array<{ id: number; file_url: string; file_name?: string; file_type?: string; file_size?: number; md5_hash?: string }> =
                toDownload.map(item => ({
                    id: item.id,
                    file_url: item.file_url,
                    md5_hash: item.md5_hash,
                }));

            await startDownload(playlistId, playlist.version, mediaList);

            setSwitchState(prev => ({ ...prev, status: 'downloading' }));

        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            console.error('[usePlaylistSwitch] Failed to start switch:', errorMessage);
            switchEventLogger.logSwitchFailed(playlistId, errorMessage);

            setSwitchState(prev => ({
                ...prev,
                status: 'failed',
                error: errorMessage,
            }));
        }
    }, [fetchPlaylistDetails, startDownload, switchConfig.downloadTimeout, performSwitch]);

    /**
     * 取消切换
     */
    const cancelSwitch = useCallback(() => {
        console.log('[usePlaylistSwitch] Cancelling switch');

        // 取消下载
        cancelDownload();

        // 清理超时定时器
        if (downloadTimeoutRef.current) {
            clearTimeout(downloadTimeoutRef.current);
            downloadTimeoutRef.current = null;
        }

        // 重置状态
        setSwitchState({
            status: 'idle',
            targetPlaylistId: null,
            targetVersion: null,
            progress: 0,
            completedFiles: 0,
            totalFiles: 0,
            failedFiles: 0,
            error: null,
            startTime: null,
        });

        targetPlaylistRef.current = null;
    }, [cancelDownload]);

    /**
     * 确认切换（手动确认）
     */
    const confirmSwitch = useCallback(() => {
        if (checkCanSwitch()) {
            performSwitch();
        }
    }, [checkCanSwitch, performSwitch]);

    /**
     * 回滚到之前的播放列表
     */
    const rollback = useCallback(async () => {
        console.log('[usePlaylistSwitch] Rolling back');

        const backupPlaylist = backupPlaylistRef.current;
        if (!backupPlaylist) {
            console.warn('[usePlaylistSwitch] No backup playlist to rollback to');
            return;
        }

        // 记录回滚事件
        switchEventLogger.logRollback(backupPlaylist.id, 'User triggered rollback');

        try {
            // 恢复备份的播放列表
            localStorage.setItem('last_playlist_id', backupPlaylist.id.toString());

            // 通知后端
            await notifyBackendSwitchComplete(backupPlaylist.id, backupPlaylist.version);

            // 重置状态
            setSwitchState({
                status: 'idle',
                targetPlaylistId: null,
                targetVersion: null,
                progress: 0,
                completedFiles: 0,
                totalFiles: 0,
                failedFiles: 0,
                error: null,
                startTime: null,
            });

            console.log('[usePlaylistSwitch] Rollback completed');
        } catch (error) {
            console.error('[usePlaylistSwitch] Rollback failed:', error);
            switchEventLogger.logError('Rollback failed', { error: String(error) });
        }
    }, [notifyBackendSwitchComplete]);

    /**
     * 处理播放列表变更检测
     */
    const handlePlaylistAssigned = useCallback(async (update: PlaylistUpdateInfo) => {
        console.log('[usePlaylistSwitch] Playlist assigned:', update);

        // 如果当前正在切换，先取消
        if (switchState.status !== 'idle') {
            cancelSwitch();
        }

        // 开始新的切换
        await startSwitch(update.playlist_id);
    }, [switchState.status, cancelSwitch, startSwitch]);

    const handlePlaylistUpdated = useCallback((update: PlaylistUpdateInfo) => {
        console.log('[usePlaylistSwitch] Playlist updated:', update);

        // 如果是当前播放列表的更新，检查是否需要重新下载
        if (currentPlaylist && update.playlist_id === currentPlaylist.id) {
            if (update.version !== currentPlaylist.version) {
                handlePlaylistAssigned(update);
            }
        }
    }, [currentPlaylist, handlePlaylistAssigned]);

    // 监听下载状态变化
    useEffect(() => {
        setSwitchState(prev => ({
            ...prev,
            progress: downloadProgress,
            completedFiles,
            totalFiles,
            failedFiles,
        }));

        // 下载完成时自动切换
        if (downloadStatus === 'completed' || downloadStatus === 'partial') {
            if (switchConfig.policy === 'after_download') {
                if (downloadStatus === 'completed' || switchConfig.allowPartialSwitch) {
                    setSwitchState(prev => ({ ...prev, status: 'ready' }));
                    performSwitch();
                }
            }
        } else if (downloadStatus === 'failed') {
            setSwitchState(prev => ({
                ...prev,
                status: 'failed',
                error: 'Download failed',
            }));
        }
    }, [downloadStatus, downloadProgress, completedFiles, totalFiles, failedFiles, switchConfig, performSwitch]);

    // 使用变更检测 Hook
    usePlaylistChangeDetection({
        deviceId,
        currentPlaylistId: currentPlaylist?.id || null,
        currentPlaylistVersion: currentPlaylist?.version || null,
        wsUrl,
        onPlaylistAssigned: handlePlaylistAssigned,
        onPlaylistUpdated: handlePlaylistUpdated,
    });

    // 检查是否可以切换
    const canSwitch = checkCanSwitch();
    const isSwitching = ['pending', 'downloading', 'ready', 'switching'].includes(switchState.status);

    return {
        switchState,
        isSwitching,
        canSwitch,
        startSwitch,
        cancelSwitch,
        confirmSwitch,
        rollback,
    };
};

export default usePlaylistSwitch;
