# CastPlay 实现指南

## 项目状态

### 已完成 ✅

#### 后端 (castplay-server/)

1. **项目结构** - 完整的目录结构
2. **配置管理** - `config.py` 多环境配置
3. **数据库模型** - 6 个核心模型：
   - Device & DeviceSchedule
   - MediaFile
   - Playlist, PlaylistItem & DevicePlaylist
4. **API 路由** - 4 个蓝图：
   - `/api/devices` - 设备管理
   - `/api/media` - 媒体文件管理
   - `/api/playlists` - 播放列表管理
   - `/api/player` - 播放端专用接口
5. **PPT 转换服务** - `app/services/converter.py`
   - PPT → PDF → 图片序列 → 视频
   - 缩略图生成
   - MD5 哈希计算
6. **Celery 异步任务** - `app/tasks/convert.py`
   - 异步 PPT 转视频任务
7. **WebSocket 推送** - `app/websocket/handler.py`
   - 设备注册和心跳
   - 播放列表更新通知
   - 定时配置更新通知
   - 强制同步和重启命令

### 待实现 🚧

#### 前端 (castplay-admin/)

需要使用 Vite + React + TypeScript + Ant Design 创建管理后台。

**初始化命令：**

```bash
cd /Users/Davy/PycharmProjects/Davy\ Skills/CastPlay
npm create vite@latest castplay-admin -- --template react-ts
cd castplay-admin
npm install
npm install antd axios react-router-dom @types/react-router-dom socket.io-client react-beautiful-dnd
```

**核心文件结构：**

```
castplay-admin/
├── src/
│   ├── api/
│   │   ├── client.ts          # Axios 实例配置
│   │   ├── device.ts          # 设备 API
│   │   ├── media.ts           # 媒体 API
│   │   ├── playlist.ts        # 播放列表 API
│   │   └── websocket.ts       # WebSocket 客户端
│   ├── pages/
│   │   ├── Dashboard.tsx      # 仪表盘
│   │   ├── DeviceList.tsx     # 设备管理
│   │   ├── MediaList.tsx      # 媒体库
│   │   └── PlaylistList.tsx   # 播放列表管理
│   ├── components/
│   │   ├── MediaUpload.tsx    # 文件上传组件
│   │   ├── PlaylistEditor.tsx # 播放列表编辑器
│   │   └── ScheduleForm.tsx   # 定时配置表单
│   ├── App.tsx
│   ├── main.tsx
│   └── router.tsx
├── package.json
└── vite.config.ts
```

**关键实现：**

1. **API 客户端** (`src/api/client.ts`):

```typescript
import axios from "axios";

const client = axios.create({
  baseURL: "http://localhost:5000/api",
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

export default client;
```

2. **设备 API** (`src/api/device.ts`):

```typescript
import client from "./client";

export const deviceApi = {
  list: (params) => client.get("/devices", { params }),
  get: (id) => client.get(`/devices/${id}`),
  update: (id, data) => client.put(`/devices/${id}`, data),
  delete: (id) => client.delete(`/devices/${id}`),
  setSchedule: (id, data) => client.post(`/devices/${id}/schedule`, data),
};
```

3. **播放列表页面** (`src/pages/PlaylistList.tsx`):

- 使用 Ant Design Table 显示列表
- 支持拖拽排序（react-beautiful-dnd）
- 分配设备对话框
- 添加媒体对话框

#### Android 端 (android-app/)

需要使用 Android Studio 创建项目。

**Gradle 配置** (`app/build.gradle`):

```gradle
dependencies {
    // Android核心
    implementation 'androidx.appcompat:appcompat:1.6.1'
    implementation 'androidx.constraintlayout:constraintlayout:2.1.4'
    implementation 'androidx.webkit:webkit:1.8.0'

    // ExoPlayer
    implementation 'com.google.android.exoplayer:exoplayer:2.19.1'

    // Glide
    implementation 'com.github.bumptech.glide:glide:4.16.0'

    // Retrofit
    implementation 'com.squareup.retrofit2:retrofit:2.9.0'
    implementation 'com.squareup.retrofit2:converter-gson:2.9.0'

    // OkHttp WebSocket
    implementation 'com.squareup.okhttp3:okhttp:4.12.0'

    // Room
    implementation 'androidx.room:room-runtime:2.6.0'
    kapt 'androidx.room:room-compiler:2.6.0'

    // Coroutines
    implementation 'org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3'
}
```

**核心文件结构：**

