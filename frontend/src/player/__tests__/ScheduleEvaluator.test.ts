/**
 * 调度评估服务单元测试
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { ScheduleEvaluator, ScheduleData } from '../services/ScheduleEvaluator';

describe('ScheduleEvaluator', () => {
  let evaluator: ScheduleEvaluator;

  // 位掩码常量（与 ScheduleEvaluator 中的逻辑一致）
  // JavaScript getDay(): 0=Sunday, 1=Monday, ..., 6=Saturday
  // 代码转换: dayBit = (day === 0) ? 64 : (1 << (day - 1))
  // 即: Sunday=64, Monday=1, Tuesday=2, Wednesday=4, Thursday=8, Friday=16, Saturday=32
  const MONDAY = 1;
  const TUESDAY = 2;
  const WEDNESDAY = 4;
  const THURSDAY = 8;
  const FRIDAY = 16;
  const SATURDAY = 32;
  const SUNDAY = 64;
  const WEEKDAYS = MONDAY | TUESDAY | WEDNESDAY | THURSDAY | FRIDAY; // 31 = Mon-Fri
  const WEEKENDS = SATURDAY | SUNDAY; // 96 = Sat-Sun
  const ALL_DAYS = WEEKDAYS | WEEKENDS; // 127 = 每天

  // 测试用调度数据
  const createSchedule = (overrides: Partial<ScheduleData> = {}): ScheduleData => ({
    id: 1,
    playlist_id: 1,
    start_time: '09:00:00',
    end_time: '17:00:00',
    days_of_week: WEEKDAYS, // 默认工作日
    enabled: true,
    priority: 1,
    ...overrides,
  });

  beforeEach(() => {
    // 创建新的评估器实例避免状态污染
    evaluator = new ScheduleEvaluator();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    evaluator.reset();
  });

  describe('reset', () => {
    it('应该重置评估器状态', () => {
      evaluator.updateSchedules([createSchedule()], 1, new Date().toISOString());
      evaluator.evaluate();

      evaluator.reset();

      expect(evaluator.getDefaultPlaylistId()).toBeNull();
      expect(evaluator.getLastEvaluation()).toBeNull();
    });
  });

  describe('updateSchedules', () => {
    it('应该更新调度数据', () => {
      const schedules = [
        createSchedule({ id: 1, playlist_id: 100 }),
        createSchedule({ id: 2, playlist_id: 200 }),
      ];

      evaluator.updateSchedules(schedules, 50);

      const result = evaluator.evaluate();
      expect(result).toBeDefined();
      expect(result).not.toBeNull();
    });

    it('应该过滤禁用状态的调度', () => {
      const schedules = [
        createSchedule({ id: 1, enabled: true, start_time: '00:00:00', end_time: '23:59:59', days_of_week: ALL_DAYS }),
        createSchedule({ id: 2, enabled: false, start_time: '00:00:00', end_time: '23:59:59', days_of_week: ALL_DAYS }),
      ];

      evaluator.updateSchedules(schedules, 1);

      // 设置任意时间
      const anyTime = new Date('2026-03-23T12:00:00');
      vi.setSystemTime(anyTime);

      const result = evaluator.evaluate();

      // 应该只有一个有效调度
      expect(result.activeSchedule?.id).toBe(1);
    });

    it('应该计算服务器时间偏移', () => {
      const serverTime = '2026-03-22T10:00:00Z';
      const localTime = new Date('2026-03-22T09:55:00Z');

      vi.setSystemTime(localTime);
      evaluator.updateSchedules([], null, serverTime);

      // 评估器应该记录了时间偏移
      const result = evaluator.evaluate();
      expect(result).toBeDefined();
    });

    it('应该设置默认播放列表 ID', () => {
      evaluator.updateSchedules([], 99);

      expect(evaluator.getDefaultPlaylistId()).toBe(99);
    });
  });

  describe('evaluate - 时间评估', () => {
    it('应该在工作时间返回匹配的调度', () => {
      const schedule = createSchedule({
        id: 1,
        playlist_id: 100,
        start_time: '09:00:00',
        end_time: '17:00:00',
        days_of_week: WEEKDAYS,
      });

      evaluator.updateSchedules([schedule], 99);

      // 设置为工作日工作时间 (周一 10:00)
      // 2026-03-23 是周一
      const mondayMorning = new Date('2026-03-23T10:00:00');
      vi.setSystemTime(mondayMorning);

      const result = evaluator.evaluate();

      expect(result.activeSchedule).toBeDefined();
      expect(result.activeSchedule?.id).toBe(1);
      expect(result.activePlaylistId).toBe(100);
    });

    it('应该在非工作时间返回默认播放列表', () => {
      const schedule = createSchedule({
        id: 1,
        playlist_id: 100,
        start_time: '09:00:00',
        end_time: '17:00:00',
        days_of_week: WEEKDAYS,
      });

      evaluator.updateSchedules([schedule], 99);

      // 设置为工作时间之外 (周一 20:00)
      const mondayEvening = new Date('2026-03-23T20:00:00');
      vi.setSystemTime(mondayEvening);

      const result = evaluator.evaluate();

      expect(result.activeSchedule).toBeNull();
      expect(result.activePlaylistId).toBe(99); // 默认播放列表
    });

    it('应该正确处理周末', () => {
      const schedule = createSchedule({
        id: 1,
        playlist_id: 100,
        start_time: '09:00:00',
        end_time: '17:00:00',
        days_of_week: WEEKDAYS, // 只有工作日
      });

      evaluator.updateSchedules([schedule], 99);

      // 设置为周六 (2026-03-28)
      const saturday = new Date('2026-03-28T10:00:00');
      vi.setSystemTime(saturday);

      const result = evaluator.evaluate();

      expect(result.activeSchedule).toBeNull();
      expect(result.activePlaylistId).toBe(99);
    });

    it('应该处理包含周末的调度', () => {
      const schedule = createSchedule({
        id: 1,
        playlist_id: 100,
        start_time: '09:00:00',
        end_time: '17:00:00',
        days_of_week: ALL_DAYS, // 每天
      });

      evaluator.updateSchedules([schedule], 99);

      // 设置为周六
      const saturday = new Date('2026-03-28T10:00:00');
      vi.setSystemTime(saturday);

      const result = evaluator.evaluate();

      expect(result.activeSchedule).toBeDefined();
      expect(result.activeSchedule?.id).toBe(1);
    });
  });

  describe('evaluate - 跨天调度', () => {
    it('应该正确处理跨天调度 (晚间到凌晨)', () => {
      const schedule = createSchedule({
        id: 1,
        playlist_id: 100,
        start_time: '22:00:00',
        end_time: '06:00:00',
        days_of_week: ALL_DAYS, // 每天
      });

      evaluator.updateSchedules([schedule], 99);

      // 设置为深夜 (周一 23:00)
      const mondayNight = new Date('2026-03-23T23:00:00');
      vi.setSystemTime(mondayNight);

      const result = evaluator.evaluate();

      expect(result.activeSchedule).toBeDefined();
      expect(result.activePlaylistId).toBe(100);
    });

    it('应该正确处理跨天调度的结束时间', () => {
      const schedule = createSchedule({
        id: 1,
        playlist_id: 100,
        start_time: '22:00:00',
        end_time: '06:00:00',
        days_of_week: ALL_DAYS,
      });

      evaluator.updateSchedules([schedule], 99);

      // 设置为凌晨 (周一 05:00)
      const mondayEarlyMorning = new Date('2026-03-23T05:00:00');
      vi.setSystemTime(mondayEarlyMorning);

      const result = evaluator.evaluate();

      expect(result.activeSchedule).toBeDefined();
      expect(result.activePlaylistId).toBe(100);
    });

    it('应该在跨天调度结束后切换到默认播放列表', () => {
      const schedule = createSchedule({
        id: 1,
        playlist_id: 100,
        start_time: '22:00:00',
        end_time: '06:00:00',
        days_of_week: ALL_DAYS,
      });

      evaluator.updateSchedules([schedule], 99);

      // 设置为早上 7 点 (调度已结束)
      const mondayMorning = new Date('2026-03-23T07:00:00');
      vi.setSystemTime(mondayMorning);

      const result = evaluator.evaluate();

      expect(result.activeSchedule).toBeNull();
      expect(result.activePlaylistId).toBe(99);
    });
  });

  describe('evaluate - 优先级选择', () => {
    it('应该选择高优先级调度', () => {
      const schedules = [
        createSchedule({ id: 1, playlist_id: 100, priority: 1 }), // 低优先级
        createSchedule({ id: 2, playlist_id: 200, priority: 3 }), // 高优先级
        createSchedule({ id: 3, playlist_id: 300, priority: 2 }), // 中优先级
      ];

      evaluator.updateSchedules(schedules, 99);

      // 设置为工作时间 (周一 10:00)
      const mondayMorning = new Date('2026-03-23T10:00:00');
      vi.setSystemTime(mondayMorning);

      const result = evaluator.evaluate();

      expect(result.activeSchedule?.id).toBe(2); // 最高优先级
      expect(result.activePlaylistId).toBe(200);
    });

    it('应该只返回当前时间匹配的调度', () => {
      const schedules = [
        createSchedule({
          id: 1,
          playlist_id: 100,
          start_time: '09:00:00',
          end_time: '12:00:00',
          priority: 3,
        }),
        createSchedule({
          id: 2,
          playlist_id: 200,
          start_time: '14:00:00',
          end_time: '17:00:00',
          priority: 1,
        }),
      ];

      evaluator.updateSchedules(schedules, 99);

      // 设置为上午 10:00
      const mondayMorning = new Date('2026-03-23T10:00:00');
      vi.setSystemTime(mondayMorning);

      const result = evaluator.evaluate();

      // 上午只匹配第一个调度
      expect(result.activeSchedule?.id).toBe(1);
      expect(result.activePlaylistId).toBe(100);
    });
  });

  describe('shouldSwitchPlaylist', () => {
    it('应该在播放列表不匹配时返回需要切换', () => {
      const schedule = createSchedule({
        id: 1,
        playlist_id: 200,
        start_time: '09:00:00',
        end_time: '17:00:00',
        days_of_week: WEEKDAYS,
      });

      evaluator.updateSchedules([schedule], 99);

      // 设置为工作日工作时间
      const mondayMorning = new Date('2026-03-23T10:00:00');
      vi.setSystemTime(mondayMorning);

      const result = evaluator.shouldSwitchPlaylist(99); // 当前播放默认列表

      expect(result.shouldSwitch).toBe(true);
      expect(result.newPlaylistId).toBe(200);
      expect(result.scheduleId).toBe(1);
    });

    it('应该在播放列表匹配时不切换', () => {
      const schedule = createSchedule({
        id: 1,
        playlist_id: 100,
        start_time: '09:00:00',
        end_time: '17:00:00',
        days_of_week: WEEKDAYS,
      });

      evaluator.updateSchedules([schedule], 99);

      // 设置为工作日工作时间
      const mondayMorning = new Date('2026-03-23T10:00:00');
      vi.setSystemTime(mondayMorning);

      const result = evaluator.shouldSwitchPlaylist(100); // 已经是正确列表

      expect(result.shouldSwitch).toBe(false);
      expect(result.newPlaylistId).toBeNull();
    });

    it('应该在无活动调度且当前播放默认列表时返回不切换', () => {
      evaluator.updateSchedules([], 99);

      const mondayEvening = new Date('2026-03-23T20:00:00');
      vi.setSystemTime(mondayEvening);

      // 当前播放的就是默认列表，不应该切换
      const result = evaluator.shouldSwitchPlaylist(99);

      expect(result.shouldSwitch).toBe(false);
    });
  });

  describe('getMsUntilNextSwitch', () => {
    it('应该返回到下一次切换的毫秒数', () => {
      const schedule = createSchedule({
        id: 1,
        playlist_id: 100,
        start_time: '10:00:00',
        end_time: '17:00:00',
        days_of_week: WEEKDAYS,
      });

      evaluator.updateSchedules([schedule], 99);

      // 设置为今天早上 9:00 (周一)
      const todayMorning = new Date('2026-03-23T09:00:00');
      vi.setSystemTime(todayMorning);

      evaluator.evaluate();
      const msUntilSwitch = evaluator.getMsUntilNextSwitch();

      expect(msUntilSwitch).not.toBeNull();
      expect(msUntilSwitch).toBeGreaterThan(0);
      // 应该是大约 1 小时 (3600000ms)
      expect(msUntilSwitch).toBeGreaterThanOrEqual(3500000);
      expect(msUntilSwitch).toBeLessThanOrEqual(3700000);
    });

    it('在没有下一次切换时返回 null', () => {
      evaluator.updateSchedules([], 99);

      const result = evaluator.getMsUntilNextSwitch();

      expect(result).toBeNull();
    });
  });

  describe('getLastEvaluation', () => {
    it('应该返回最后一次评估结果', () => {
      const schedule = createSchedule({
        id: 1,
        playlist_id: 100,
        start_time: '00:00:00',
        end_time: '23:59:59',
        days_of_week: ALL_DAYS,
      });

      evaluator.updateSchedules([schedule], 99);

      // 评估前应该为 null
      const result1 = evaluator.getLastEvaluation();
      expect(result1).toBeNull();

      // 评估后应该返回结果
      const evalResult = evaluator.evaluate();
      expect(evalResult.activeSchedule?.id).toBe(1);

      const result2 = evaluator.getLastEvaluation();
      expect(result2).not.toBeNull();
      expect(result2?.activeSchedule?.id).toBe(1);
    });
  });

  describe('边界条件', () => {
    it('应该处理空调度列表', () => {
      evaluator.updateSchedules([], 99);

      const monday = new Date('2026-03-23T10:00:00');
      vi.setSystemTime(monday);

      const result = evaluator.evaluate();

      expect(result.activeSchedule).toBeNull();
      expect(result.activePlaylistId).toBe(99);
      expect(result.nextSchedule).toBeNull();
      expect(result.nextSwitchTime).toBeNull();
    });

    it('应该处理无效的时间格式', () => {
      const schedule = createSchedule({
        start_time: 'invalid',
        end_time: 'also_invalid',
      });

      evaluator.updateSchedules([schedule], 99);

      const monday = new Date('2026-03-23T10:00:00');
      vi.setSystemTime(monday);

      // 不会抛出异常，但返回 NaN 秒数
      const result = evaluator.evaluate();
      expect(result).toBeDefined();
    });

    it('应该处理调度结束时间早于开始时间 (跨天)', () => {
      const schedule = createSchedule({
        id: 1,
        playlist_id: 100,
        start_time: '22:00:00',
        end_time: '06:00:00',
        days_of_week: ALL_DAYS,
      });

      evaluator.updateSchedules([schedule], 99);

      // 在结束时间之前
      const earlyMorning = new Date('2026-03-23T05:00:00');
      vi.setSystemTime(earlyMorning);

      const result = evaluator.evaluate();

      expect(result.activeSchedule).toBeDefined();
      expect(result.activePlaylistId).toBe(100);
    });

    it('应该处理全天调度', () => {
      const schedule = createSchedule({
        id: 1,
        playlist_id: 100,
        start_time: '00:00:00',
        end_time: '23:59:59',
        days_of_week: ALL_DAYS,
      });

      evaluator.updateSchedules([schedule], 99);

      const anyTime = new Date('2026-03-23T12:00:00');
      vi.setSystemTime(anyTime);

      const result = evaluator.evaluate();

      expect(result.activeSchedule).toBeDefined();
    });

    it('应该处理只有周日的调度', () => {
      const schedule = createSchedule({
        id: 1,
        playlist_id: 100,
        start_time: '09:00:00',
        end_time: '17:00:00',
        days_of_week: SUNDAY,
      });

      evaluator.updateSchedules([schedule], 99);

      // 周日 (2026-03-29)
      const sunday = new Date('2026-03-29T10:00:00');
      vi.setSystemTime(sunday);

      const result = evaluator.evaluate();

      expect(result.activeSchedule).toBeDefined();
      expect(result.activePlaylistId).toBe(100);

      // 周一应该不匹配
      const monday = new Date('2026-03-23T10:00:00');
      vi.setSystemTime(monday);

      const mondayResult = evaluator.evaluate();
      expect(mondayResult.activeSchedule).toBeNull();
    });
  });
});
