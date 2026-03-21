/**
 * 播放器配置类型定义
 * 包含服务器配置、设备注册、播放列表选择的类型
 */

// ============================================
// 存储键常量
// ============================================

export const STORAGE_KEYS = {
  SERVER_CONFIG: 'castplay_server_config',
  DEVICE_REGISTRATION: 'castplay_device_registration',
  PLAYLIST_SELECTION: 'castplay_playlist_selection',
} as const;

// ============================================
// 服务器配置类型
// ============================================

export type ConnectionStatus = 'success' | 'failed' | 'pending';
export type Protocol = 'http' | 'https';

export interface ServerConfig {
  /** 服务器地址（不含协议） */
  address: string;
  /** 端口号 */
  port: number;
  /** 连接协议 */
  protocol: Protocol;
  /** 配置保存时间（ISO 格式） */
  configuredAt: string;
  /** 最后连接状态 */
  lastConnectionStatus: ConnectionStatus;
  /** 最后连接时间（ISO 格式） */
  lastConnectionAt: string | null;
}

export interface ServerConfigInput {
  /** 用户输入的原始地址 */
  rawAddress: string;
}

export interface AddressValidationResult {
  /** 验证是否通过 */
  valid: boolean;
  /** 标准化后的地址 */
  normalized?: string;
  /** 提取的主机名 */
  host?: string;
  /** 提取的端口号 */
  port?: number;
  /** 错误消息 */
  error?: string;
}

// ============================================
// 设备注册类型
// ============================================

export interface DeviceRegistration {
  /** 设备是否已注册 */
  isRegistered: boolean;
  /** 设备 UUID（注册后分配） */
  deviceId: string | null;
  /** 注册时间（ISO 格式） */
  registeredAt: string | null;
  /** 注册操作者 */
  registeredBy: string | null;
}

// 注意：注册码从构建时环境变量读取
// import.meta.env.VITE_REGISTRATION_CODE

// ============================================
// 播放列表选择类型
// ============================================

export interface PlaylistSelection {
  /** 选中的播放列表 ID 列表 */
  selectedIds: number[];
  /** 最后更新时间（ISO 格式） */
  updatedAt: string;
  /** 是否由用户手动修改 */
  userModified: boolean;
}

export interface PlaylistInfo {
  /** 播放列表 ID */
  id: number;
  /** 播放列表名称 */
  name: string;
  /** 媒体数量 */
  mediaCount: number;
  /** 总大小（MB） */
  totalSizeMb: number;
  /** 缩略图 URL */
  thumbnailUrl?: string;
}

// ============================================
// Zustand Store 状态类型
// ============================================

export interface PlayerConfigState {
  /** 服务器配置 */
  server: ServerConfig | null;
  /** 设备注册状态 */
  registration: DeviceRegistration;
  /** 播放列表选择 */
  playlistSelection: PlaylistSelection;

  // Actions
  setServerConfig: (config: Omit<ServerConfig, 'configuredAt' | 'lastConnectionStatus'>) => void;
  updateConnectionStatus: (status: ConnectionStatus) => void;
  setRegistrationComplete: (deviceId: string) => void;
  setPlaylistSelection: (ids: number[], userModified: boolean) => void;
  clearAllConfig: () => void;
}

// ============================================
// Android Bridge 类型扩展
// 注意：AndroidBridge 接口在 ./types.ts 中定义
// ============================================

// ============================================
// 组件 Props 类型
// ============================================

export interface ServerConfigDialogProps {
  /** 是否显示对话框 */
  visible: boolean;
  /** 初始地址值 */
  initialAddress?: string;
  /** 保存回调 */
  onSave: (config: ServerConfig) => void;
  /** 取消回调 */
  onCancel: () => void;
}

export interface RegistrationCodeDisplayProps {
  /** 注册码 */
  code: string;
  /** 复制成功回调 */
  onCopySuccess?: () => void;
}

export interface PlaylistSelectionModalProps {
  /** 设备 ID */
  deviceId: string;
  /** 是否显示 */
  visible: boolean;
  /** 完成回调 */
  onCompleted: () => void;
}
