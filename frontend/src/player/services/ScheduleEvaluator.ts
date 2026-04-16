/**
 * 调度评估服务
 * 用于播放端离线评估调度规则，自动切换播放列表
 */

export interface ScheduleData {
  id: number;
  playlist_id: number;
  start_time: string;  // HH:MM:SS
  end_time: string;    // HH:MM:SS
  days_of_week: number;  // 位掩码
  enabled: boolean;
  priority: number;
}

export interface ScheduleEvaluationResult {
  activeSchedule: ScheduleData | null;
  activePlaylistId: number | null;
  nextSchedule: ScheduleData | null;
  nextSwitchTime: Date | null;
}

export class ScheduleEvaluator {
  private schedules: ScheduleData[] = [];
  private defaultPlaylistId: number | null = null;
  private serverTimeOffset: number = 0;  // 服务器时间与本地时间的偏移（毫秒）
  private lastEvaluation: ScheduleEvaluationResult | null = null;

  constructor() {
    // 构造函数
  }

  /**
   * 更新调度数据
   */
  updateSchedules(
    schedules: ScheduleData[],
    defaultPlaylistId: number | null = null,
    serverTime?: string
  ): void {
    this.schedules = schedules.filter(s => s.enabled);
    if (defaultPlaylistId !== undefined) {
      this.defaultPlaylistId = defaultPlaylistId;
    }

    // 计算服务器时间偏移
    if (serverTime) {
      const serverDate = new Date(serverTime);
      this.serverTimeOffset = serverDate.getTime() - Date.now();
    }

    console.log('[ScheduleEvaluator] Updated schedules:', {
      scheduleCount: this.schedules.length,
      defaultPlaylistId: this.defaultPlaylistId,
      serverTimeOffset: this.serverTimeOffset,
    });
  }

  /**
   * 获取当前时间（考虑服务器时间偏移）
   */
  private getCurrentTime(): Date {
    return new Date(Date.now() + this.serverTimeOffset);
  }

  /**
   * 评估当前应该激活的调度
   */
  evaluate(): ScheduleEvaluationResult {
    const now = this.getCurrentTime();
    const currentTime = now.getTime();
    const currentDay = now.getDay();
    // JavaScript: 0=Sunday, 6=Saturday
    // 我们的位掩码: 0=Monday, 6=Sunday
    const dayBit = currentDay === 0 ? 64 : 1 << (currentDay - 1);

    // 当前时间（时:分:秒）
    const currentHours = now.getHours();
    const currentMinutes = now.getMinutes();
    const currentSeconds = now.getSeconds();
    const currentTotalSeconds = currentHours * 3600 + currentMinutes * 60 + currentSeconds;

    // 找出所有匹配的调度
    const matchingSchedules = this.schedules.filter(schedule => {
      // 检查星期
      if (!(schedule.days_of_week & dayBit)) {
        return false;
      }

      // 检查时间范围
      const startSeconds = this.timeToSeconds(schedule.start_time);
      const endSeconds = this.timeToSeconds(schedule.end_time);

      // 处理不跨天的情况
      if (startSeconds < endSeconds) {
        return currentTotalSeconds >= startSeconds && currentTotalSeconds < endSeconds;
      }

      // 处理跨天的情况（如 22:00 - 06:00）
      return currentTotalSeconds >= startSeconds || currentTotalSeconds < endSeconds;
    });

    // 按优先级排序（高优先级优先）
    matchingSchedules.sort((a, b) => b.priority - a.priority);

    // 找出下一个将激活的调度
    let nextSchedule: ScheduleData | null = null;
    let nextSwitchTime: Date | null = null;
    let minTimeUntilNext = Infinity;

    for (const schedule of this.schedules) {
      const timeUntilNext = this.calculateTimeUntilNext(schedule, currentTotalSeconds, dayBit, now);

      if (timeUntilNext !== null && timeUntilNext > 0 && timeUntilNext < minTimeUntilNext) {
        minTimeUntilNext = timeUntilNext;
        nextSchedule = schedule;
        nextSwitchTime = new Date(currentTime + timeUntilNext * 1000);
      }
    }

    const result: ScheduleEvaluationResult = {
      activeSchedule: matchingSchedules[0] || null,
      activePlaylistId: matchingSchedules[0]?.playlist_id || this.defaultPlaylistId,
      nextSchedule,
      nextSwitchTime,
    };

    this.lastEvaluation = result;
    return result;
  }

  /**
   * 计算到下一个调度开始的时间（秒）
   */
  private calculateTimeUntilNext(
    schedule: ScheduleData,
    currentTotalSeconds: number,
    currentDayBit: number,
    now: Date
  ): number | null {
    const startSeconds = this.timeToSeconds(schedule.start_time);

    // 检查今天是否匹配
    if (schedule.days_of_week & currentDayBit) {
      // 今天还有效
      if (startSeconds > currentTotalSeconds) {
        return startSeconds - currentTotalSeconds;
      }
    }

    // 找下一个匹配的日期
    for (let i = 1; i <= 7; i++) {
      const futureDate = new Date(now);
      futureDate.setDate(futureDate.getDate() + i);
      const futureDay = futureDate.getDay();
      const futureDayBit = futureDay === 0 ? 64 : 1 << (futureDay - 1);

      if (schedule.days_of_week & futureDayBit) {
        // 计算到那一天的时间
        const secondsUntilMidnight = (24 * 3600) - currentTotalSeconds;
        const fullDaysSeconds = (i - 1) * 24 * 3600;
        return secondsUntilMidnight + fullDaysSeconds + startSeconds;
      }
    }

    return null;  // 没有匹配的日期
  }

  /**
   * 将时间字符串转换为秒数
   */
  private timeToSeconds(time: string): number {
    const [hours, minutes, seconds] = time.split(':').map(Number);
    return hours * 3600 + minutes * 60 + (seconds || 0);
  }

  /**
   * 获取默认播放列表 ID
   */
  getDefaultPlaylistId(): number | null {
    return this.defaultPlaylistId;
  }

  /**
   * 获取最后一次评估结果
   */
  getLastEvaluation(): ScheduleEvaluationResult | null {
    return this.lastEvaluation;
  }

  /**
   * 检查是否需要切换播放列表
   */
  shouldSwitchPlaylist(currentPlaylistId: number | null): { shouldSwitch: boolean; newPlaylistId: number | null; scheduleId: number | null } {
    const result = this.evaluate();

    if (result.activePlaylistId === null) {
      return { shouldSwitch: false, newPlaylistId: null, scheduleId: null };
    }

    const shouldSwitch = currentPlaylistId !== result.activePlaylistId;
    return {
      shouldSwitch,
      newPlaylistId: shouldSwitch ? result.activePlaylistId : null,
      scheduleId: result.activeSchedule?.id || null,
    };
  }

  /**
   * 获取下一次切换的时间（用于设置定时器）
   */
  getNextSwitchTime(): Date | null {
    return this.lastEvaluation?.nextSwitchTime || null;
  }

  /**
   * 计算到下一次切换的毫秒数
   */
  getMsUntilNextSwitch(): number | null {
    const nextTime = this.getNextSwitchTime();
    if (!nextTime) return null;

    const ms = nextTime.getTime() - this.getCurrentTime().getTime();
    return ms > 0 ? ms : null;
  }
}

// 单例导出
export const scheduleEvaluator = new ScheduleEvaluator();
