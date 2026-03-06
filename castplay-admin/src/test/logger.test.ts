/**
 * Logger 工具函数测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { logger, apiLogger, uiLogger } from '../utils/logger'

describe('Logger', () => {
  beforeEach(() => {
    vi.spyOn(console, 'debug').mockImplementation(() => {})
    vi.spyOn(console, 'info').mockImplementation(() => {})
    vi.spyOn(console, 'warn').mockImplementation(() => {})
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  it('should create logger instance', () => {
    expect(logger).toBeDefined()
    expect(logger.debug).toBeDefined()
    expect(logger.info).toBeDefined()
    expect(logger.warn).toBeDefined()
    expect(logger.error).toBeDefined()
  })

  it('should log debug messages in development mode', () => {
    logger.debug('Test debug message')
    expect(console.debug).toHaveBeenCalled()
  })

  it('should log info messages', () => {
    logger.info('Test info message')
    expect(console.info).toHaveBeenCalled()
  })

  it('should log warning messages', () => {
    logger.warn('Test warning message')
    expect(console.warn).toHaveBeenCalled()
  })

  it('should log error messages', () => {
    logger.error('Test error message')
    expect(console.error).toHaveBeenCalled()
  })

  it('should accept additional arguments', () => {
    const data = { key: 'value' }
    logger.info('Message with data', data)
    expect(console.info).toHaveBeenCalledWith(
      expect.stringContaining('[INFO]'),
      data
    )
  })
})

describe('API Logger', () => {
  beforeEach(() => {
    vi.spyOn(console, 'debug').mockImplementation(() => {})
    vi.spyOn(console, 'info').mockImplementation(() => {})
    vi.spyOn(console, 'warn').mockImplementation(() => {})
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  it('should create apiLogger instance', () => {
    expect(apiLogger).toBeDefined()
  })

  it('should log API related messages', () => {
    apiLogger.info('API request started')
    expect(console.info).toHaveBeenCalled()
  })
})

describe('UI Logger', () => {
  beforeEach(() => {
    vi.spyOn(console, 'debug').mockImplementation(() => {})
    vi.spyOn(console, 'info').mockImplementation(() => {})
    vi.spyOn(console, 'warn').mockImplementation(() => {})
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  it('should create uiLogger instance', () => {
    expect(uiLogger).toBeDefined()
  })

  it('should log warning messages', () => {
    uiLogger.warn('UI warning message')
    expect(console.warn).toHaveBeenCalled()
  })

  it('should log error messages', () => {
    uiLogger.error('UI error message')
    expect(console.error).toHaveBeenCalled()
  })
})
