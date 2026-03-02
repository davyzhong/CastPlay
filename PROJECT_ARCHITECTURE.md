# CastPlay 项目架构文档

## 📁 项目结构总览

```
CastPlay/
├── castplay-server/          # 后端服务（Flask）
├── castplay-admin/           # 前端管理后台（React + TypeScript）
├── android-app/              # Android 播放端应用
├── docs/                     # 项目文档（建议新增）
└── scripts/                  # 部署和工具脚本（建议新增）
```

---

## 🔧 后端服务架构 (castplay-server/)

### 目录结构

```
castplay-server/
├── app/                      # 应用核心代码
│   ├── __init__.py          # 应用工厂，Flask app 初始化
│   ├── api/                 # RESTful API 路由层
│   │   ├── __init__.py     # API 蓝图导出
│   │   ├── device.py       # 设备管理 API（8个端点）
│   │   ├── media.py        # 媒体文件管理 API（6个端点）
│   │   ├── playlist.py     # 播放列表管理 API（10个端点）
│   │   └── player.py       # 播放端专用 API（4个端点）
│   │
│   ├── models/              # 数据模型层（ORM）
│   │   ├── __init__.py     # 模型导出
│   │   ├── device.py       # 设备和定时配置模型
│   │   ├── media.py        # 媒体文件模型
│   │   └── playlist.py     # 播放列表和关联模型
│   │
│   ├── services/            # 业务逻辑服务层
│   │   ├── __init__.py
│   │   └── converter.py    # PPT 转视频转换服务
│   │
│   ├── tasks/               # 异步任务（Celery）
│   │   ├── __init__.py
│   │   ├── celery_app.py   # Celery 配置和初始化
│   │   └── convert.py      # PPT 转换异步任务
│   │
│   └── websocket/           # WebSocket 实时推送
│       ├── __init__.py
│       └── handler.py       # WebSocket 事件处理器
│
├── storage/                 # 文件存储目录
│   ├── uploads/            # 用户上传的原始文件
│   ├── converted/          # PPT 转换后的视频文件
│   └── thumbnails/         # 媒体文件缩略图
│
├── migrations/              # 数据库迁移文件（Flask-Migrate）
├── config.py               # 配置文件（多环境配置）
├── run.py                  # 应用启动入口
└── requirements.txt        # Python 依赖包
```

### 核心组件说明

#### 1. API 路由层 (app/api/)

**职责**：处理 HTTP 请求，参数验证，调用业务逻辑，返回响应

| 文件          | 端点数 | 主要功能                                         |
| ------------- | ------ | ------------------------------------------------ |
| `device.py`   | 8      | 设备注册、心跳、列表、详情、更新、删除、定时配置 |
| `media.py`    | 6      | 文件上传、列表、详情、删除、下载、缩略图         |
| `playlist.py` | 10     | 播放列表 CRUD、媒体项管理、设备分配              |
| `player.py`   | 4      | 播放端初始化、版本检查、文件下载、状态上报       |

**设计模式**：

- 蓝图（Blueprint）模式实现模块化路由
- RESTful API 设计规范
- 统一的 JSON 响应格式

#### 2. 数据模型层 (app/models/)

**职责**：定义数据库表结构，封装数据访问逻辑

**核心模型**：

- `Device` - 设备基本信息
- `DeviceSchedule` - 设备定时配置（一对一）
- `MediaFile` - 媒体文件信息
- `Playlist` - 播放列表
- `PlaylistItem` - 播放列表项（多对多中间表）
- `DevicePlaylist` - 设备与播放列表关联（多对多中间表）

**关系图**：

```
Device 1:1 DeviceSchedule
Device N:M Playlist (通过 DevicePlaylist)
Playlist N:M MediaFile (通过 PlaylistItem)
```

#### 3. 业务服务层 (app/services/)

**职责**：复杂业务逻辑的封装，独立于 HTTP 请求

