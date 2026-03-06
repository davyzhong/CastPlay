/**
 * 全局常量定义
 *
 * 避免在代码中硬编码魔法数字和字符串
 */

// ============= API 相关 =============
export const DEFAULT_PAGE_SIZE = 20;
export const MAX_PAGE_SIZE = 100;

// ============= 文件上传 =============
export const MAX_FILE_SIZE_MB = 500;
export const ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'];
export const ALLOWED_VIDEO_EXTENSIONS = ['mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv'];
export const ALLOWED_PPT_EXTENSIONS = ['ppt', 'pptx'];

// ============= 媒体类型 =============
export const MEDIA_TYPE = {
  IMAGE: 'image' as const,
  VIDEO: 'video' as const,
  PPT: 'ppt' as const,
};

export const MEDIA_TYPE_LABELS = {
  [MEDIA_TYPE.IMAGE]: '图片',
  [MEDIA_TYPE.VIDEO]: '视频',
  [MEDIA_TYPE.PPT]: 'PPT',
};

// ============= MIME 类型映射 =============
export const MIME_TYPE_MAP: Record<string, string> = {
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.png': 'image/png',
  '.gif': 'image/gif',
  '.bmp': 'image/bmp',
  '.webp': 'image/webp',
  '.mp4': 'video/mp4',
  '.avi': 'video/x-msvideo',
  '.mov': 'video/quicktime',
  '.mkv': 'video/x-matroska',
};

// ============= 状态管理 =============
export const MEDIA_STATUS = {
  PROCESSING: 'processing' as const,
  READY: 'ready' as const,
  FAILED: 'failed' as const,
};

export const MEDIA_STATUS_LABELS = {
  [MEDIA_STATUS.PROCESSING]: '处理中',
  [MEDIA_STATUS.READY]: '就绪',
  [MEDIA_STATUS.FAILED]: '失败',
};

// ============= 播放列表 =============
export const DEFAULT_IMAGE_DISPLAY_DURATION = 5; // 图片默认显示时长（秒）
export const DEFAULT_PPT_FRAME_DURATION = 5; // PPT 每页默认时长（秒）

// ============= WebSocket =============
export const WS_RECONNECT_DELAY = 3000; // 重连延迟（毫秒）
export const WS_MAX_RECONNECT_ATTEMPTS = 5; // 最大重连次数

// ============= UI 配置 =============
export const TABLE_PAGE_SIZE_OPTIONS = [10, 20, 50, 100];
export const UPLOAD_DRAGGER_HEIGHT = 200;

// ============= 文件格式化 =============
export const formatFileSize = (bytes: number): string => {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
};

export const formatDateTime = (dateString: string): string => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
};
