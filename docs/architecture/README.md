# CastPlay All-in-One 项目详细说明书

## 1. 项目概述

CastPlay All-in-One 是一款一体化数字标牌管理系统，采用前后端分离架构，支持设备管理、媒体管理、播放列表管理和远程控制等功能。该项目为 v2.0 版本，采用了全新的 bootstrap 架构，实现了零依赖部署，显著提升了启动速度和运维效率。

### 1.1 项目特点
- **零依赖部署**：无需 Redis、Celery、PostgreSQL 等外部依赖
- **一体化设计**：后端 + 前端 + 数据库，开箱即用
- **极速启动**：5 分钟完成部署，10 秒启动
- **小规模优化**：专为 <50 设备场景设计
- **代码精简**：相比原项目减少 34% 代码量

### 1.2 技术指标对比
| 指标 | CastPlay | All-in-One v2.0 | 改进 |
|------|----------|------------------|------|
| 代码量 | 8,106 行 | 5,330 行 | -34% ✅ |
| Python 文件 | 79 个 | 36 个 | -54% ✅ |
| 外部依赖 | Redis+Celery+PG | 无 | -100% ✅ |
| 部署时间 | 30 分钟 | 5 分钟 | -83% ✅ |
| 启动时间 | ~2 分钟 | ~10 秒 | -92% ✅ |
| 运维成本 | 高 | 几乎为零 | -90% ✅ |

## 2. 后端架构分析

### 2.1 技术栈
- **框架**: FastAPI
- **数据库**: SQLite (SQLAlchemy ORM)
- **调度器**: APScheduler
- **认证**: JWT + bcrypt
- **日志**: loguru
- **类型检查**: Pydantic

### 2.2 项目结构
```
app/
├── api/              # API 路由
├── bootstrap/        # 应用引导模块
├── models/           # 数据模型
├── schemas/          # Pydantic 模型
├── services/         # 业务服务
├── utils/            # 工具函数
├── websocket/        # WebSocket 处理
└── workers/          # 工作进程
```

### 2.3 数据模型
#### 2.3.1 用户模型 (User)
- 用户认证和权限管理

#### 2.3.2 设备模型 (Device)
- 设备唯一标识 (UUID)
- 设备名称、时区、网络信息
- 设备状态 (在线/离线)
- 设备类型 (web_browser, android_tv)
- 播放状态 (当前播放列表、最后播放媒体)

#### 2.3.3 媒体模型 (MediaFile)
- 文件信息 (名称、类型、路径、大小)
- 转换后文件路径 (PPT 转视频)
- 缩略图路径
- 文件状态 (就绪/处理中/失败)

#### 2.3.4 播放列表模型 (Playlist)
- 播放列表基本信息
- 播放列表项关联
- 设备分配关联
- 系统播放列表标识

#### 2.3.5 播放列表项模型 (PlaylistItem)
- 媒体文件关联
- 显示顺序和持续时间

#### 2.3.6 设备播放列表关联模型 (DevicePlaylist)
- 设备与播放列表的关联关系
- 播放列表分配给设备后立即生效

### 2.4 API 接口
#### 2.4.1 设备管理接口 (/api/devices/)
- `POST /register` - 设备注册
- `GET /` - 获取设备列表
- `GET /{device_id}` - 获取设备详情
- `PUT /{device_id}` - 更新设备信息
- `PUT /{device_id}/disable` - 启用/禁用设备
- `POST /{device_id}/schedule` - 设置设备定时配置
- `GET /{device_id}/schedule` - 获取设备定时配置
- `GET /{device_id}/cached-media` - 获取设备缓存媒体
- `GET /{device_id}/playlists` - 获取设备关联播放列表

#### 2.4.2 媒体管理接口 (/api/media/)
- `POST /upload` - 上传媒体文件
- `GET /` - 获取媒体列表
- `GET /{media_id}` - 获取媒体详情
- `DELETE /{media_id}` - 删除媒体文件
- `GET /{media_id}/download` - 下载媒体文件
- `GET /{media_id}/thumbnail` - 获取缩略图
- `POST /{media_id}/retry` - 重试 PPT 转换

#### 2.4.3 播放列表接口 (/api/playlists/)
- `POST /` - 创建播放列表
- `GET /` - 获取播放列表列表
- `GET /{playlist_id}` - 获取播放列表详情
- `PUT /{playlist_id}` - 更新播放列表
- `DELETE /{playlist_id}` - 删除播放列表
- `POST /{playlist_id}/items` - 添加媒体到播放列表
- `PUT /{playlist_id}/items/{item_id}` - 更新播放列表项
- `DELETE /{playlist_id}/items/{item_id}` - 移除播放列表项
- `PUT /{playlist_id}/items/reorder` - 重排序播放列表项
- `POST /{playlist_id}/devices/{device_id}` - 分配播放列表到设备
- `DELETE /{playlist_id}/devices/{device_id}` - 取消设备分配

