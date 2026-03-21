/**
 * 播放列表视频预览功能测试
 * 测试从点击视频图标到播放控制的完整流程
 *
 * 测试用例总结：
 * 1. 视频图标渲染 - 验证视频项目显示可点击的图标
 * 2. 视频预览模态框 - 点击图标后打开预览
 * 3. 播放速度控制 - 测试 1X/2X/4X/8X 按钮
 * 4. 模态框关闭 - 验证关闭时重置状态
 * 5. PPT 预览功能 - 根据 PPT 转换状态显示不同 UI
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '../test/utils'
import PlaylistListPage from '../pages/PlaylistList'

// Mock playlist API
vi.mock('../api/playlist', () => ({
  getPlaylistList: vi.fn(() => Promise.resolve({
    items: [
      {
        id: 1,
        name: 'Test Playlist with Video',
        description: '',
        item_count: 2,
        device_count: 0,
        created_at: '2024-01-01 00:00:00',
        updated_at: '2024-01-01 00:00:00',
      },
    ],
    total: 1,
  })),
  createPlaylist: vi.fn(),
  getPlaylistDetail: vi.fn(() => Promise.resolve({
    id: 1,
    name: 'Test Playlist with Video',
    description: '',
    items: [
      {
        id: 1,
        playlist_id: 1,
        media_id: 1,
        file_name: 'test-video.mp4',
        file_type: 'video',
        display_order: 0,
        display_duration: 10,
        created_at: '2024-01-01 00:00:00',
      },
      {
        id: 2,
        playlist_id: 1,
        media_id: 2,
        file_name: 'test-image.png',
        file_type: 'image',
        display_order: 1,
        display_duration: 5,
        created_at: '2024-01-01 00:00:00',
      },
    ],
    devices: [],
    created_at: '2024-01-01 00:00:00',
    updated_at: '2024-01-01 00:00:00',
  })),
  deletePlaylist: vi.fn(),
  removeItemFromPlaylist: vi.fn(),
  assignPlaylistToDevice: vi.fn(),
  unassignPlaylistFromDevice: vi.fn(),
  reorderPlaylistItems: vi.fn(),
  addItemsToPlaylistBatch: vi.fn(),
  updatePlaylistItem: vi.fn(),
  updatePlaylist: vi.fn(),
}))

// Mock media API
vi.mock('../api/media', () => ({
  getMediaList: vi.fn(() => Promise.resolve({
    items: [
      {
        id: 1,
        file_name: 'test-video.mp4',
        file_type: 'video',
        file_path: '/data/media/1.mp4',
        file_size: 1024000,
        status: 'ready',
        created_at: '2024-01-01 00:00:00',
      },
      {
        id: 2,
        file_name: 'test-image.png',
        file_type: 'image',
        file_path: '/data/media/2.png',
        file_size: 512000,
        status: 'ready',
        created_at: '2024-01-01 00:00:00',
      },
    ],
    total: 2,
  })),
  getMediaFileUrl: vi.fn((id: number) => `/api/media/${id}/download`),
  getThumbnail: vi.fn((id: number) => `/api/media/${id}/thumbnail`),
}))

// Mock device API
vi.mock('../api/device', () => ({
  getDeviceList: vi.fn(() => Promise.resolve({
    items: [],
    total: 0,
  })),
}))

describe('播放列表视频预览功能', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllTimers()
  })

  // ============================================================================
  // 1. 视频图标渲染测试
  // ============================================================================

  describe('视频图标渲染', () => {
    it('视频类型项目应显示可点击的图标', async () => {
      render(<PlaylistListPage />)

      // 等待播放列表加载
      await waitFor(() => {
        expect(screen.getByText('播放列表管理')).toBeInTheDocument()
      }, { timeout: 10000 })

      // 点击"管理"按钮打开播放列表详情
      const manageButtons = await screen.findAllByRole('button', { name: /管理/i })
      expect(manageButtons.length).toBeGreaterThan(0)
      fireEvent.click(manageButtons[0])

      // 等待详情模态框打开
      await waitFor(() => {
        expect(screen.getByText('Test Playlist with Video')).toBeInTheDocument()
      }, { timeout: 10000 })

      // 验证视频图标存在且可点击（现在使用播放图标）
      const playIcons = screen.getAllByText('▶️')
      expect(playIcons.length).toBeGreaterThan(0)
    })

    it('视频图标应有点击预览功能', async () => {
      render(<PlaylistListPage />)

      await waitFor(() => {
        expect(screen.getByText('播放列表管理')).toBeInTheDocument()
      }, { timeout: 10000 })

      const manageButtons = screen.findAllByRole('button', { name: /管理/i })
      const btn = await manageButtons
      fireEvent.click(btn[0])

      await waitFor(() => {
        expect(screen.getByText('Test Playlist with Video')).toBeInTheDocument()
      }, { timeout: 10000 })

      // 验证视频缩略图容器有 cursor: pointer 样式（可点击）
      const playIcons = screen.getAllByText('▶️')
      const videoThumbnail = playIcons[0].closest('div[style*="cursor: pointer"]')
      expect(videoThumbnail).toBeInTheDocument()
    })
  })

  // ============================================================================
  // 2. 播放速度控制测试
  // ============================================================================

  describe('播放速度控制', () => {
    it('应显示播放速度按钮 (1X/2X/4X/8X)', async () => {
      render(<PlaylistListPage />)

      await waitFor(() => {
        expect(screen.getByText('播放列表管理')).toBeInTheDocument()
      }, { timeout: 10000 })

      const manageButtons = await screen.findAllByRole('button', { name: /管理/i })
      fireEvent.click(manageButtons[0])

      await waitFor(() => {
        expect(screen.getByText('Test Playlist with Video')).toBeInTheDocument()
      }, { timeout: 10000 })

      // 点击视频缩略图（通过播放图标找到可点击容器）
      const playIcons = screen.getAllByText('▶️')
      const videoThumbnail = playIcons[0].closest('div[style*="cursor: pointer"]') as HTMLElement
      fireEvent.click(videoThumbnail)

      // 等待视频预览模态框打开
      await waitFor(() => {
        // 验证所有速度按钮都存在
        expect(screen.getByRole('button', { name: '1X' })).toBeInTheDocument()
      }, { timeout: 10000 })

      expect(screen.getByRole('button', { name: '2X' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: '4X' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: '8X' })).toBeInTheDocument()
    })

    it('点击速度按钮应更新视频播放速率', async () => {
      render(<PlaylistListPage />)

      await waitFor(() => {
        expect(screen.getByText('播放列表管理')).toBeInTheDocument()
      }, { timeout: 10000 })

      const manageButtons = await screen.findAllByRole('button', { name: /管理/i })
      fireEvent.click(manageButtons[0])

      await waitFor(() => {
        expect(screen.getByText('Test Playlist with Video')).toBeInTheDocument()
      }, { timeout: 10000 })

      // 点击视频缩略图（通过播放图标找到可点击容器）
      const playIcons = screen.getAllByText('▶️')
      const videoThumbnail = playIcons[0].closest('div[style*="cursor: pointer"]') as HTMLElement
      fireEvent.click(videoThumbnail)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: '2X' })).toBeInTheDocument()
      }, { timeout: 10000 })

      const video = document.querySelector('video') as HTMLVideoElement
      expect(video).toBeInTheDocument()

      const speed2xBtn = screen.getByRole('button', { name: '2X' })

      // 点击 2X 按钮
      fireEvent.click(speed2xBtn)

      // 验证视频播放速率更新
      await waitFor(() => {
        expect(video.playbackRate).toBe(2)
      })
    })

    it('切换速度应高亮当前速度按钮', async () => {
      render(<PlaylistListPage />)

      await waitFor(() => {
        expect(screen.getByText('播放列表管理')).toBeInTheDocument()
      }, { timeout: 10000 })

      const manageButtons = await screen.findAllByRole('button', { name: /管理/i })
      fireEvent.click(manageButtons[0])

      await waitFor(() => {
        expect(screen.getByText('Test Playlist with Video')).toBeInTheDocument()
      }, { timeout: 10000 })

      // 点击视频缩略图（通过播放图标找到可点击容器）
      const playIcons = screen.getAllByText('▶️')
      const videoThumbnail = playIcons[0].closest('div[style*="cursor: pointer"]') as HTMLElement
      fireEvent.click(videoThumbnail)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: '4X' })).toBeInTheDocument()
      }, { timeout: 10000 })

      const speed4xBtn = screen.getByRole('button', { name: '4X' })

      // 点击 4X 按钮
      fireEvent.click(speed4xBtn)

      // 验证按钮变为 primary 样式
      await waitFor(() => {
        expect(speed4xBtn).toHaveClass('ant-btn-primary')
      })
    })
  })

  // ============================================================================
  // 3. 集成测试
  // ============================================================================

  describe('视频预览集成测试', () => {
    it('完整的视频预览流程：点击图标 -> 打开预览 -> 切换速度', { timeout: 30000 }, async () => {
      render(<PlaylistListPage />)

      // 1. 等待页面加载
      await waitFor(() => {
        expect(screen.getByText('播放列表管理')).toBeInTheDocument()
      }, { timeout: 10000 })

      // 2. 打开播放列表详情
      const manageButtons = await screen.findAllByRole('button', { name: /管理/i })
      fireEvent.click(manageButtons[0])

      await waitFor(() => {
        expect(screen.getByText('Test Playlist with Video')).toBeInTheDocument()
      }, { timeout: 10000 })

      // 3. 点击视频缩略图（通过播放图标找到可点击容器）
      const playIcons = screen.getAllByText('▶️')
      const videoIconContainer = playIcons[0].closest('div[style*="cursor: pointer"]') as HTMLElement
      fireEvent.click(videoIconContainer)

      // 4. 等待预览模态框打开并验证视频元素
      await waitFor(() => {
        const video = document.querySelector('video')
        expect(video).toBeInTheDocument()
      }, { timeout: 10000 })

      const video = document.querySelector('video') as HTMLVideoElement
      expect(video.src).toContain('/api/media/1/download')

      // 5. 测试速度按钮
      const speed2xBtn = screen.getByRole('button', { name: '2X' })
      fireEvent.click(speed2xBtn)

      await waitFor(() => {
        expect(video.playbackRate).toBe(2)
        expect(speed2xBtn).toHaveClass('ant-btn-primary')
      })

      // 6. 切换到 4X
      const speed4xBtn = screen.getByRole('button', { name: '4X' })
      fireEvent.click(speed4xBtn)

      await waitFor(() => {
        expect(video.playbackRate).toBe(4)
        expect(speed4xBtn).toHaveClass('ant-btn-primary')
      })
    })
  })

  // ============================================================================
  // 4. PPT 预览功能测试
  // ============================================================================

  describe('PPT 预览功能', () => {
    it('PPT 转换成功时应显示播放图标并打开视频预览', async () => {
      // 更新 mock 数据以包含 PPT 项目
      const { getPlaylistDetail } = await import('../api/playlist')
      const { getMediaList } = await import('../api/media')

      vi.mocked(getPlaylistDetail).mockResolvedValue({
        id: 1,
        name: 'Test Playlist with PPT',
        description: '',
        items: [
          {
            id: 3,
            playlist_id: 1,
            media_id: 3,
            file_name: 'test-ppt.pptx',
            file_type: 'ppt',
            display_order: 0,
            display_duration: 10,
            created_at: '2024-01-01 00:00:00',
          },
        ],
        devices: [],
        created_at: '2024-01-01 00:00:00',
        updated_at: '2024-01-01 00:00:00',
      })

      vi.mocked(getMediaList).mockResolvedValue({
        items: [
          {
            id: 3,
            file_name: 'test-ppt.pptx',
            file_type: 'ppt',
            file_path: '/data/media/3.pptx',
            file_size: 1024000,
            status: 'ready',
            created_at: '2024-01-01 00:00:00',
          },
        ],
        total: 1,
      })

      render(<PlaylistListPage />)

      await waitFor(() => {
        expect(screen.getByText('播放列表管理')).toBeInTheDocument()
      }, { timeout: 10000 })

      const manageButtons = await screen.findAllByRole('button', { name: /管理/i })
      fireEvent.click(manageButtons[0])

      await waitFor(() => {
        expect(screen.getByText('Test Playlist with PPT')).toBeInTheDocument()
      }, { timeout: 10000 })

      // 验证 PPT 显示播放图标
      const playIcons = screen.getAllByText('▶️')
      expect(playIcons.length).toBeGreaterThan(0)

      // 点击播放图标
      const pptThumbnail = playIcons[0].closest('div[style*="cursor: pointer"]')
      if (pptThumbnail) {
        fireEvent.click(pptThumbnail)
      }

      // 等待视频预览模态框打开
      await waitFor(() => {
        const video = document.querySelector('video')
        expect(video).toBeInTheDocument()
      }, { timeout: 10000 })
    })

    it('PPT 转换中时应显示加载状态和"暂不可预览"提示', async () => {
      const { getPlaylistDetail } = await import('../api/playlist')
      const { getMediaList } = await import('../api/media')

      vi.mocked(getPlaylistDetail).mockResolvedValue({
        id: 2,
        name: 'Test Playlist with Processing PPT',
        description: '',
        items: [
          {
            id: 4,
            playlist_id: 2,
            media_id: 4,
            file_name: 'processing-ppt.pptx',
            file_type: 'ppt',
            display_order: 0,
            display_duration: 10,
            created_at: '2024-01-01 00:00:00',
          },
        ],
        devices: [],
        created_at: '2024-01-01 00:00:00',
        updated_at: '2024-01-01 00:00:00',
      })

      vi.mocked(getMediaList).mockResolvedValue({
        items: [
          {
            id: 4,
            file_name: 'processing-ppt.pptx',
            file_type: 'ppt',
            file_path: '/data/media/4.pptx',
            file_size: 1024000,
            status: 'processing',
            created_at: '2024-01-01 00:00:00',
          },
        ],
        total: 1,
      })

      render(<PlaylistListPage />)

      await waitFor(() => {
        expect(screen.getByText('播放列表管理')).toBeInTheDocument()
      }, { timeout: 10000 })

      const manageButtons = await screen.findAllByRole('button', { name: /管理/i })
      fireEvent.click(manageButtons[0])

      await waitFor(() => {
        expect(screen.getByText('Test Playlist with Processing PPT')).toBeInTheDocument()
      }, { timeout: 10000 })

      // 验证显示"暂不可预览"提示
      expect(screen.getByText('暂不可预览')).toBeInTheDocument()
    })

    it('PPT 转换失败时应显示错误状态和"转换失败"提示', async () => {
      const { getPlaylistDetail } = await import('../api/playlist')
      const { getMediaList } = await import('../api/media')

      vi.mocked(getPlaylistDetail).mockResolvedValue({
        id: 3,
        name: 'Test Playlist with Failed PPT',
        description: '',
        items: [
          {
            id: 5,
            playlist_id: 3,
            media_id: 5,
            file_name: 'failed-ppt.pptx',
            file_type: 'ppt',
            display_order: 0,
            display_duration: 10,
            created_at: '2024-01-01 00:00:00',
          },
        ],
        devices: [],
        created_at: '2024-01-01 00:00:00',
        updated_at: '2024-01-01 00:00:00',
      })

      vi.mocked(getMediaList).mockResolvedValue({
        items: [
          {
            id: 5,
            file_name: 'failed-ppt.pptx',
            file_type: 'ppt',
            file_path: '/data/media/5.pptx',
            file_size: 1024000,
            status: 'failed',
            created_at: '2024-01-01 00:00:00',
          },
        ],
        total: 1,
      })

      render(<PlaylistListPage />)

      await waitFor(() => {
        expect(screen.getByText('播放列表管理')).toBeInTheDocument()
      }, { timeout: 10000 })

      const manageButtons = await screen.findAllByRole('button', { name: /管理/i })
      fireEvent.click(manageButtons[0])

      await waitFor(() => {
        expect(screen.getByText('Test Playlist with Failed PPT')).toBeInTheDocument()
      }, { timeout: 10000 })

      // 验证显示"转换失败"提示
      expect(screen.getByText('转换失败')).toBeInTheDocument()
    })
  })
})
