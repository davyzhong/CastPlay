/**
 * 定时播放调度 Hook
 * 处理设备定时开关机和播放时间控制
 */
import { useState, useCallback, useEffect, useRef } from 'react';
import type { PlayerSchedule } from './types';

export interface UsePlaybackSchedulerReturn {
  schedule: PlayerSchedule | null;
  shouldPlay: boolean;
  checkSchedule: () => { shouldPlay: boolean; timeUntilChange: number | null };
  updateSchedule: (newSchedule: PlayerSchedule) => void;
}

export const usePlaybackScheduler = (
  currentSchedule: PlayerSchedule | null,
  timezone: string = 'Asia/Shanghai'
): UsePlaybackSchedulerReturn => {
  const [schedule, setSchedule] = useState<PlayerSchedule | null>(currentSchedule);
  const [shouldPlay, setShouldPlay] = useState(true);
  const checkIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // 获取 Android Bridge
  const getAndroidBridge = useCallback(() => {
    return window.AndroidBridge;
  }, []);

  // 获取当前时区
  const getCurrentTimezone = useCallback(() => {
    const bridge = getAndroidBridge();
    if (bridge) {
      return bridge.getLocalTimezone() || timezone;
    }
    return timezone || Intl.DateTimeFormat().resolvedOptions().timeZone;
  }, [getAndroidBridge, timezone]);

  // 检查当前是否应该播放
  const checkSchedule = useCallback(() => {
    if (!schedule || !schedule.is_enabled) {
      return { shouldPlay: true, timeUntilChange: null };
    }

    // 获取设备本地时区（用于未来扩展）
    getCurrentTimezone(); // 保留调用以备将来使用
    const now = new Date();

    // 计算本地时间（考虑时区）
    const localDay = now.getDay(); // 0-6, 0=周日

    // 检查今天是否在工作日列表
    // weekdays 使用 1-7，1=周一，7=周日
    // JavaScript getDay() 返回 0=周日，1=周一...6=周六
    // 鷻加配置中使用 1=周一，7=周日，所以需要转换
    const jsDay = localDay === 0 ? 7 : localDay;
    const weekdays = schedule.weekdays || [1, 2, 3, 4, 5];

    if (!weekdays.includes(jsDay)) {
      return { shouldPlay: false, timeUntilChange: null };
    }

    // 检查当前时间是否在播放时段
    const localHour = now.getHours();
    const localMinute = now.getMinutes();
    const currentTime = localHour * 60 + localMinute;

    // 解析开关机时间
    const [onHour, onMin] = (schedule.power_on_time || '00:00').split(':').map(Number);
    const [offHour, offMin] = (schedule.power_off_time || '23:59').split(':').map(Number);
    const onTime = onHour * 60 + onMin;
    const offTime = offHour * 60 + offMin;

    const inPlayTime = currentTime >= onTime && currentTime <= offTime;

    // 计算距离下次状态变化的时间
    let timeUntilChange: number | null = null;
    if (inPlayTime) {
      // 计算距离关机的时间
      timeUntilChange = (offTime - currentTime) * 60 * 1000; // 毫秒
    } else if (currentTime < onTime) {
      // 计算距离开机的时间
      timeUntilChange = (onTime - currentTime) * 60 * 1000;
    }

    return { shouldPlay: inPlayTime, timeUntilChange };
  }, [schedule, getCurrentTimezone]);

  // 更新定时配置
  const updateSchedule = useCallback((newSchedule: PlayerSchedule) => {
    setSchedule(newSchedule);
  }, []);

  // 定期检查定时配置
  useEffect(() => {
    if (!schedule?.is_enabled) {
      setShouldPlay(true);
      return;
    }

    // 立即检查一次
    const result = checkSchedule();
    setShouldPlay(result.shouldPlay);

    // 每分钟检查一次
    checkIntervalRef.current = setInterval(() => {
      const checkResult = checkSchedule();
      setShouldPlay(checkResult.shouldPlay);
    }, 60000);

    return () => {
      if (checkIntervalRef.current) {
        clearInterval(checkIntervalRef.current);
      }
    };
  }, [schedule, checkSchedule]);

  // 同步外部传入的 schedule
  useEffect(() => {
    if (currentSchedule) {
      setSchedule(currentSchedule);
    }
  }, [currentSchedule]);

  return {
    schedule,
    shouldPlay,
    checkSchedule,
    updateSchedule,
  };
};