**converter.py**：

- PPT → PDF → 图片序列 → 视频
- 使用 LibreOffice、pdftoppm、ffmpeg
- 自动生成缩略图
- 计算 MD5 哈希值

#### 4. 异步任务层 (app/tasks/)

**职责**：处理耗时操作，避免阻塞 HTTP 请求

**convert.py**：

- 异步 PPT 转视频任务
- 自动更新转换状态
- 错误处理和重试机制

**Celery 架构**：

```
Client (API) → Redis (Broker) → Celery Worker → Database
```

#### 5. WebSocket 层 (app/websocket/)

**职责**：服务端向客户端的实时推送

**支持的事件**：

- `device_register` - 设备注册连接
- `heartbeat` - 心跳维持
- `playlist_update` - 播放列表更新通知
- `schedule_update` - 定时配置更新通知
- `force_sync` - 强制同步通知
- `reboot` - 远程重启命令

**技术栈**：Flask-SocketIO + Redis

---

## ⚛️ 前端管理后台架构 (castplay-admin/)

### 目录结构

```
castplay-admin/
├── src/
│   ├── api/                 # API 服务层
│   │   ├── client.ts       # Axios 实例配置
│   │   ├── device.ts       # 设备 API 封装
│   │   ├── media.ts        # 媒体 API 封装
│   │   └── playlist.ts     # 播放列表 API 封装
│   │
│   ├── pages/               # 页面组件
│   │   ├── Dashboard.tsx   # 仪表盘（统计概览）
│   │   ├── DeviceList.tsx  # 设备管理页面
│   │   ├── MediaList.tsx   # 媒体库管理页面
│   │   └── PlaylistList.tsx # 播放列表管理页面
│   │
│   ├── layouts/             # 布局组件
│   │   └── MainLayout.tsx  # 主布局（侧边栏+内容区）
│   │
│   ├── components/          # 可复用组件（建议新增）
│   │   ├── MediaUpload.tsx # 文件上传组件
│   │   ├── PlaylistEditor.tsx # 播放列表编辑器
│   │   └── ScheduleForm.tsx # 定时配置表单
│   │
│   ├── hooks/               # 自定义 Hooks（建议新增）
│   ├── utils/               # 工具函数（建议新增）
│   ├── types/               # TypeScript 类型定义（建议新增）
│   ├── App.tsx              # 根组件
│   ├── main.tsx             # 应用入口
│   └── index.css            # 全局样式
│
├── public/                  # 静态资源
├── index.html               # HTML 模板
├── package.json             # 依赖配置
├── tsconfig.json            # TypeScript 配置
└── vite.config.ts           # Vite 构建配置
```

### 技术栈

- **框架**：React 18.x
- **语言**：TypeScript 5.x
- **构建工具**：Vite 5.x
- **UI 库**：Ant Design 5.x
- **HTTP 客户端**：Axios
- **路由**：React Router DOM
- **状态管理**：React Hooks（建议后期引入 Zustand/Redux）

### 核心模块说明

#### 1. API 服务层 (src/api/)

**职责**：封装后端 API 调用，统一错误处理

**client.ts**：

- Axios 实例配置
- 请求/响应拦截器
- 统一错误处理
- 认证 Token 自动注入

**各 API 模块**：

- 类型安全的 API 调用封装
- Promise-based 异步调用
- 完整的 TypeScript 类型定义

#### 2. 页面组件 (src/pages/)

| 页面         | 路由         | 主要功能               | 状态        |
| ------------ | ------------ | ---------------------- | ----------- |
| Dashboard    | `/`          | 统计概览               | ✅ 基础实现 |
| DeviceList   | `/devices`   | 设备管理、定时配置     | ✅ 完整实现 |
| MediaList    | `/media`     | 媒体上传、列表展示     | ⚠️ 待完善   |
| PlaylistList | `/playlists` | 播放列表管理、拖拽排序 | ⚠️ 待完善   |