```
android-app/
├── app/src/main/
│   ├── java/com/castplay/player/
│   │   ├── MainActivity.java
│   │   ├── PlayerActivity.java
│   │   ├── data/
│   │   │   ├── db/
│   │   │   │   ├── AppDatabase.java
│   │   │   │   ├── dao/
│   │   │   │   └── entity/
│   │   │   ├── model/
│   │   │   └── repository/
│   │   ├── network/
│   │   │   ├── ApiService.java
│   │   │   ├── RetrofitClient.java
│   │   │   └── WebSocketManager.java
│   │   ├── service/
│   │   │   ├── SyncService.java
│   │   │   ├── ScheduleService.java
│   │   │   └── DownloadService.java
│   │   ├── player/
│   │   │   ├── MediaPlayer.java
│   │   │   ├── ImagePlayer.java
│   │   │   └── VideoPlayer.java
│   │   └── util/
│   ├── res/
│   └── AndroidManifest.xml
├── build.gradle
└── settings.gradle
```

**核心逻辑：**

1. **MainActivity** - WebView 加载服务器 URL
2. **SyncManager** - 后台同步播放列表和媒体文件
3. **ScheduleManager** - 定时开关机控制
4. **PlaybackEngine** - 多媒体播放引擎
   - ImagePlayer：图片轮播（Handler + ImageView）
   - VideoPlayer：视频循环（ExoPlayer）
   - PlaylistManager：混合列表播放逻辑

**关键实现：**

1. **WebSocket 客户端** (`WebSocketManager.java`):

```java
public class WebSocketManager {
    private OkHttpClient client;
    private WebSocket webSocket;
    private String deviceId;

    public void connect(String url, String deviceId) {
        Request request = new Request.Builder()
            .url(url)
            .build();

        webSocket = client.newWebSocket(request, new WebSocketListener() {
            @Override
            public void onOpen(WebSocket webSocket, Response response) {
                // 注册设备
                JSONObject register = new JSONObject();
                register.put("device_id", deviceId);
                webSocket.send(register.toString());
            }

            @Override
            public void onMessage(WebSocket webSocket, String text) {
                // 处理推送消息
                handleMessage(text);
            }
        });
    }

    private void handleMessage(String message) {
        // 解析并处理: playlist_update, schedule_update, force_sync, reboot
    }
}
```

2. **播放引擎** (`PlaybackEngine.java`):

```java
public class PlaybackEngine {
    private List<MediaItem> playlist;
    private int currentIndex = 0;
    private ImageView imageView;
    private PlayerView videoView;
    private ExoPlayer exoPlayer;

    public void play() {
        if (playlist == null || playlist.isEmpty()) return;

        MediaItem item = playlist.get(currentIndex);

        switch (item.getType()) {
            case IMAGE:
                playImage(item);
                break;
            case VIDEO:
            case PPT:
                playVideo(item);
                break;
        }
    }

    private void playImage(MediaItem item) {
        Glide.with(context)
            .load(item.getFilePath())
            .into(imageView);

        // 定时切换下一个
        handler.postDelayed(() -> playNext(), item.getDuration() * 1000);
    }

    private void playVideo(MediaItem item) {
        MediaItem media = MediaItem.fromUri(item.getFilePath());
        exoPlayer.setMediaItem(media);
        exoPlayer.prepare();
        exoPlayer.play();

        // 监听播放完成
        exoPlayer.addListener(new Player.Listener() {
            @Override
            public void onPlaybackStateChanged(int state) {
                if (state == Player.STATE_ENDED) {
                    playNext();
                }
            }
        });
    }

    private void playNext() {
        currentIndex = (currentIndex + 1) % playlist.size();
        play();
    }
}
```

## 部署指南

### 后端部署

1. **安装依赖**:

```bash
cd castplay-server
pip install -r requirements.txt
```

2. **安装系统工具**:

```bash
# Ubuntu/Debian
sudo apt-get install libreoffice poppler-utils imagemagick ffmpeg redis-server

# macOS
brew install libreoffice poppler imagemagick ffmpeg redis
```

3. **初始化数据库**:

```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

4. **启动 Redis**:

```bash
redis-server
```

5. **启动 Celery Worker**:

```bash
celery -A app.tasks.celery_app:celery worker --loglevel=info
```

6. **启动 Flask 服务器**:

```bash
python run.py
```

### 前端部署

```bash
cd castplay-admin
npm install
npm run dev   # 开发模式
npm run build # 生产构建
```

### Android 打包

1. 在 Android Studio 中打开项目
2. Build → Generate Signed Bundle / APK
3. 选择 APK，配置签名
4. 生成 release APK

## API 文档

### 设备管理

**POST /api/devices/register** - 设备注册

```json
{
  "device_id": "unique-device-id",
  "device_name": "Office TV 1",
  "timezone": "Asia/Shanghai"
}
```

**GET /api/devices** - 设备列表
**GET /api/devices/{id}** - 设备详情
**PUT /api/devices/{id}** - 更新设备
**DELETE /api/devices/{id}** - 删除设备

**POST /api/devices/{id}/schedule** - 设置定时

```json
{
  "power_on_time": "08:00",
  "power_off_time": "18:00",
  "weekdays": [1, 2, 3, 4, 5],
  "is_enabled": true
}
```

### 媒体管理

**POST /api/media/upload** - 上传文件

- Content-Type: multipart/form-data
- Fields: file, file_type (image/video/ppt)

**GET /api/media** - 媒体列表
**GET /api/media/{id}** - 媒体详情
**DELETE /api/media/{id}** - 删除媒体
**GET /api/media/{id}/download** - 下载文件

### 播放列表管理

**POST /api/playlists** - 创建播放列表

```json
{
  "name": "办公区轮播",
  "description": "公司大厅显示内容"
}
```

**GET /api/playlists** - 播放列表
**GET /api/playlists/{id}** - 详情
**PUT /api/playlists/{id}** - 更新
**DELETE /api/playlists/{id}** - 删除

**POST /api/playlists/{id}/items** - 添加媒体

```json
{
  "media_id": 1,
  "display_duration": 5
}
```

**DELETE /api/playlists/{pid}/items/{iid}** - 移除媒体
**PUT /api/playlists/{id}/items/reorder** - 重新排序

**POST /api/playlists/{pid}/devices/{did}** - 分配到设备

### 播放端 API

**POST /api/player/init** - 初始化

```json
{
  "device_id": "unique-device-id"
}
```

返回：设备信息、播放列表、定时配置、WebSocket URL

**GET /api/player/media/{id}/download** - 下载媒体
**GET /api/player/media/{id}/converted** - 下载转换后的视频

**POST /api/player/status** - 上报状态

```json
{
  "device_id": "unique-device-id",
  "status": "online"
}
```

### WebSocket 协议

**客户端 → 服务器**

- `device_register`: 注册设备
  ```json
  { "device_id": "xxx" }
  ```
- `heartbeat`: 心跳
  ```json
  { "device_id": 1 }
  ```

**服务器 → 客户端**

- `registered`: 注册成功
- `playlist_update`: 播放列表更新
  ```json
  {
    "playlist_id": 1,
    "action": "update",
    "timestamp": "2026-01-29T10:30:00"
  }
  ```
- `schedule_update`: 定时配置更新
- `force_sync`: 强制同步
- `reboot`: 重启命令

## 测试

### 后端 API 测试

使用 curl 或 Postman 测试 API：

```bash
# 设备注册
curl -X POST http://localhost:5000/api/devices/register \
  -H "Content-Type: application/json" \
  -d '{"device_id": "test-001", "device_name": "Test Device"}'

# 上传图片
curl -X POST http://localhost:5000/api/media/upload \
  -F "file=@/path/to/image.jpg" \
  -F "file_type=image"

# 创建播放列表
curl -X POST http://localhost:5000/api/playlists \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Playlist"}'
```

### WebSocket 测试

使用浏览器控制台：

```javascript
const socket = io("http://localhost:5000");

socket.on("connect", () => {
  console.log("Connected");
  socket.emit("device_register", { device_id: "test-001" });
});

socket.on("registered", (data) => {
  console.log("Registered:", data);
});

socket.on("playlist_update", (data) => {
  console.log("Playlist updated:", data);
});
```

## 常见问题

### PPT 转换失败

1. 检查 LibreOffice 是否安装：`which soffice`
2. 检查 pdftoppm 是否安装：`which pdftoppm`
3. 检查 ffmpeg 是否安装：`which ffmpeg`
4. 查看 Celery 日志：`celery -A app.tasks.celery_app:celery worker --loglevel=debug`

### WebSocket 连接失败

1. 检查 Redis 是否运行：`redis-cli ping`
2. 检查 CORS 配置
3. 检查防火墙规则

### Android 无法下载文件

1. 检查网络权限：`AndroidManifest.xml` 中添加 `INTERNET` 权限
2. 检查存储权限：`WRITE_EXTERNAL_STORAGE`
3. 检查 API URL 配置

## 下一步开发

1. **用户认证** - JWT 登录系统
2. **播放统计** - 记录播放次数、时长
3. **内容审核** - 上传内容审核流程
4. **多租户支持** - 组织和权限管理
5. **移动端管理** - 移动版管理后台
6. **日志系统** - 完善日志和监控
7. **自动更新** - Android APK 自动更新

## 总结

CastPlay 项目后端核心功能已全部实现，包括：

- ✅ 完整的 RESTful API
- ✅ PPT 转视频转换服务
- ✅ WebSocket 实时推送
- ✅ 数据库模型和关系

前端和 Android 端需要按照本文档的指导继续开发。所有核心逻辑和架构已经设计完成，可以直接按照模板代码实现。