#### 2.4.4 认证接口 (/api/auth/)
- `POST /token` - 获取访问令牌
- `POST /refresh` - 刷新令牌
- `GET /me` - 获取当前用户信息

#### 2.4.5 播放端接口 (/api/player/)
- `GET /playlists/{device_id}` - 获取设备播放列表
- `GET /config/{device_id}` - 获取设备配置
- `POST /status/{device_id}` - 上报播放状态

### 2.5 WebSocket 通信
- **连接端点**: `/ws/{device_id}`
- **消息类型**:
  - 播放列表分配/更新/移除
  - 设备配置更新
  - 定时配置更新
  - 播放控制指令
  - 心跳机制

### 2.6 文件处理服务
- **PPT 转换**: PPT → PDF → 图片序列 → 视频
- **缩略图生成**: 为媒体文件生成预览图
- **文件验证**: 扩展名和 Magic Number 验证
- **文件上传**: 支持图片、视频、PPT 格式

### 2.7 任务调度
- **PPT 转换任务**: 使用 APScheduler 后台处理
- **定时配置**: 设备定时开关机功能
- **3个工作线程**: 支持并发任务处理

## 3. 前端架构分析

### 3.1 技术栈
- **框架**: React 18
- **UI 库**: Ant Design 5
- **状态管理**: Zustand
- **路由**: React Router DOM
- **拖拽**: @dnd-kit
- **HTTP 客户端**: Axios

### 3.2 项目结构
```
frontend/
├── src/
│   ├── api/          # API 客户端
│   ├── components/   # 通用组件
│   ├── pages/        # 页面组件
│   ├── store/        # 状态管理
│   ├── types/        # TypeScript 类型定义
│   ├── utils/        # 工具函数
│   ├── App.tsx       # 应用入口
│   └── main.tsx      # 主入口文件
├── public/           # 静态资源
└── package.json      # 依赖配置
```

### 3.3 页面组件
#### 3.3.1 登录页面 (Login)
- JWT 认证
- 令牌管理

#### 3.3.2 仪表盘 (Dashboard)
- 系统概览
- 统计信息展示

#### 3.3.3 设备管理 (DeviceList)
- 设备列表展示
- 设备状态管理
- 设备注册码管理
- 设备定时配置

#### 3.3.4 媒体库 (MediaList)
- 媒体文件上传 (支持拖拽)
- 媒体列表展示
- 缩略图预览
- 文件状态管理
- PPT 转换重试

#### 3.3.5 播放列表 (PlaylistList)
- 播放列表创建/管理
- 媒体拖拽排序
- 批量添加媒体
- 播放列表预览
- 设备分配管理

#### 3.3.6 Web播放端模拟器 (WebPlayerSimulator)
- 播放端模拟功能
- 实时预览

### 3.4 API 客户端
- 统一的请求拦截器
- 错误处理机制
- 认证令牌自动附加

### 3.5 类型定义
- 用户、设备、媒体、播放列表等实体类型
- API 响应类型
- WebSocket 消息类型

## 4. 核心业务逻辑与数据流

### 4.1 设备注册流程
1. 设备向 `/api/devices/register` 发起注册请求
2. 系统检查设备是否已存在 (按 device_id 或 MAC 地址)
3. 若存在则更新状态，若不存在则创建新设备记录
4. 生成注册码 (基于 device_id 的哈希)
5. 返回设备信息，建立 WebSocket 连接

### 4.2 媒体上传与处理流程
1. 用户通过前端界面上传媒体文件
2. 后端验证文件类型和大小
3. 保存文件并计算 MD5 哈希
4. 生成缩略图 (图片类型)
5. 对 PPT 文件启动后台转换任务
6. 更新文件状态 (PPT 文件初始为 processing)

### 4.3 播放列表管理流程
1. 管理员创建播放列表
2. 向播放列表添加媒体文件
3. 调整媒体播放顺序和时长
4. 将播放列表分配给特定设备
5. 通过 WebSocket 通知设备更新

### 4.4 设备控制流程
1. 管理员在后台更改设备配置
2. 系统通过 WebSocket 发送通知到目标设备
3. 设备接收并执行相应操作
4. 设备可上报状态变更

### 4.5 数据流向
```
前端界面 ←→ REST API ←→ 业务逻辑 ←→ 数据库
     ↓           ↓         ↓         ↓
WebSocket ←→ 通知服务 ←→ 任务调度 ←→ 文件系统
```

## 5. 部署与运行

### 5.1 系统要求
- Python 3.10+
- Node.js 18+ (前端开发)
- LibreOffice (PPT 转换)
- ffmpeg (视频处理)