---

## 📱 Android 播放端架构 (android-app/)

### 目录结构

```
android-app/
└── app/
    ├── src/main/
    │   ├── java/com/castplay/player/
    │   │   ├── MainActivity.java          # 主活动（播放界面）
    │   │   │
    │   │   ├── network/                   # 网络层
    │   │   │   ├── RetrofitClient.java   # Retrofit 客户端单例
    │   │   │   ├── ApiService.java       # API 接口定义
    │   │   │   └── WebSocketManager.java # WebSocket 管理器
    │   │   │
    │   │   ├── data/                      # 数据层
    │   │   │   ├── db/                   # 数据库（Room）
    │   │   │   │   ├── entity/          # 实体类
    │   │   │   │   │   ├── DeviceEntity.java
    │   │   │   │   │   ├── MediaFileEntity.java
    │   │   │   │   │   └── PlaylistEntity.java
    │   │   │   │   ├── dao/             # 数据访问对象
    │   │   │   │   │   ├── MediaFileDao.java
    │   │   │   │   │   └── PlaylistDao.java
    │   │   │   │   └── AppDatabase.java # 数据库主类
    │   │   │   └── model/               # 数据模型
    │   │   │       ├── InitResponse.java
    │   │   │       ├── StatusRequest.java
    │   │   │       └── MediaItem.java
    │   │   │
    │   │   ├── service/                   # 业务服务层
    │   │   │   ├── SyncManager.java      # 同步管理器
    │   │   │   └── ScheduleManager.java  # 定时管理器
    │   │   │
    │   │   ├── player/                    # 播放引擎
    │   │   │   └── PlaybackEngine.java   # 混合播放引擎
    │   │   │
    │   │   └── receiver/                  # 广播接收器
    │   │       └── ScheduleReceiver.java # 定时任务接收器
    │   │
    │   ├── res/                           # 资源文件
    │   │   ├── layout/                   # 布局文件
    │   │   │   └── activity_main.xml
    │   │   ├── values/                   # 值资源
    │   │   └── mipmap/                   # 应用图标
    │   │
    │   └── AndroidManifest.xml            # 应用清单
    │
    └── build.gradle                       # 构建配置
```

### 技术栈

- **语言**：Java 8+
- **最低 SDK**：21 (Android 5.0)
- **目标 SDK**：33 (Android 13)
- **架构组件**：
  - Room Database - 本地数据持久化
  - Retrofit 2 - HTTP 网络请求
  - OkHttp 3 - WebSocket 连接
  - ExoPlayer 2 - 视频播放
  - Glide 4 - 图片加载

### 核心模块说明

#### 1. 网络层 (network/)

**RetrofitClient.java**：

- Retrofit 单例模式
- 自动 JSON 转换（Gson）
- 超时和重试配置

**WebSocketManager.java**：

- WebSocket 连接管理
- 自动重连机制（5 秒延迟）
- 事件监听器模式

#### 2. 数据层 (data/)

**Room 数据库**：

- 离线优先架构
- 自动迁移策略
- 事务支持

**实体类**：

- `DeviceEntity` - 设备信息缓存
- `MediaFileEntity` - 媒体文件元数据
- `PlaylistEntity` - 播放列表缓存

#### 3. 业务服务层 (service/)

**SyncManager.java**：

- 完整同步流程
- 文件下载管理
- MD5 校验
- 版本检查

**ScheduleManager.java**：

- AlarmManager 定时任务
- 工作日配置
- 时区处理

#### 4. 播放引擎 (player/)

**PlaybackEngine.java**：

- 混合播放（图片 + 视频）
- ExoPlayer 视频播放
- Glide 图片展示
- 自动循环切换
- Handler 定时控制

---

## 🔄 数据流架构

### 1. 内容发布流程

