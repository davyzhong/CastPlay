# CastPlay 播放端技术方案（简化版）

**版本：** 1.0
**更新日期：** 2026-03-06
**适用场景：** 小规模部署（<50 台）、弱网环境、低频更新

---

## 📋 目录

1. [需求概述](#1-需求概述)
2. [系统架构](#2-系统架构)
3. [核心功能设计](#3-核心功能设计)
4. [数据库设计](#4-数据库设计)
5. [API 接口设计](#5-api-接口设计)
6. [部署指南](#6-部署指南)
7. [测试计划](#7-测试计划)

---

## 1. 需求概述

### 1.1 核心需求

CastPlay 系统需支持两种播放端：

1. **Android TV 播放端**：APK 形式，开机自启，自动加载设备绑定的播放列表
2. **Web 网页播放端**：浏览器访问，行为与 Android 端完全一致

**关键约束：**

- 部署规模小：<50 台客户端
- 网络环境不稳定：需要本地缓存和离线播放能力
- 内容更新频率低：播放列表通常天/周/月级别才更新
- 无需复杂管理：仅需采集播放端状态，不需要远程控制

### 1.2 功能范围

#### ✅ 需要的功能

- 设备自动注册与标识
- 播放列表全量预下载
- 离线播放能力
- 低频心跳上报（2 小时一次）
- 播放端状态采集（在线状态、当前播放列表）
- 管理后台查看设备列表

#### ❌ 不需要的功能

- 远程管理（禁用/启用设备）
- 详细日志上报
- 截图监控
- WebSocket 实时通信
- 复杂的并发控制

---

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────┐
│                    播放端 (Android/Web)                  │
│                                                          │
│  启动流程：                                              │
│  1. 生成/读取设备 ID (localStorage)                      │
│  2. 调用 /api/player/init                                │
│  3. 全量下载播放列表媒体文件                              │
│  4. 开始本地播放                                         │
│                                                          │
│  运行时：                                                │
│  • 每 2 小时发送心跳（上报状态）                          │
│  • 每次启动时检查播放列表版本                             │
│  • 无 WebSocket 长连接                                   │
└─────────────────────────────────────────────────────────┘
                      ↓ 低频 HTTP 请求（2 小时一次）
┌─────────────────────────────────────────────────────────┐
│                    Backend API                           │
│                                                          │
│  FastAPI 应用：                                          │
│  • /api/player/init (POST)                               │
│  • /api/player/heartbeat (POST)                          │
│  • /api/player/playlist/{id}/check (POST)                │
│  • /api/player/status (GET)                              │
│                                                          │
│  SQLite / PostgreSQL:                                    │
│  └─ devices 表                                           │
│     ├─ device_id (VARCHAR, unique)                       │
│     ├─ last_online (TIMESTAMP)                          │
│     ├─ current_playlist_id (INT, FK)                     │
│     └─ last_media_id (INT, FK)                           │
└─────────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│                  管理后台 /devices                        │
│  React + Ant Design                                     │
│  • 设备列表（表格展示）                                  │
│  • 显示：设备 ID、名称、状态、播放列表、最后在线时间       │
│  • 导出 CSV 功能                                          │
└─────────────────────────────────────────────────────────┘
```

### 2.2 数据流图

```
播放端启动
    ↓
生成/读取设备 ID ← localStorage
    ↓
调用 /api/player/init
    ├─ 自动注册（如果未注册）
    └─ 返回播放列表 + 版本号
    ↓
全量下载播放列表所有媒体
    ├─ Android: DownloadService (原生)
    └─ Web: Cache API + IndexedDB
    ↓
开始本地播放（完全离线）
    ↓
每 2 小时发送心跳
    ├─ device_id
    ├─ current_playlist_id
    ├─ last_media_id
    └─ status (playing/idle)
    ↓
后端更新 devices 表
    ↓
管理员访问 /devices 页面
    ↓
实时查看所有播放端状态
```

### 2.3 关键技术决策

| 技术点        | 方案选择               | 理由                             |
| ------------- | ---------------------- | -------------------------------- |
| **缓存策略**  | 全量预下载             | 播放列表小 (<1GB)，更新频率低    |
| **设备标识**  | UUID v4 (localStorage) | 简单、跨平台、无需硬件权限       |
| **心跳频率**  | 2 小时一次             | 播放列表更新频率低，无需频繁上报 |
| **网络检测**  | 浏览器事件 + 低频心跳  | 足够判断在线/离线                |
| **WebSocket** | ❌ 不需要              | 通信需求极少，HTTP 轮询足够      |
| **离线能力**  | ⭐⭐⭐⭐⭐             | 大部分时间完全离线运行           |

---

## 3. 核心功能设计

### 3.1 设备标识与自动认证

**设计原则：**

- 每个播放端有唯一标识（UUID）
- 首次启动时自动生成并持久化
- 后续启动复用已保存的 ID
- 支持手动重置（用于测试或重新部署）

**Web 端实现：**

```typescript
class DeviceIdManager {
  private static readonly STORAGE_KEY = "castplay_device_id";

  static async getDeviceId(): Promise<string> {
    let deviceId = localStorage.getItem(this.STORAGE_KEY);

    if (!deviceId) {
      deviceId = this.generateUUIDv4();
      localStorage.setItem(this.STORAGE_KEY, deviceId);
    }

    return deviceId;
  }

  private static generateUUIDv4(): string {
    if (crypto && "randomUUID" in crypto) {
      return crypto.randomUUID();
    }

    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0;
      const v = c === "x" ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }
}
```

**Android 端实现：**

```kotlin
@JavascriptInterface
fun getDeviceId(): String {
    val prefs = context.getSharedPreferences("castplay_prefs", Context.MODE_PRIVATE)
    var deviceId = prefs.getString("device_id", null)

    if (deviceId == null) {
        deviceId = java.util.UUID.randomUUID().toString()
        prefs.edit().putString("device_id", deviceId).apply()
    }

    return deviceId
}
```

### 3.2 全量预下载策略

**设计原则：**

- 启动时一次性下载整个播放列表
- 顺序下载（避免并发过高）
- 支持断点续传（跳过已缓存文件）
- 下载完成后完全离线播放

**Web 端实现：**

```typescript
const preloadPlaylist = async (
  items: PlayerPlaylistItem[]
): Promise<boolean> => {
  let successCount = 0;

  for (const item of items) {
    try {
      const downloaded = await downloadMediaFile(item);
      if (downloaded) successCount++;
    } catch (error) {
      console.error(`Download failed: ${item.media_id}`, error);
    }
  }

  return successCount === items.length;
};
```

**Android 端实现：**

```kotlin
fun downloadMedia(url: String, mediaId: Long, fileName: String) {
    val file = File(getExternalFilesDir("media"), "$mediaId_$fileName")

    // 如果文件已存在，跳过下载
    if (file.exists()) {
        notifyDownloadComplete(mediaId, true)
        return
    }

    // 后台下载
    CoroutineScope(Dispatchers.IO).launch {
        try {
            val request = Request.Builder().url(url).build()
            val response = OkHttpClient.newCall(request).execute()

            response.body?.byteStream()?.use { input ->
                FileOutputStream(file).use { output ->
                    input.copyTo(output)
                }
            }

            notifyDownloadComplete(mediaId, true)
        } catch (e: Exception) {
            notifyDownloadComplete(mediaId, false)
        }
    }
}
```

### 3.3 心跳上报机制

**设计原则：**

- 每 2 小时上报一次状态
- 启动时立即上报一次
- 静默失败，不影响播放
- 仅上报必要信息

**上报内容：**

```json
{
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "current_playlist_id": 123,
  "last_media_id": 456,
  "status": "playing"
}
```

**TypeScript 实现：**

```typescript
const useHeartbeat = (
  deviceId: string | null,
  currentPlaylistId: number | null,
  lastMediaId: number | null,
  playbackStatus: "playing" | "idle"
) => {
  const HEARTBEAT_INTERVAL = 2 * 60 * 60 * 1000; // 2 小时

  const sendHeartbeat = useCallback(async () => {
    if (!deviceId) return;

    const payload = {
      device_id: deviceId,
      current_playlist_id: currentPlaylistId,
      last_media_id: lastMediaId,
      status: playbackStatus,
    };

    try {
      await axios.post("/api/player/heartbeat", payload, { timeout: 5000 });
    } catch (error) {
      console.debug("Heartbeat failed (offline):", error);
    }
  }, [deviceId, currentPlaylistId, lastMediaId, playbackStatus]);

  useEffect(() => {
    if (!deviceId) return;

    // 立即发送一次
    sendHeartbeat();

    // 定时发送
    const interval = setInterval(sendHeartbeat, HEARTBEAT_INTERVAL);
    return () => clearInterval(interval);
  }, [deviceId, sendHeartbeat]);
};
```

### 3.4 播放列表版本检查

**设计原则：**

- 每次启动时检查版本
- 如果服务器版本更新，刷新页面重新下载
- 低频轮询（可选，每 30 分钟一次）

**TypeScript 实现：**

```typescript
const checkVersion = async (
  playlistId: number,
  currentVersion: string
): Promise<boolean> => {
  const response = await axios.post(
    `/api/player/playlist/${playlistId}/check`,
    {
      version: currentVersion,
    }
  );

  return response.data.needs_update;
};
```

---

## 4. 数据库设计

### 4.1 devices 表结构

```sql
CREATE TABLE devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id VARCHAR(255) UNIQUE NOT NULL,
    device_name VARCHAR(255) DEFAULT 'Unknown Player',
    device_type VARCHAR(50) DEFAULT 'web_browser',

    -- 状态信息
    status VARCHAR(50) DEFAULT 'offline',
    last_online TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 播放状态（新增字段）
    current_playlist_id INTEGER REFERENCES playlists(id),
    last_media_id INTEGER REFERENCES media_files(id),

    -- 元数据（JSON 格式，可选）
    metadata TEXT
);

-- 索引
CREATE INDEX idx_devices_device_id ON devices(device_id);
CREATE INDEX idx_devices_status ON devices(status);
CREATE INDEX idx_devices_last_online ON devices(last_online);
```

### 4.2 迁移脚本

```sql
-- 添加新字段（如果表已存在）
ALTER TABLE devices ADD COLUMN current_playlist_id INTEGER;
ALTER TABLE devices ADD COLUMN last_media_id INTEGER;
ALTER TABLE devices ADD COLUMN metadata TEXT;
```

---

## 5. API 接口设计

### 5.1 /api/player/init (POST)

**功能：** 播放端初始化（自动注册 + 返回播放列表）

**请求：**

```json
{
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "device_type": "android_tv"
}
```

**响应：**

```json
{
    "device": {
        "id": 1,
        "device_id": "550e8400-e29b-41d4-a716-446655440000",
        "device_name": "Player-440000"
    },
    "playlists": [...],
    "server_time": "2026-03-06T10:30:00Z"
}
```

### 5.2 /api/player/heartbeat (POST)

**功能：** 接收心跳（2 小时一次）

**请求：**

```json
{
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "current_playlist_id": 123,
  "last_media_id": 456,
  "status": "playing"
}
```

**响应：**

```json
{
  "acknowledged": true
}
```

### 5.3 /api/player/playlist/{id}/check (POST)

**功能：** 检查播放列表版本

**请求：**

```json
{
  "version": "2026-03-06T10:00:00Z"
}
```

**响应：**

```json
{
  "needs_update": true,
  "current_version": "2026-03-06T12:00:00Z"
}
```

### 5.4 /api/player/status (GET)

**功能：** 获取设备状态列表（管理后台使用）

**查询参数：**

- `status_filter`: online | offline | null（全部）

**响应示例：**

```json
[
  {
    "device_id": "550e8400-e29b-41d4-a716-446655440000",
    "device_name": "Player-440000",
    "status": "online",
    "last_online": "2026-03-06T10:30:00Z",
    "current_playlist": {
      "id": 123,
      "name": "会议室播放列表"
    }
  }
]
```

---

## 6. 部署指南

### 6.1 后端部署

```bash
# 1. 安装依赖
cd castplay-allinone
pip install -r requirements.txt

# 2. 运行数据库迁移
python scripts/migrate_db.py

# 3. 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 6.2 前端部署

```bash
# 1. 安装依赖
cd frontend
npm install

# 2. 构建生产版本
npm run build

# 3. 部署到 Nginx
cp -r dist/* /var/www/castplay/
```

### 6.3 Android APK 打包

1. 使用 Android Studio 打开 android/ 目录
2. 修改 build.gradle.kts 中的配置
3. Build → Generate Signed Bundle / APK
4. 分发到各电视盒子

---

## 7. 测试计划

### 7.1 功能测试

- [ ] 设备自动注册
- [ ] 播放列表全量下载
- [ ] 离线播放
- [ ] 心跳上报
- [ ] 版本检查与更新

### 7.2 性能测试

- [ ] 下载速度测试（不同网络环境）
- [ ] 内存占用测试
- [ ] 存储空间管理

### 7.3 兼容性测试

- [ ] Android TV 盒子（不同品牌）
- [ ] Web 浏览器（Chrome、Firefox、Edge）
- [ ] 不同屏幕分辨率

---

## 附录

### A. 常见问题解答

**Q: 设备 ID 丢失怎么办？**
A: 清除 localStorage 后会自动生成新的 ID，相当于新设备注册。

**Q: 下载失败如何处理？**
A: 静默失败，继续播放其他已下载的媒体。下次启动时会重试。

**Q: 如何清理缓存？**
A: 管理后台提供清空缓存按钮，或在 App 设置中清除数据。

### B. 参考资料

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [React 官方文档](https://react.dev/)
- [Android WebView 指南](https://developer.android.com/guide/webapps/webview)
