/**
 * Constants 常量测试
 */
import { describe, it, expect } from 'vitest'
import {
  DEFAULT_PAGE_SIZE,
  MAX_PAGE_SIZE,
  MAX_FILE_SIZE_MB,
  MEDIA_TYPE,
  MEDIA_TYPE_LABELS,
  ALLOWED_IMAGE_EXTENSIONS,
  ALLOWED_VIDEO_EXTENSIONS
} from '../constants/index'

describe('Constants', () => {
  describe('API Constants', () => {
    it('should have correct page size constants', () => {
      expect(DEFAULT_PAGE_SIZE).toBe(20)
      expect(MAX_PAGE_SIZE).toBe(100)
    })
  })

  describe('File Upload Constants', () => {
    it('should have correct max file size', () => {
      expect(MAX_FILE_SIZE_MB).toBe(500)
    })

    it('should have allowed image extensions', () => {
      expect(ALLOWED_IMAGE_EXTENSIONS).toEqual(
        expect.arrayContaining(['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'])
      )
    })

    it('should have allowed video extensions', () => {
      expect(ALLOWED_VIDEO_EXTENSIONS).toEqual(
        expect.arrayContaining(['mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv'])
      )
    })
  })

  describe('Media Type Constants', () => {
    it('should have media type definitions', () => {
      expect(MEDIA_TYPE.IMAGE).toBe('image')
      expect(MEDIA_TYPE.VIDEO).toBe('video')
      expect(MEDIA_TYPE.PPT).toBe('ppt')
    })

    it('should have media type labels', () => {
      expect(MEDIA_TYPE_LABELS[MEDIA_TYPE.IMAGE]).toBe('图片')
      expect(MEDIA_TYPE_LABELS[MEDIA_TYPE.VIDEO]).toBe('视频')
      expect(MEDIA_TYPE_LABELS[MEDIA_TYPE.PPT]).toBe('PPT')
    })
  })
})