```
管理后台
  ↓ 1. 上传媒体文件
后端 API
  ↓ 2. 触发 Celery 任务（PPT转换）
Celery Worker
  ↓ 3. 转换完成，更新状态
管理后台
  ↓ 4. 创建播放列表，添加媒体
后端 API
  ↓ 5. 分配播放列表到设备
WebSocket
  ↓ 6. 推送更新通知
Android 设备
  ↓ 7. 同步数据，下载文件
本地播放
```

### 2. 设备同步流程

```
Android 启动
  ↓ 1. 调用 /api/player/init
后端返回
  ↓ 2. 播放列表 + 定时配置 + WebSocket URL
SyncManager
  ↓ 3. 保存播放列表到 Room
  ↓ 4. 下载媒体文件（MD5校验）
  ↓ 5. 设置定时任务
PlaybackEngine
  ↓ 6. 加载并播放
```

### 3. 实时推送流程

```
管理后台操作
  ↓ 1. 更新播放列表/定时配置
后端 API
  ↓ 2. 数据库更新
  ↓ 3. 调用 notify_xxx() 函数
WebSocket 服务
  ↓ 4. emit 到指定设备房间
Android WebSocket
  ↓ 5. 接收事件
  ↓ 6. 触发重新同步
```

---

## 🏗️ 设计模式

### 后端

1. **应用工厂模式**（Application Factory）

   - `create_app()` 函数创建 Flask 实例
   - 支持多环境配置注入

2. **蓝图模式**（Blueprint）

   - 模块化路由管理
   - 独立的错误处理

3. **仓储模式**（Repository）
   - 数据访问抽象
   - SQLAlchemy ORM

### 前端

1. **组件化开发**

   - 可复用组件封装
   - Props 数据流

2. **Hooks 模式**
   - 逻辑复用
   - 状态管理

### Android

1. **单例模式**（Singleton）

   - RetrofitClient
   - WebSocketManager
   - AppDatabase

2. **观察者模式**（Observer）

   - WebSocket 事件监听
   - 回调接口

3. **工厂模式**（Factory）
   - Room Database 创建

---

## 📊 数据库设计

### ER 图

```
┌─────────────┐       ┌──────────────────┐
│   Device    │──1:1──│ DeviceSchedule   │
└──────┬──────┘       └──────────────────┘
       │
       │ N:M (DevicePlaylist)
       │
┌──────┴──────┐       ┌──────────────────┐
│  Playlist   │──N:M──│   MediaFile      │
└─────────────┘       └──────────────────┘
  (PlaylistItem)
```

### 表结构说明

**device** - 设备表

- `id` - 主键
- `device_id` - 唯一设备标识（UUID）
- `device_name` - 设备名称
- `timezone` - 时区
- `last_online` - 最后在线时间
- `status` - 状态（online/offline）

**device_schedule** - 定时配置表

- `id` - 主键
- `device_id` - 外键（device.id）
- `power_on_time` - 开机时间
- `power_off_time` - 关机时间
- `is_enabled` - 是否启用
- `weekdays` - 工作日（1-7）

**media_file** - 媒体文件表

- `id` - 主键
- `file_name` - 文件名
- `file_type` - 类型（image/video/ppt）
- `file_path` - 文件路径
- `file_size` - 文件大小
- `converted_path` - 转换后路径（PPT）
- `thumbnail_path` - 缩略图路径
- `md5_hash` - MD5 哈希
- `status` - 状态（ready/processing/failed）

**playlist** - 播放列表表

- `id` - 主键
- `name` - 名称
- `description` - 描述

**playlist_item** - 播放列表项表（中间表）

- `id` - 主键
- `playlist_id` - 外键（playlist.id）
- `media_id` - 外键（media_file.id）
- `display_order` - 显示顺序
- `display_duration` - 显示时长（秒）

**device_playlist** - 设备播放列表关联表（中间表）

- `id` - 主键
- `device_id` - 外键（device.id）
- `playlist_id` - 外键（playlist.id）
- `is_active` - 是否激活

