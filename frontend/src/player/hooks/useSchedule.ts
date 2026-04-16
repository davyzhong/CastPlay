/**
 * 调度管理 Hook
 * 用于播放端自动切换播放列表
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { scheduleEvaluator, ScheduleData, ScheduleEvaluationResult } from '../services/ScheduleEvaluator';

interface UseScheduleOptions {
  /** 设备 UUID */
  deviceId: string | null;
  /** 当前播放列表 ID */
  currentPlaylistId: number | null;
  /** 是否在线 */
  isOnline?: boolean;
  /** 调度切换回调 */
  onScheduleSwitch?: (playlistId: number, scheduleId: number | null) => void;
  /** 评估间隔（毫秒），默认 60000（1分钟） */
  evaluationInterval?: number;
}

interface UseScheduleReturn {
  /** 当前激活的调度 */
  activeSchedule: ScheduleData | null;
  /** 当前激活的播放列表 ID */
  activePlaylistId: number | null;
  /** 默认播放列表 ID */
  defaultPlaylistId: number | null;
  /** 下一次切换时间 */
  nextSwitchTime: Date | null;
  /** 是否正在加载 */
  isLoading: boolean;
  /** 是否需要切换 */
  shouldSwitch: boolean;
  /** 手动刷新调度数据 */
  refreshSchedules: () => Promise<void>;
  /** 手动评估 */
  evaluate: () => ScheduleEvaluationResult;
}

/**
 * 调度管理 Hook
 */
export function useSchedule(options: UseScheduleOptions): UseScheduleReturn {
  const {
    deviceId,
    currentPlaylistId,
    isOnline = true,
    onScheduleSwitch,
    evaluationInterval = 60000,  // 1 分钟
  } = options;

  const [activeSchedule, setActiveSchedule] = useState<ScheduleData | null>(null);
  const [activePlaylistId, setActivePlaylistId] = useState<number | null>(null);
  const [defaultPlaylistId, setDefaultPlaylistId] = useState<number | null>(null);
  const [nextSwitchTime, setNextSwitchTime] = useState<Date | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [shouldSwitch, setShouldSwitch] = useState(false);

  const lastActivePlaylistIdRef = useRef<number | null>(null);
  const evaluationTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const switchTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // 获取调度数据
  const fetchSchedules = useCallback(async () => {
    if (!deviceId || !isOnline) return;

    setIsLoading(true);
    try {
      const response = await fetch(`/api/player/${deviceId}/schedules`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      scheduleEvaluator.updateSchedules(
        data.schedules || [],
        data.default_playlist_id,
        data.server_time
      );

      setDefaultPlaylistId(data.default_playlist_id);

      // 立即评估
      const result = scheduleEvaluator.evaluate();
      setActiveSchedule(result.activeSchedule);
      setActivePlaylistId(result.activePlaylistId);
      setNextSwitchTime(result.nextSwitchTime);

      console.log('[useSchedule] Fetched schedules:', {
        scheduleCount: data.schedules?.length || 0,
        activePlaylistId: result.activePlaylistId,
        activeScheduleId: result.activeSchedule?.id,
      });
    } catch (error) {
      console.error('[useSchedule] Failed to fetch schedules:', error);
    } finally {
      setIsLoading(false);
    }
  }, [deviceId, isOnline]);

  // 手动评估
  const evaluate = useCallback(() => {
    const result = scheduleEvaluator.evaluate();
    setActiveSchedule(result.activeSchedule);
    setActivePlaylistId(result.activePlaylistId);
    setNextSwitchTime(result.nextSwitchTime);
    return result;
  }, []);

  // 检查是否需要切换
  const checkAndSwitch = useCallback(() => {
    const { shouldSwitch: needSwitch, newPlaylistId, scheduleId } = scheduleEvaluator.shouldSwitchPlaylist(currentPlaylistId);

    if (needSwitch && newPlaylistId !== null) {
      console.log('[useSchedule] Schedule switch detected:', {
        from: currentPlaylistId,
        to: newPlaylistId,
        scheduleId,
      });

      setShouldSwitch(true);
      lastActivePlaylistIdRef.current = newPlaylistId;

      if (onScheduleSwitch) {
        onScheduleSwitch(newPlaylistId, scheduleId);
      }
    }
  }, [currentPlaylistId, onScheduleSwitch]);

  // 设置下一次切换的定时器
  const scheduleNextSwitch = useCallback(() => {
    // 清除之前的定时器
    if (switchTimerRef.current) {
      clearTimeout(switchTimerRef.current);
    }

    const msUntilSwitch = scheduleEvaluator.getMsUntilNextSwitch();
    if (msUntilSwitch !== null && msUntilSwitch > 0) {
      // 限制最大等待时间（1小时），防止定时器过长
      const maxWait = 3600000;
      const waitTime = Math.min(msUntilSwitch, maxWait);

      switchTimerRef.current = setTimeout(() => {
        console.log('[useSchedule] Switch timer triggered');
        checkAndSwitch();
        scheduleNextSwitch();
      }, waitTime);

      console.log('[useSchedule] Scheduled next switch in', Math.round(waitTime / 1000), 'seconds');
    }
  }, [checkAndSwitch]);

  // 初始化：获取调度数据
  useEffect(() => {
    if (deviceId) {
      fetchSchedules();
    }
  }, [deviceId, fetchSchedules]);

  // 定期评估和重新获取调度数据
  useEffect(() => {
    if (!deviceId) return;

    // 设置定期评估定时器
    evaluationTimerRef.current = setInterval(() => {
      console.log('[useSchedule] Periodic evaluation');
      checkAndSwitch();

      // 如果在线，定期刷新调度数据
      if (isOnline) {
        fetchSchedules();
      }
    }, evaluationInterval);

    // 设置切换定时器
    scheduleNextSwitch();

    return () => {
      if (evaluationTimerRef.current) {
        clearInterval(evaluationTimerRef.current);
      }
      if (switchTimerRef.current) {
        clearTimeout(switchTimerRef.current);
      }
    };
  }, [deviceId, isOnline, evaluationInterval, checkAndSwitch, scheduleNextSwitch, fetchSchedules]);

  // 当 currentPlaylistId 变化时，重置 shouldSwitch
  useEffect(() => {
    if (currentPlaylistId === lastActivePlaylistIdRef.current) {
      setShouldSwitch(false);
    }
  }, [currentPlaylistId]);

  return {
    activeSchedule,
    activePlaylistId,
    defaultPlaylistId,
    nextSwitchTime,
    isLoading,
    shouldSwitch,
    refreshSchedules: fetchSchedules,
    evaluate,
  };
}

export default useSchedule;
