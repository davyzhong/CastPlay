# CLAUDE_zhCN.md

本文件为 Claude Code (claude.ai/code) 在本项目工作时提供指导。

## 项目概述

CastPlay 是一款轻量级数字标牌管理系统，支持 Android 设备离线播放。主要功能：

- 多格式媒体支持（图片、视频、PPT 自动转换）
- WebSocket 实时推送播放列表更新
- Web 管理后台（设备管理和内容管理）
- Android 客户端离线缓存

## 常用命令

### 开发服务器

```bash
# 启动后端（端口 8000）
python scripts/server/start.py
# 或使用 uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 启动前端开发服务器（端口 3000）
cd frontend && npm run dev

# 同时启动前后端（并行）
make dev
```

### 数据库管理

```bash
python scripts/db/init.py      # 初始化数据库
python scripts/db/backup.py    # 备份数据库
python scripts/migration/      # 数据库迁移脚本（添加列等）
```

### 测试

```bash
pytest tests/                          # 所有测试
pytest tests/unit/ -v                  # 仅单元测试
pytest tests/integration/ -v           # 仅集成测试
pytest tests/ -m "not slow" --maxfail=5  # 快速测试
pytest tests/ -k "test_name" -v        # 运行特定测试
```

### 代码质量

```bash
make lint       # 运行所有检查器（black, isort, mypy, pylint）
make format     # 自动格式化（black + isort）
ruff check app/  # 快速检查
```

### 前端

```bash
cd frontend
npm run dev          # 开发服务器
npm run build        # 生产构建
npm run lint         # ESLint 检查
npm run test         # Vitest 测试
```

### Android

```bash
./build-android.sh [serverUrl]  # 构建 APK 并注入服务器地址
```

### CLI 工具

```bash
castplay devices list              # 列出所有设备
castplay control pause <device_id> # 控制播放（暂停）
castplay status                    # 系统状态
castplay --help                    # 查看所有命令
```

## 架构

### 后端（FastAPI + SQLite）

```
app/
├── main.py              # FastAPI 入口，WebSocket 端点
├── config.py            # Pydantic Settings 配置
├── database.py          # SQLAlchemy 会话管理
├── scheduler.py         # 后台任务调度器
├── bootstrap/           # 应用初始化模块
├── api/                 # API 路由处理器
│   ├── auth.py         # 认证端点
│   ├── devices.py      # 设备 CRUD
│   ├── media.py        # 媒体文件上传/转换
│   ├── playlists.py    # 播放列表管理
│   ├── player.py       # 播放器 API
│   └── control.py      # 远程控制命令
├── models/              # SQLAlchemy ORM 模型
├── schemas/             # Pydantic 请求/响应模型
├── services/            # 业务逻辑服务
│   ├── converter.py    # PPT 转视频
│   └── notification.py # WebSocket 通知服务
├── utils/               # 工具函数
└── websocket/           # WebSocket 连接管理器
```

关键模式：
- Bootstrap 模块处理所有启动初始化（数据库、目录、路由、调度器）
- `main.py` 中的 WebSocket 端点处理设备连接和心跳
- Services 层将业务逻辑与 API 路由分离
- SQLite + SQLAlchemy ORM，无外部依赖

### 前端（React + TypeScript + Vite）

```
frontend/src/
├── App.tsx              # 主应用，含路由
├── main.tsx             # 入口
├── player-main.tsx      # 播放器页面入口（多页面应用）
├── pages/               # 页面组件
│   ├── Dashboard.tsx    # 主仪表盘
│   ├── DeviceList.tsx   # 设备管理
│   ├── MediaList.tsx    # 媒体库
│   ├── PlaylistList.tsx # 播放列表
│   └── WebPlayerSimulator.tsx  # Web 播放器模拟器
├── player/              # 播放器相关组件
├── store/               # Zustand 状态管理
└── utils/               # API 客户端和工具
```

关键模式：
- Vite 多页面构建（admin index.html + player.html）
- Zustand 状态管理
- Ant Design UI 组件
- 相对路径确保 Android WebView 兼容

### Android（Kotlin）

```
android/app/src/main/java/com/castplay/player/
├── MainActivity.kt      # WebView 主界面
├── CacheManager.kt      # 离线媒体缓存
├── JsBridge.kt          # JavaScript 桥接
└── network/             # 网络工具
```

### MCP 服务器

位于 `mcp/`:
- `ppt-converter/` - PPT 转视频/图片转换工具
- `android-tools/` - Android SDK 集成（模拟器、APK）

## 核心端点

