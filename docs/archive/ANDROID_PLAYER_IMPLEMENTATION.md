# CastPlay Android 播放端实现总结

## 一、后端改造

### 1. Device 模型扩展
**文件**: `app/models/device.py`

新增字段：
- `mac_address` - MAC 地址 (XX:XX:XX:XX:XX:XX)，唯一索引
- `ip_address` - IP 地址（支持 IPv6）
- `registration_code` - 基于 MAC 生成的注册码
- `playback_speed` - 播放速度倍数 (1, 2, 4, 8)

### 2. CachedMedia 模型
**文件**: `app/models/device.py`

用于跟踪设备已缓存的媒体文件：
- `device_id` - 设备 ID
- `media_id` - 媒体文件 ID
- `local_path` - 设备本地路径
- `md5_hash` - MD5 校验值
- `download_status` - 下载状态 (pending/downloading/completed/failed)

### 3. Playlist 模型扩展
**文件**: `app/models/playlist.py`

新增字段：
- `is_system` - 是否系统默认播放列表
- `version` - 版本号（用于增量更新）

### 4. 设备注册 API 改造
**文件**: `app/api/devices.py`

支持两种注册方式：
1. **MAC 地址注册**（推荐）：提供 `mac_address`，自动生成 `device_id` 和 `registration_code`
2. **传统 device_id 注册**：提供 `device_id`

注册码生成算法：
```python
def generate_registration_code(mac_address: str) -> str:
    clean_mac = mac_address.replace(':', '').upper()
    hash_obj = hashlib.sha256(clean_mac.encode())
    code = hash_obj.hexdigest()[:12].upper()
    return f"CP-{code[:4]}-{code[4:8]}-{code[8:12]}"
```

### 5. 播放速度配置 API
```http
PUT /api/devices/{device_id}/playback-speed
Body: { "speed": 2 }
```

## 二、前端播放器模块

**目录**: `frontend/src/player/`

### 文件结构
```
player/
├── index.tsx                 # 模块导出
├── types.ts                  # 类型定义
├── PlayerCore.tsx            # 核心播放逻辑
├── useDeviceRegistration.ts  # 设备注册 Hook
├── usePlaylistSync.ts        # 播放列表同步 Hook
├── useMediaCache.ts          # 媒体缓存 Hook
├── useOfflineMode.ts         # 离线模式 Hook
└── usePlaybackScheduler.ts   # 定时播放 Hook
```

### 核心 Hooks

1. **useDeviceRegistration**: 处理设备注册，支持 MAC 地址注册
2. **usePlaylistSync**: 播放列表版本检查和增量更新
3. **useMediaCache**: 媒体文件下载和缓存管理
4. **useOfflineMode**: 网络状态检测和离线播放
5. **usePlaybackScheduler**: 基于本地时区的定时播放

### Android Bridge 接口
```typescript
interface AndroidBridge {
  getMacAddress(): string;
  getIPAddress(): string;
  getDeviceId(): string;
  getRegistrationCode(): string;
  downloadMedia(url: string, mediaId: string): void;
  getDownloadProgress(mediaId: string): number;
  isMediaCached(mediaId: string): boolean;
  getCachedMediaPath(mediaId: string): string;
  getLocalTimezone(): string;
  showToast(message: string): void;
}
```

## 三、Android 应用

**目录**: `android/`

### 项目结构
```
android/
├── app/
│   ├── src/main/
│   │   ├── java/com/castplay/player/
│   │   │   ├── MainActivity.kt          # 主 Activity
│   │   │   ├── CastPlayApplication.kt   # Application 类
│   │   │   ├── JsBridge.kt             # JavaScript 接口
│   │   │   ├── CacheManager.kt         # 缓存管理
│   │   │   ├── MyDeviceAdminReceiver.kt # 设备管理
│   │   │   └── BootReceiver.kt         # 开机启动
│   │   ├── res/
│   │   │   ├── layout/activity_main.xml
│   │   │   ├── values/strings.xml
│   │   │   ├── values/colors.xml
│   │   │   ├── values/themes.xml
│   │   │   └── xml/
│   │   │       ├── network_security_config.xml
│   │   │       └── device_admin_policies.xml
│   │   └── AndroidManifest.xml
│   └── build.gradle.kts
├── build.gradle.kts
├── settings.gradle.kts
└── gradle.properties
```

### 核心功能

1. **WebView 宿主**: 加载播放器前端
2. **JavaScript Bridge**: 提供原生功能访问
3. **缓存管理**: 媒体文件下载和本地缓存
4. **Kiosk 模式**: 设备锁定为专用播放器
5. **开机自启**: 设备启动后自动运行
6. **离线播放**: 支持离线缓存播放

### 构建命令
```bash
# 构建调试版本
cd android && ./gradlew assembleDebug

# 构建发布版本
cd android && ./gradlew assembleRelease

# 安装到设备
adb install app/build/outputs/apk/debug/app-debug.apk
```

## 四、关键工作流程

### 设备注册流程
```
1. Android 应用启动
2. JsBridge.getMacAddress() 获取 MAC 地址
3. JsBridge.getRegistrationCode() 生成注册码
4. POST /api/devices/register { mac_address, registration_code }
5. 服务端返回设备信息
6. 保存到本地存储
```

### 播放列表同步流程
```
1. 设备启动 → POST /api/player/init
2. 服务端返回播放列表 + 版本号
3. 设备对比本地版本
4. 如需更新:
   a. 获取新增/修改的媒体项列表
   b. 调用 JsBridge.downloadMedia() 下载
   c. 下载完成后更新本地播放列表
5. WebSocket 监听实时更新
```

### 离线播放流程
```
1. 监听网络状态 (online/offline 事件)
2. 离线时:
   a. 检查 JsBridge.isMediaCached()
   b. 使用 JsBridge.getCachedMediaPath() 获取本地路径
   c. 加载 file:// URL
3. 在线时:
   a. 使用原始 HTTP URL
   b. 后台预加载缓存
```

## 五、测试验证

### 后端 API 测试
```bash
# MAC 地址注册
curl -X POST http://localhost:5000/api/devices/register \
  -H "Content-Type: application/json" \
  -d '{"mac_address":"AA:BB:CC:DD:EE:FF","device_name":"Test Device"}'

# 设置播放速度
curl -X PUT http://localhost:5000/api/devices/1/playback-speed \
  -H "Content-Type: application/json" \
  -d '{"speed": 2}'

# 播放端初始化
curl -X POST http://localhost:5000/api/player/init \
  -H "Content-Type: application/json" \
  -d '{"device_id":"device-AABBCCDDEEFF"}'
```

### 咋告测试
```bash
cd frontend && npm run build:player
```

### Android 构建测试
```bash
cd android && ./gradlew assembleDebug
```

## 六、后续优化建议

1. **媒体预加载优化**: 根据网络状况智能预加载
2. **错误恢复机制**: 下载失败自动重试
3. **统计上报**: 播放统计和设备状态上报
4. **OTA 更新**: 支持应用自动更新
5. **多窗口支持**: 支持多屏幕设备
