/**
 * API Client 测试
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { getMediaUrl } from '../api/client'

// 由于 apiClient 在模块加载时创建，我们暂时不测试它
// 只测试 getMediaUrl 工具函数

describe('API Client', () => {
  describe('getMediaUrl', () => {
    it('should return correct download URL for media ID', () => {
      const mediaId = 123
      const url = getMediaUrl(mediaId, 'download')

      expect(url).toContain('/api/media/123/download')
    })

    it('should return correct thumbnail URL for media ID', () => {
      const mediaId = 456
      const url = getMediaUrl(mediaId, 'thumbnail')

      expect(url).toContain('/api/media/456/thumbnail/noauth')
    })

    it('should return correct converted video URL', () => {
      const mediaId = 789
      const url = getMediaUrl(mediaId, 'converted')

      expect(url).toContain('/api/player/media/789/converted')
    })

    it('should default to download type when not specified', () => {
      const mediaId = 999
      const url = getMediaUrl(mediaId)

      expect(url).toContain('/api/media/999/download')
    })
  })
})
