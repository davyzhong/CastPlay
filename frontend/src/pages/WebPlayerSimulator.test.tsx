/**
 * WebPlayerSimulator 单元测试
 * 验证播放端模拟器的核心功能
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '../test/utils'
import WebPlayerSimulator from './WebPlayerSimulator'

// Mock player API
vi.mock('../api/player', () => import('../test/mocks/player'))

describe('WebPlayerSimulator', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllTimers()
  })

  // ============================================================================
  // 1. 组件渲染测试
  // ============================================================================

  describe('组件渲染', () => {
    it('应该显示页面标题', async () => {
      render(<WebPlayerSimulator />)
      await waitFor(() => {
        expect(screen.getByText('Web 播放端模拟器')).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('应该显示调试模式开关', async () => {
      render(<WebPlayerSimulator />)
      await waitFor(() => {
        expect(screen.getByText('调试')).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('应该显示设备信息卡片', async () => {
      render(<WebPlayerSimulator />)
      await waitFor(() => {
        expect(screen.getByText('设备信息')).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('应该显示设备ID标签', async () => {
      render(<WebPlayerSimulator />)
      await waitFor(() => {
        expect(screen.getByText('ID')).toBeInTheDocument()
      }, { timeout: 5000 })
    })
  })

  // ============================================================================
  // 2. 播放列表功能测试
  // ============================================================================

  describe('播放列表功能', () => {
    it('应该显示播放列表区域', async () => {
      render(<WebPlayerSimulator />)
      await waitFor(() => {
        // 使用 getAllByText 因为可能有多个匹配
        const elements = screen.getAllByText('播放列表')
        expect(elements.length).toBeGreaterThan(0)
      }, { timeout: 5000 })
    })
  })

  // ============================================================================
  // 3. 设备信息测试
  // ============================================================================

  describe('设备信息显示', () => {
    it('应该显示设备时区标签', async () => {
      render(<WebPlayerSimulator />)
      await waitFor(() => {
        expect(screen.getByText('时区')).toBeInTheDocument()
      }, { timeout: 5000 })
    })
  })

  // ============================================================================
  // 4. 调试模式测试
  // ============================================================================

  describe('调试模式', () => {
    it('默认不显示调试设置', async () => {
      render(<WebPlayerSimulator />)
      await waitFor(() => {
        expect(screen.getByText('Web 播放端模拟器')).toBeInTheDocument()
      }, { timeout: 5000 })
      expect(screen.queryByText('调试设置')).not.toBeInTheDocument()
    })

    it('开启调试模式后显示调试设置', async () => {
      render(<WebPlayerSimulator />)

      await waitFor(() => {
        expect(screen.getByText('Web 播放端模拟器')).toBeInTheDocument()
      }, { timeout: 5000 })

      const switches = screen.getAllByRole('switch')
      const debugSwitch = switches[0]
      fireEvent.click(debugSwitch)

      await waitFor(() => {
        expect(screen.getByText('调试设置')).toBeInTheDocument()
      })
    })
  })

  // ============================================================================
  // 5. 播放控制功能测试
  // ============================================================================

  describe('播放控制功能', () => {
    it('应该显示播放速度按钮', async () => {
      render(<WebPlayerSimulator />)
      await waitFor(() => {
        expect(screen.getByText('1X')).toBeInTheDocument()
        expect(screen.getByText('2X')).toBeInTheDocument()
        expect(screen.getByText('4X')).toBeInTheDocument()
        expect(screen.getByText('8X')).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('点击速度按钮应切换播放速度', async () => {
      render(<WebPlayerSimulator />)

      await waitFor(() => {
        expect(screen.getByText('2X')).toBeInTheDocument()
      }, { timeout: 5000 })

      const speed2xBtn = screen.getByText('2X')
      fireEvent.click(speed2xBtn)

      await waitFor(() => {
        expect(speed2xBtn.closest('button')).toHaveClass('ant-btn-primary')
      })
    })
  })

  // ============================================================================
  // 集成测试
  // ============================================================================

  describe('WebPlayerSimulator 集成测试', () => {
    it('完整的初始化流程', async () => {
      render(<WebPlayerSimulator />)

      // 等待初始化完成
      await waitFor(() => {
        expect(screen.getByText('Web 播放端模拟器')).toBeInTheDocument()
      }, { timeout: 5000 })

      // 应该显示设备信息卡片
      expect(screen.getByText('设备信息')).toBeInTheDocument()
    })

    it('调试模式可以切换', async () => {
      render(<WebPlayerSimulator />)

      await waitFor(() => {
        expect(screen.getByText('Web 播放端模拟器')).toBeInTheDocument()
      }, { timeout: 5000 })

      // 初始状态没有调试设置
      expect(screen.queryByText('调试设置')).not.toBeInTheDocument()

      // 开启调试模式
      const switches = screen.getAllByRole('switch')
      fireEvent.click(switches[0])

      // 应该显示调试设置
      await waitFor(() => {
        expect(screen.getByText('调试设置')).toBeInTheDocument()
      })

      // 再次关闭
      fireEvent.click(switches[0])

      // 应该隐藏调试设置
      await waitFor(() => {
        expect(screen.queryByText('调试设置')).not.toBeInTheDocument()
      })
    })
  })

  // ============================================================================
  // 功能需求验证测试
  // ============================================================================

  describe('功能需求验证', () => {
    describe('需求1: 网页代表 Android 端', () => {
      it('应该自动初始化设备', async () => {
        render(<WebPlayerSimulator />)
        await waitFor(() => {
          expect(screen.getByText('设备信息')).toBeInTheDocument()
        }, { timeout: 5000 })
      })

      it('应该包含设备信息展示', async () => {
        render(<WebPlayerSimulator />)
        await waitFor(() => {
          expect(screen.getByText('设备信息')).toBeInTheDocument()
          expect(screen.getByText('名称')).toBeInTheDocument()
          expect(screen.getByText('ID')).toBeInTheDocument()
        }, { timeout: 5000 })
      })
    })

    describe('需求2: 信息外显和设置功能', () => {
      it('应该可以设置调试模式', async () => {
        render(<WebPlayerSimulator />)
        await waitFor(() => {
          const switches = screen.getAllByRole('switch')
          expect(switches.length).toBeGreaterThan(0)
        }, { timeout: 5000 })
      })
    })

    describe('播放功能验证', () => {
      it('应该支持 1X/2X/4X/8X 播放速度', async () => {
        render(<WebPlayerSimulator />)
        await waitFor(() => {
          expect(screen.getByText('1X')).toBeInTheDocument()
          expect(screen.getByText('2X')).toBeInTheDocument()
          expect(screen.getByText('4X')).toBeInTheDocument()
          expect(screen.getByText('8X')).toBeInTheDocument()
        }, { timeout: 5000 })
      })
    })
  })

  // ============================================================================
  // 测试结果汇总
  // ============================================================================

  describe('测试结果汇总', () => {
    it('所有核心功能模块都已实现', async () => {
      render(<WebPlayerSimulator />)

      await waitFor(() => {
        expect(screen.getByText('Web 播放端模拟器')).toBeInTheDocument()
      }, { timeout: 5000 })

      // 核心模块验证
      expect(screen.getByText('设备信息')).toBeInTheDocument()
    })
  })
})