### 5.2 后端部署
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python scripts/init_db.py

# 启动服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

### 5.3 前端部署
```bash
# 安装依赖
npm install

# 开发模式
npm run dev

# 构建生产版本
npm run build
```

### 5.4 访问地址
- 管理后台: http://localhost:8000/
- API 文档: http://localhost:8000/docs
- API 文档 (ReDoc): http://localhost:8000/redoc

## 6. 项目特色功能

### 6.1 播放列表预览
- 支持在管理端预览播放列表效果
- 可调整播放速度
- 支持逐个媒体预览

### 6.2 拖拽排序
- 播放列表中支持拖拽调整媒体顺序
- 实时保存排序结果

### 6.3 批量操作
- 批量添加媒体到播放列表
- 批量选择和预览媒体

### 6.4 设备管理
- 设备在线状态监控
- 设备禁用/启用功能
- 设备定时开关机配置
- 设备注册码找回功能

### 6.5 文件处理
- 支持多种媒体格式 (图片、视频、PPT)
- PPT 自动转换为视频
- 自动生成缩略图
- 文件内容验证

### 6.6 WebSocket 实时通信
- 设备状态实时同步
- 播放列表即时推送
- 播放控制指令下发

## 7. 扩展性设计

### 7.1 插件化架构
- 通过 bootstrap 模块统一管理初始化流程
- 易于添加新的功能模块

### 7.2 配置管理
- 使用 Pydantic Settings 进行配置管理
- 支持环境变量覆盖

### 7.3 模块化设计
- 功能模块职责清晰分离
- 便于独立开发和测试

## 8. Android端实现

### 8.1 Android端概述
CastPlay All-in-One 提供了完整的Android端播放器实现，作为数字标牌系统的终端播放设备。Android端采用WebView容器承载前端播放器界面，同时提供原生功能支持，如设备管理、媒体缓存、网络监控等。

### 8.2 Android端技术栈
- **开发语言**: Kotlin
- **目标SDK**: API Level 34 (Android 14)
- **最低支持**: API Level 26 (Android 8.0)
- **构建系统**: Gradle (Kotlin DSL)
- **UI框架**: WebView + 原生组件
- **网络**: HttpURLConnection + DownloadManager

### 8.3 Android端架构
```
android/
├── app/                    # 应用模块
│   ├── src/main/
│   │   ├── java/com/castplay/player/
│   │   │   ├── MainActivity.kt      # 主Activity，WebView宿主
│   │   │   ├── JsBridge.kt          # JavaScript桥接接口
│   │   │   ├── CacheManager.kt      # 媒体缓存管理
│   │   │   ├── CastPlayApplication.kt # 应用程序类
│   │   │   ├── BootReceiver.kt      # 开机启动接收器
│   │   │   ├── ErrorReporter.kt     # 错误上报
│   │   │   └── MyDeviceAdminReceiver.kt # 设备管理接收器
│   │   ├── res/                     # 资源文件
│   │   ├── assets/www/              # 前端资源（构建时复制）
│   │   └── AndroidManifest.xml      # 应用配置
├── build.gradle.kts        # 项目构建配置
├── app/build.gradle.kts    # 应用模块构建配置
├── settings.gradle.kts     # 模块设置
└── build-android.sh        # 自动化构建脚本
```

### 8.4 核心功能实现

#### 8.4.1 MainActivity
- **Kiosk模式**: 通过DevicePolicyManager实现设备锁定，防止用户退出应用
- **全屏显示**: 隐藏系统栏，保持沉浸式体验
- **WebView容器**: 加载前端播放器界面，支持离线优先策略
- **网络容错**: 当服务器不可达时自动降级到本地资源
- **生命周期管理**: 正确处理应用生命周期事件

#### 8.4.2 JsBridge (JavaScript桥接)
提供原生功能访问接口：
- `getMacAddress()`: 获取设备MAC地址
- `getIPAddress()`: 获取设备IP地址
- `getDeviceId()`: 生成设备唯一ID
- `getRegistrationCode()`: 生成设备注册码
- `downloadMedia()`: 下载媒体文件
- `getDownloadProgress()`: 获取下载进度
- `isMediaCached()`: 检查媒体是否已缓存
- `getCachedMediaPath()`: 获取缓存媒体路径
- `getLocalTimezone()`: 获取本地时区
- `showToast()`: 显示Toast消息
- `isNetworkAvailable()`: 检查网络可用性

#### 8.4.3 CacheManager (缓存管理)
- **下载管理**: 使用Android DownloadManager处理媒体文件下载
- **MD5校验**: 下载完成后进行完整性校验
- **重试机制**: 失败时自动重试（最多3次，指数退避）
- **存储管理**: 自动清理旧文件，防止存储空间耗尽
- **进度监控**: 实时跟踪下载进度并通知前端
- **智能清理**: 根据存储空间自动清理非必要文件