---

## 🔐 安全性考虑

### 当前实现

1. **CORS 配置** - 支持跨域请求
2. **文件类型检查** - 限制上传文件类型
3. **文件大小限制** - 最大 500MB
4. **JWT 认证**（已配置但未使用）

### 建议增强

1. **认证授权**

   - 实现 JWT 登录认证
   - 角色权限管理（超级管理员）

2. **API 安全**

   - Rate Limiting（接口限流）
   - 输入验证和过滤
   - SQL 注入防护

3. **文件安全**

   - 文件内容校验
   - 路径遍历防护
   - 病毒扫描

4. **传输安全**
   - HTTPS 加密传输
   - WebSocket TLS 加密

---

## 🚀 部署架构

### 推荐部署方案

```
┌─────────────────────────────────────────────┐
│            Nginx (反向代理 + 静态文件)          │
└────────┬─────────────────────────┬──────────┘
         │                         │
    ┌────▼─────┐            ┌──────▼──────┐
    │ Flask    │            │   React     │
    │ Server   │            │   Admin     │
    └────┬─────┘            └─────────────┘
         │
    ┌────▼─────┐
    │ Celery   │
    │ Worker   │
    └────┬─────┘
         │
    ┌────▼─────┐     ┌──────────┐
    │  Redis   │     │   DB     │
    │(消息队列) │     │(PostgreSQL)│
    └──────────┘     └──────────┘
```

### 容器化部署（建议）

```yaml
# docker-compose.yml
services:
  - flask-app # Flask 应用
  - celery-worker # Celery Worker
  - redis # Redis
  - postgresql # 数据库
  - nginx # 反向代理
```

---

## 📈 性能优化建议

### 后端

1. **数据库优化**

   - 索引优化（device_id, status）
   - 查询优化（分页、懒加载）
   - 连接池配置

2. **缓存策略**

   - Redis 缓存热点数据
   - 媒体文件 CDN 分发

3. **异步处理**
   - 所有耗时操作使用 Celery
   - WebSocket 消息队列

### 前端

1. **代码分割**

   - React.lazy() 懒加载
   - 路由级别代码分割

2. **资源优化**
   - 图片压缩
   - Gzip 压缩
   - 静态资源 CDN

### Android

1. **图片优化**

   - Glide 缓存策略
   - 图片压缩

2. **网络优化**
   - 断点续传
   - 批量下载
   - 离线优先

---

## 🧪 测试策略

### 后端测试

- **单元测试**：pytest
- **API 测试**：pytest + requests
- **集成测试**：Docker Compose

### 前端测试

- **单元测试**：Vitest
- **组件测试**：React Testing Library
- **E2E 测试**：Playwright

### Android 测试

- **单元测试**：JUnit
- **UI 测试**：Espresso

---

## 📚 开发规范

### Git 工作流

```
main        - 生产环境
  ↑
develop     - 开发环境
  ↑
feature/*   - 功能分支
bugfix/*    - 修复分支
```

### 提交信息规范

```
feat: 新功能
fix: 修复 bug
docs: 文档更新
style: 代码格式
refactor: 重构
test: 测试相关
chore: 构建/工具链
```

### 代码审查清单

- [ ] 代码符合项目规范
- [ ] 添加必要注释
- [ ] 单元测试覆盖
- [ ] 无安全隐患
- [ ] 性能可接受

---

## 🔄 版本管理

### 当前版本

- 后端：v1.0.0
- 前端：v1.0.0
- Android：v1.0.0

### 版本号规则

`主版本.次版本.修订号`

- 主版本：不兼容的 API 变更
- 次版本：向下兼容的功能新增
- 修订号：向下兼容的 bug 修复

---

## 📞 联系方式

- **项目负责人**：[待填写]
- **技术支持**：[待填写]
- **文档维护**：[待填写]

---

**最后更新**：2026-01-29
**文档版本**：v1.0
