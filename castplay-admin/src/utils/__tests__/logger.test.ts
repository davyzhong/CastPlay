/**
 * Tests for Logger Utility
 */
import { Logger, logger, apiLogger, wsLogger, uiLogger } from '../utils/logger';

describe('Logger', () => {
  beforeEach(() => {
    // 清除所有 mock
    jest.clearAllMocks();
  });

  describe('Initialization', () => {
    it('should create logger with default settings', () => {
      const testLogger = new Logger();
      expect(testLogger).toBeDefined();
    });

    it('should accept custom enabled and level settings', () => {
      const testLogger = new Logger(true, 'debug');
      expect(testLogger).toBeDefined();
    });
  });

  describe('Logging Methods', () => {
    let testLogger: Logger;
    let consoleSpy: jest.SpyInstance;

    beforeEach(() => {
      testLogger = new Logger(true, 'debug');
      consoleSpy = jest.spyOn(console, 'debug').mockImplementation();
    });

    afterEach(() => {
      consoleSpy.mockRestore();
    });

    it('should log debug messages when enabled', () => {
      testLogger.debug('test message');
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should include timestamp in logs', () => {
      testLogger.debug('test message');
      const callArgs = consoleSpy.mock.calls[0][0];
      expect(callArgs).toMatch(/\[DEBUG\]/);
      expect(callArgs).toMatch(/\d{4}-\d{2}-\d{2}T/);
    });

    it('should format message with prefix', () => {
      testLogger.debug('test message');
      const callArgs = consoleSpy.mock.calls[0][0];
      expect(callArgs).toContain('[DEBUG]');
    });
  });

  describe('Log Levels', () => {
    it('should respect log level hierarchy', () => {
      const warnLogger = new Logger(true, 'warn');
      const warnSpy = jest.spyOn(console, 'warn').mockImplementation();
      const infoSpy = jest.spyOn(console, 'info').mockImplementation();

      warnLogger.warn('warning');
      warnLogger.info('info');

      expect(warnSpy).toHaveBeenCalled();
      expect(infoSpy).not.toHaveBeenCalled();

      warnSpy.mockRestore();
      infoSpy.mockRestore();
    });

    it('should allow all levels when set to debug', () => {
      const debugLogger = new Logger(true, 'debug');
      const debugSpy = jest.spyOn(console, 'debug').mockImplementation();
      const infoSpy = jest.spyOn(console, 'info').mockImplementation();
      const warnSpy = jest.spyOn(console, 'warn').mockImplementation();
      const errorSpy = jest.spyOn(console, 'error').mockImplementation();

      debugLogger.debug('debug');
      debugLogger.info('info');
      debugLogger.warn('warn');
      debugLogger.error('error');

      expect(debugSpy).toHaveBeenCalled();
      expect(infoSpy).toHaveBeenCalled();
      expect(warnSpy).toHaveBeenCalled();
      expect(errorSpy).toHaveBeenCalled();

      debugSpy.mockRestore();
      infoSpy.mockRestore();
      warnSpy.mockRestore();
      errorSpy.mockRestore();
    });
  });

  describe('Disabled Logger', () => {
    it('should not log anything when disabled', () => {
      const disabledLogger = new Logger(false, 'debug');
      const spy = jest.spyOn(console, 'debug').mockImplementation();

      disabledLogger.debug('test');

      expect(spy).not.toHaveBeenCalled();
      spy.mockRestore();
    });
  });

  describe('Pre-configured Loggers', () => {
    it('should export default logger', () => {
      expect(logger).toBeDefined();
      expect(logger instanceof Logger).toBe(true);
    });

    it('should export apiLogger', () => {
      expect(apiLogger).toBeDefined();
      expect(apiLogger instanceof Logger).toBe(true);
    });

    it('should export wsLogger', () => {
      expect(wsLogger).toBeDefined();
      expect(wsLogger instanceof Logger).toBe(true);
    });

    it('should export uiLogger', () => {
      expect(uiLogger).toBeDefined();
      expect(uiLogger instanceof Logger).toBe(true);
    });
  });

  describe('Error Logging', () => {
    it('should always log errors regardless级别', () => {
      const errorLogger = new Logger(true, 'error');
      const errorSpy = jest.spyOn(console, 'error').mockImplementation();

      errorLogger.error('error message');

      expect(errorSpy).toHaveBeenCalled();
      errorSpy.mockRestore();
    });

    it('should support additional arguments', () => {
      const debugLogger = new Logger(true, 'debug');
      const spy = jest.spyOn(console, 'debug').mockImplementation();

      const errorObj = new Error('test error');
      debugLogger.debug('error occurred', errorObj, { extra: 'data' });

      expect(spy).toHaveBeenCalledWith(
        expect.stringContaining('[DEBUG]'),
        'error occurred',
        errorObj,
        { extra: 'data' }
      );

      spy.mockRestore();
    });
  });
});