#### 8.4.4 Kiosk模式实现
- **设备管理员**: 通过MyDeviceAdminReceiver获得设备管理权限
- **应用锁定**: 防止用户退出播放器应用
- **开机自启**: 通过BootReceiver实现开机自动启动

### 8.5 Android端配置

#### 8.5.1 权限配置
```xml
<!-- 网络权限 -->
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
<uses-permission android:name="android.permission.ACCESS_WIFI_STATE" />

<!-- 存储权限 -->
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />

<!-- 设备管理权限 -->
<uses-permission android:name="android.permission.BIND_DEVICE_ADMIN" />

<!-- 开机启动 -->
<uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" />
```

#### 8.5.2 构建配置
- **编译SDK**: API Level 34
- **最小SDK**: API Level 26
- **混淆配置**: release版本启用代码混淆和资源压缩
- **服务器URL**: 支持构建时配置服务器地址

### 8.6 环境搭建与依赖

#### 8.6.1 开发环境要求
- **JDK**: 17或更高版本
- **Android SDK**: API Level 34
- **Android Studio**: Flamingo | 2022.2.1或更高版本
- **Gradle**: 8.2或更高版本
- **NDK**: (可选) 用于原生库开发

#### 8.6.2 依赖库
```kotlin
// 核心库
implementation("androidx.core:core-ktx:1.12.0")
implementation("androidx.appcompat:appcompat:1.6.1")
implementation("com.google.android.material:material:1.11.0")
implementation("androidx.constraintlayout:constraintlayout:2.1.4")
implementation("androidx.webkit:webkit:1.8.0")

// 测试库
testImplementation("junit:junit:4.13.2")
androidTestImplementation("androidx.test.ext:junit:1.1.5")
androidTestImplementation("androidx.test.espresso:espresso-core:3.5.1")
```

### 8.7 测试方案

#### 8.7.1 Android端测试
- **单元测试**: 使用JUnit测试业务逻辑
- **集成测试**: 测试与后端API的交互
- **UI测试**: 使用Espresso测试UI组件
- **设备测试**: 在真实Android设备上验证功能

#### 8.7.2 测试文件
- `tests/integration/test_android_features.py`: Android端功能测试
- 测试内容包括：
  - MAC地址注册
  - 注册码生成
  - 播放速度配置
  - 播放列表版本控制
  - 缓存媒体管理
  - IP地址处理

### 8.8 构建与打包

#### 8.8.1 构建脚本 (build-android.sh)
自动化构建流程：
1. 构建前端资源 (`npm run build`)
2. 复制前端文件到Android assets目录
3. 使用Gradle构建Android APK
4. 支持构建时指定服务器URL

#### 8.8.2 构建命令
```bash
# 基础构建（使用默认服务器地址）
./build-android.sh

# 指定服务器地址构建
./build-android.sh http://192.168.1.100:8000
```

#### 8.8.3 构建产物
- **APK位置**: `android/app/build/outputs/apk/debug/app-debug.apk`
- **APK大小**: 约20-30MB（取决于前端资源大小）
- **安装命令**: `adb install -r android/app/build/outputs/apk/debug/app-debug.apk`

### 8.9 部署与安装

#### 8.9.1 设备准备
1. 启用开发者选项和USB调试
2. （可选）设置设备为Kiosk模式（需要设备管理员权限）
3. 确保网络连接正常

#### 8.9.2 安装步骤
1. 通过ADB安装APK
2. 首次启动时授予必要权限
3. 配置服务器地址（如果需要）

#### 8.9.3 验证步骤
1. 启动应用，检查是否正常加载播放器界面
2. 验证设备注册功能
3. 测试媒体播放功能
4. 验证WebSocket连接状态
5. 检查缓存功能是否正常工作

### 8.10 运维与监控

#### 8.10.1 日志监控
- **应用日志**: 使用Logcat查看应用运行日志
- **错误上报**: 通过ErrorReporter收集和上报错误信息
- **性能监控**: 监控内存使用、CPU占用等指标

#### 8.10.2 设备管理
- **远程控制**: 通过WebSocket发送控制指令
- **状态监控**: 实时监控设备在线状态
- **故障恢复**: 自动重连和错误恢复机制

### 8.11 扩展性考虑

#### 8.11.1 功能扩展
- **插件化**: 通过JsBridge可以扩展更多原生功能
- **模块化**: 代码结构支持功能模块化开发
- **配置化**: 支持运行时动态配置

#### 8.11.2 性能优化
- **缓存策略**: 智能缓存管理，减少网络依赖
- **资源优化**: 图片压缩、视频预处理等
- **内存管理**: 避免内存泄漏，优化GC性能