| 端点 | 用途 |
|------|------|
| `GET /` | 管理后台界面 |
| `GET /player.html` | 播放器界面 |
| `WS /ws/{device_id}` | 设备 WebSocket 通信 |
| `POST /api/auth/login` | 认证 |
| `/api/devices/*` | 设备管理 |
| `/api/media/*` | 媒体上传/转换 |
| `/api/playlists/*` | 播放列表管理 |
| `/api/player/{device_id}/*` | 播放器专用 API |

## 配置

- 环境变量通过 `.env` 文件（见 `.env.example`）
- 关键配置：`SECRET_KEY`（生产环境必填）、`ENVIRONMENT`、`DATABASE_PATH`
- 开发模式：自动生成密钥，允许任意来源 CORS

## 代码规范

- Python 行长：100 字符
- 格式化：Black + isort（black 配置）
- 检查：ruff, mypy, pylint
- 提交风格：Conventional Commits（`feat:`、`fix:`、`chore:` 等）
- 可用 pre-commit 钩子：`pre-commit install`

## 文件存储

```
data/
├── castplay.db          # SQLite 数据库
├── uploads/             # 原始上传文件
├── converted/           # 转换后媒体（PPT→视频）
└── thumbnails/          # 生成的缩略图
```

## 播放器配置 UI（003-player-config-ui）

### 功能概述

播放器配置 UI 提供三个首次设置的关键功能：

1. **服务器配置（US1）** - 首次启动时配置服务器 IP/域名
2. **设备注册码（US2）** - 显示注册码供管理员配对
3. **播放列表选择（US3）** - 多选播放列表

### 播放器启动流程

```
1. 检查服务器配置 → 如未配置，显示 ServerConfigDialog
2. 连接服务器 → 通过 useDeviceRegistration 自动注册
3. 检查注册码 → 如有注册码但无播放列表，显示 RegistrationCodeDisplay
4. 检查播放列表选择 → 如有多个播放列表，显示 PlaylistSelectionModal
5. 开始播放 → 播放选中的播放列表
```

### 关键组件

| 组件 | 用途 |
|------|------|
| `ServerConfigDialog` | 服务器 IP/域名输入、连接测试、协议检测 |
| `RegistrationCodeDisplay` | 显示注册码，复制到剪贴板 |
| `PlaylistSelectionModal` | 多选播放列表，全选/取消全选 |
| `SettingsButton` | 悬浮齿轮图标，重新打开服务器配置 |

### 关键 Hook

| Hook | 用途 |
|------|------|
| `useServerConfig` | 服务器配置管理、连接测试 |
| `useRegistrationCode` | 构建时注册码，注册状态 |
| `usePlaylistSelection` | 播放列表多选并持久化 |
| `useDeviceRegistration` | 与服务器自动注册设备 |

### 存储键

配置通过以下键持久化：

```typescript
// frontend/src/player/types/config.ts
STORAGE_KEYS = {
  SERVER_CONFIG: 'castplay_server_config',
  DEVICE_REGISTRATION: 'castplay_device_registration',
  PLAYLIST_SELECTION: 'castplay_playlist_selection',
}
```

### 环境变量

- `REGISTRATION_CODE` - 构建时注册码（嵌入 APK/web 构建）
- 示例：`REGISTRATION_CODE=ABC123 npm run build`

### Android 集成

`AndroidBridge` 接口提供存储方法：

```typescript
interface AndroidBridge {
  getConfig(key: string): string;
  setConfig(key: string, value: string): void;
  copyToClipboard(text: string): boolean;
  // ... 其他方法
}
```

### 错误处理

- `ConfigErrorBoundary` - 捕获配置错误，提供重试/清除选项
- `LoadingOverlay` - 配置操作的加载状态
- `ConfigLogger` - 统一的配置日志

## 技术栈

- Python 3.10+, TypeScript 5.x + FastAPI, SQLAlchemy, Pydantic, React, Zustand, Ant Design, APScheduler (001-playlist-scheduling)
- SQLite (via SQLAlchemy ORM) (001-playlist-scheduling)
- TypeScript 5.2+, Python 3.10+ + React 18, FastAPI, Ant Design 5, Zustand, SQLite (003-player-config-ui)
- localStorage (web), SharedPreferences/DataStore via JsBridge (Android) (003-player-config-ui)

## 近期变更

- 001-playlist-scheduling: 新增 Python 3.10+, TypeScript 5.x + FastAPI, SQLAlchemy, Pydantic, React, Zustand, Ant Design, APScheduler

## 相关文档

- [优化建议文档](./docs/OPTIMIZATION.md) - 项目代码审查结果和 production 化建议
