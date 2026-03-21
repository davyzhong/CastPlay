/**
 * 测试环境配置
 */
import '@testing-library/jest-dom'
import { vi, afterEach } from 'vitest'

// 模拟 window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// 模拟 ResizeObserver - 使用 class 语法
class MockResizeObserver {
  observe = vi.fn()
  unobserve = vi.fn()
  disconnect = vi.fn()
}
global.ResizeObserver = MockResizeObserver as unknown as typeof ResizeObserver

// 模拟 IntersectionObserver - 使用 class 语法
class MockIntersectionObserver {
  observe = vi.fn()
  unobserve = vi.fn()
  disconnect = vi.fn()
}
global.IntersectionObserver = MockIntersectionObserver as unknown as typeof IntersectionObserver

// 模拟 WebSocket
class MockWebSocket {
  static CONNECTING = 0
  static OPEN = 1
  static CLOSING = 2
  static CLOSED = 3

  readyState = MockWebSocket.OPEN
  onopen: (() => void) | null = null
  onclose: (() => void) | null = null
  onmessage: ((event: { data: string }) => void) | null = null
  onerror: (() => void) | null = null

  constructor(_url: string) {
    setTimeout(() => {
      this.onopen?.()
    }, 0)
  }

  send(_data: string) {}
  close() {
    this.readyState = MockWebSocket.CLOSED
    this.onclose?.()
  }
}
global.WebSocket = MockWebSocket as unknown as typeof WebSocket

// 模拟 localStorage
const localStorageMock = {
  getItem: vi.fn(() => null),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn(),
}
Object.defineProperty(window, 'localStorage', { value: localStorageMock, writable: true })

// 清除所有 mock
afterEach(() => {
  vi.clearAllMocks()
})
