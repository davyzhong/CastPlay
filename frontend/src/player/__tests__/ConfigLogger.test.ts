/**
 * 配置日志服务单元测试
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { ConfigLogger, configLogger as importedLogger } from '../services/ConfigLogger';

describe('ConfigLogger', () => {
  // 获取 ConfigLogger 类本身（通过实例的构造函数）
  const ConfigLoggerClass = importedLogger.constructor as typeof ConfigLogger;
  let configLogger: ConfigLogger;

  beforeEach(() => {
    vi.clearAllMocks();

    // Reset singleton
    (ConfigLoggerClass as any).instance = undefined;
    configLogger = ConfigLoggerClass.getInstance();
    configLogger.clearLogs();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('getInstance', () => {
    it('应该返回单例实例', () => {
      const instance1 = ConfigLoggerClass.getInstance();
      const instance2 = ConfigLoggerClass.getInstance();
      expect(instance1).toBe(instance2);
    });
  });

  describe('init', () => {
    it('应该使用默认选项初始化', () => {
      const consoleSpy = vi.spyOn(console, 'info').mockImplementation();

      configLogger.init();

      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('[ConfigLogger]'),
        'Logger initialized',
        expect.any(String)
      );

      consoleSpy.mockRestore();
    });

    it('应该设置设备 ID', () => {
      configLogger.init({ deviceId: 'device-123', logToConsole: false });

      const exported = configLogger.exportLogs();
      const data = JSON.parse(exported);
      expect(data.deviceId).toBe('device-123');
    });
  });

  describe('基本日志方法', () => {
    beforeEach(() => {
      configLogger.init({ logToConsole: false });
      configLogger.clearLogs();
    });

    it('debug 应该记录调试级别日志', () => {
      configLogger.debug('TestCategory', 'Test message', { value: 'test-value' });

      const logs = configLogger.getLogs();
      expect(logs.length).toBeGreaterThan(0);
      const lastLog = logs[logs.length - 1];
      expect(lastLog.level).toBe('debug');
      expect(lastLog.category).toBe('TestCategory');
      expect(lastLog.message).toBe('Test message');
      expect(lastLog.data).toEqual({ value: 'test-value' });
    });

    it('info 应该记录信息级别日志', () => {
      configLogger.info('TestCategory', 'Test message');

      const logs = configLogger.getLogs();
      expect(logs.length).toBeGreaterThan(0);
      const lastLog = logs[logs.length - 1];
      expect(lastLog.level).toBe('info');
    });

    it('warn 应该记录警告级别日志', () => {
      configLogger.warn('TestCategory', 'Test message');

      const logs = configLogger.getLogs();
      expect(logs.length).toBeGreaterThan(0);
      const lastLog = logs[logs.length - 1];
      expect(lastLog.level).toBe('warn');
    });

    it('error 应该记录错误级别日志', () => {
      const testError = new Error('Test error');
      configLogger.error('TestCategory', 'Test message', testError);

      const logs = configLogger.getLogs();
      expect(logs.length).toBeGreaterThan(0);
      const lastLog = logs[logs.length - 1];
      expect(lastLog.level).toBe('error');
      expect(lastLog.error).toBe(testError);
    });
  });

  describe('配置操作日志方法', () => {
    beforeEach(() => {
      configLogger.init({ logToConsole: false });
      configLogger.clearLogs();
    });

    describe('logServerConfig', () => {
      it('应该记录服务器配置操作', () => {
        configLogger.logServerConfig('save', { address: '192.168.1.100' });

        const logs = configLogger.getLogsByCategory('ServerConfig');
        expect(logs.length).toBeGreaterThan(0);
        expect(logs[logs.length - 1].message).toContain('save');
      });
    });

    describe('logDeviceRegistration', () => {
      it('应该记录设备注册操作', () => {
        configLogger.logDeviceRegistration('complete', { deviceId: 'device-123' });

        const logs = configLogger.getLogsByCategory('DeviceRegistration');
        expect(logs.length).toBeGreaterThan(0);
        expect(logs[logs.length - 1].message).toContain('complete');
      });

      it('应该用 error 级别记录失败操作', () => {
        configLogger.logDeviceRegistration('fail', { error: 'Network error' });

        const logs = configLogger.getLogsByCategory('DeviceRegistration');
        expect(logs[logs.length - 1].level).toBe('error');
      });
    });

    describe('logRegistrationCode', () => {
      it('应该记录注册码操作', () => {
        configLogger.logRegistrationCode('display');

        const logs = configLogger.getLogsByCategory('RegistrationCode');
        expect(logs.length).toBeGreaterThan(0);
        expect(logs[logs.length - 1].message).toContain('display');
      });
    });

    describe('logPlaylistSelection', () => {
      it('应该记录播放列表选择操作', () => {
        configLogger.logPlaylistSelection('confirm', { count: 3 });

        const logs = configLogger.getLogsByCategory('PlaylistSelection');
        expect(logs.length).toBeGreaterThan(0);
        expect(logs[logs.length - 1].message).toContain('confirm');
      });
    });

    describe('logStorage', () => {
      it('应该记录存储操作', () => {
        configLogger.logStorage('set', 'test-key', { value: 'test' });

        const logs = configLogger.getLogsByCategory('Storage');
        expect(logs.length).toBeGreaterThan(0);
        expect(logs[logs.length - 1].message).toContain('set');
        expect(logs[logs.length - 1].message).toContain('test-key');
      });
    });

    describe('logNetwork', () => {
      it('应该记录网络请求', () => {
        configLogger.logNetwork('request', { url: '/api/health' });

        const logs = configLogger.getLogsByCategory('Network');
        expect(logs.length).toBeGreaterThan(0);
        expect(logs[logs.length - 1].level).toBe('debug');
      });

      it('应该用 error 级别记录网络错误', () => {
        configLogger.logNetwork('error', { error: 'Connection timeout' });

        const logs = configLogger.getLogsByCategory('Network');
        expect(logs[logs.length - 1].level).toBe('error');
      });
    });
  });

  describe('敏感数据清理', () => {
    beforeEach(() => {
      configLogger.init({ logToConsole: false });
      configLogger.clearLogs();
    });

    it('应该清理密码字段', () => {
      configLogger.info('Test', 'Test message', {
        username: 'user',
        password: 'secret123',
      });

      const logs = configLogger.getLogs();
      const lastLog = logs[logs.length - 1];
      expect(lastLog.data?.password).toBe('***REDACTED***');
      expect(lastLog.data?.username).toBe('user');
    });

    it('应该清理 token 字段', () => {
      configLogger.info('Test', 'Test message', {
        accessToken: 'abc123',
        refreshToken: 'xyz789',
      });

      const logs = configLogger.getLogs();
      const lastLog = logs[logs.length - 1];
      expect(lastLog.data?.accessToken).toBe('***REDACTED***');
      expect(lastLog.data?.refreshToken).toBe('***REDACTED***');
    });

    it('应该清理包含 secret 的字段', () => {
      configLogger.info('Test', 'Test message', {
        apiKey: 'key123',
        clientSecret: 'secret123',
      });

      const logs = configLogger.getLogs();
      const lastLog = logs[logs.length - 1];
      expect(lastLog.data?.apiKey).toBe('***REDACTED***');
      expect(lastLog.data?.clientSecret).toBe('***REDACTED***');
    });
  });

  describe('日志管理', () => {
    beforeEach(() => {
      configLogger.init({ logToConsole: false });
      configLogger.clearLogs();
    });

    describe('getLogs', () => {
      it('应该返回所有日志的副本', () => {
        configLogger.info('Test', 'Message 1');
        configLogger.info('Test', 'Message 2');

        const logs = configLogger.getLogs();
        expect(logs.length).toBeGreaterThanOrEqual(2);
      });
    });

    describe('getLogsByLevel', () => {
      it('应该过滤指定级别的日志', () => {
        configLogger.debug('Test', 'Debug');
        configLogger.info('Test', 'Info');
        configLogger.warn('Test', 'Warn');
        configLogger.error('Test', 'Error');

        const errorLogs = configLogger.getLogsByLevel('error');
        expect(errorLogs.length).toBeGreaterThan(0);
        expect(errorLogs.every((l) => l.level === 'error')).toBe(true);
      });
    });

    describe('getLogsByCategory', () => {
      it('应该过滤指定类别的日志', () => {
        configLogger.info('CategoryA', 'Message 1');
        configLogger.info('CategoryB', 'Message 2');
        configLogger.info('CategoryA', 'Message 3');

        const categoryALogs = configLogger.getLogsByCategory('CategoryA');
        expect(categoryALogs.length).toBeGreaterThanOrEqual(2);
      });
    });

    describe('clearLogs', () => {
      it('应该清除日志', () => {
        configLogger.info('Test', 'Message 1');
        configLogger.info('Test', 'Message 2');

        configLogger.clearLogs();

        // clearLogs itself adds a log
        const logs = configLogger.getLogs();
        expect(logs.length).toBe(1);
      });
    });
  });

  describe('导出功能', () => {
    beforeEach(() => {
      configLogger.init({ logToConsole: false, deviceId: 'test-device' });
      configLogger.clearLogs();
    });

    describe('exportLogs', () => {
      it('应该导出包含元数据的 JSON', () => {
        configLogger.info('Test', 'Message');

        const exported = configLogger.exportLogs();
        const data = JSON.parse(exported);

        expect(data.deviceId).toBe('test-device');
        expect(data.exportedAt).toBeDefined();
        expect(data.userAgent).toBeDefined();
        expect(data.url).toBeDefined();
        expect(Array.isArray(data.logs)).toBe(true);
      });
    });

    describe('downloadLogs', () => {
      it('应该创建下载链接', () => {
        const createElementSpy = vi.spyOn(document, 'createElement');
        const appendChildSpy = vi.spyOn(document.body, 'appendChild');
        const removeChildSpy = vi.spyOn(document.body, 'removeChild');

        configLogger.downloadLogs();

        expect(createElementSpy).toHaveBeenCalledWith('a');
        expect(appendChildSpy).toHaveBeenCalled();
        expect(removeChildSpy).toHaveBeenCalled();

        createElementSpy.mockRestore();
        appendChildSpy.mockRestore();
        removeChildSpy.mockRestore();
      });
    });

    describe('getStats', () => {
      it('应该返回日志统计信息', () => {
        configLogger.debug('CatA', 'Debug');
        configLogger.info('CatA', 'Info');
        configLogger.warn('CatB', 'Warn');
        configLogger.error('CatB', 'Error');
        configLogger.error('CatB', 'Error 2');

        const stats = configLogger.getStats();

        expect(stats.byLevel.debug).toBeGreaterThanOrEqual(1);
        expect(stats.byLevel.info).toBeGreaterThanOrEqual(1);
        expect(stats.byLevel.warn).toBeGreaterThanOrEqual(1);
        expect(stats.byLevel.error).toBeGreaterThanOrEqual(2);
        expect(stats.oldestTimestamp).toBeDefined();
        expect(stats.newestTimestamp).toBeDefined();
      });
    });
  });

  describe('setEnabled', () => {
    it('禁用后不应该记录日志', () => {
      configLogger.init({ logToConsole: false });
      configLogger.setEnabled(false);
      configLogger.clearLogs();

      configLogger.info('Test', 'Message');

      const logs = configLogger.getLogs();
      // clearLogs still adds a log when enabled, but after disable no new logs
      expect(logs.every((l) => l.message !== 'Message')).toBe(true);
    });
  });

  describe('setDeviceId', () => {
    it('应该更新设备 ID', () => {
      configLogger.init({ logToConsole: false });
      configLogger.setDeviceId('new-device-id');

      const exported = configLogger.exportLogs();
      const data = JSON.parse(exported);
      expect(data.deviceId).toBe('new-device-id');
    });
  });
});
