---
name: CastPlay All-in-One
description: 单容器数字标牌管理系统 — FastAPI 后端 + React 管理端 + Android 播放端，无需 Redis/Celery/PostgreSQL。针对 50 块屏以下的场景做了专项优化。
license: MIT
homepage: https://github.com/davyzhong/CastPlay
language: zh-Hans
---

<div align="center">

# 🖥️ CastPlay All-in-One

**单容器数字标牌 — 10 秒拉起。一个 Web 控制台，管设备、传素材、推播放列表。**

`上传素材` → `编排播放列表` → `推送到设备` → `2 秒内屏幕同步更新`

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.0.0-success)](https://github.com/davyzhong/CastPlay/releases)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python)](https://www.python.org)
[![Docker](https://img.shields.io/badge/docker-ready-blue?logo=docker)](Dockerfile)
[![Backend](https://img.shields.io/badge/backend-FastAPI%20%2B%20SQLAlchemy-009688)](https://fastapi.tiangolo.com)
[![Frontend](https://img.shields.io/badge/admin-React%2018%20%2B%20Ant%20Design-61dafb)](https://react.dev)
[![Player](https://img.shields.io/badge/player-Android%20WebView-3DDC84)](android/)
[![Security](https://img.shields.io/badge/security-policy-lightgrey)](SECURITY.md)

**Languages**: [English](./README.md) · [中文](./README.zh.md)

[快速开始](#-快速开始) · [安装](#-安装) · [架构](#-架构) · [API](#-api-接口) · [Android 播放端](#-android-播放端) · [同类对比](#-同类对比) · [贡献](#-贡献)

</div>

---

> 一个进程跑一整套：管理端 + REST + WebSocket、多格式素材（含 PPT）、Kiosk 模式 Android 客户端。无需 Redis、无需 Celery、无需独立数据库。

---

## ✨ 为什么选 CastPlay

- **🚀 单容器、零外部依赖** — `docker run castplay` 把管理端 + API + WebSocket 全部拉起。无需 Redis、Celery、单独的数据库服务。
- **🖼️ 多格式素材，含 PPT** — 拖入 `.pptx`，服务端通过 LibreOffice + ffmpeg 转码为视频，原幻灯片动画保留。
- **📡 实时推送到每一块屏** — 播放列表和定时配置通过 WebSocket 派发，客户端 ≈ 2 秒内生效，无需轮询。
- **📱 Kiosk 锁定 Android 播放端** — `MainActivity.kt` 是带 `DevicePolicyManager` 锁定模式的 WebView，设备始终只能看你推的内容。
- **📅 定时 + 多时区** — 每台设备独立的每日开关机窗口，多时区支持，自动回退到默认播放列表。
- **🔍 为 50 块屏以下优化** — SQLite 持久化、APScheduler 调度、3 个 worker 线程。这个规模再上 Redis/Celery/PG 是过度设计。

---

## 🚀 快速开始

### 30 秒 — 用 Docker 试用

```bash
docker run -d \
  --name castplay \
  -p 8000:8000 \
  -v castplay-data:/app/data \
  ghcr.io/davyzhong/castplay:latest
# 或本地构建：
# docker build -t castplay:latest . && docker compose up -d
```

打开 <http://localhost:8000/> 进入管理后台，<http://localhost:8000/player.html> 进入 Web 播放端预览。

### 60 秒 — 从源码（不用 Docker）

```bash
# 1. 克隆
git clone https://github.com/davyzhong/CastPlay.git
cd CastPlay

# 2. 安装系统依赖（Ubuntu/Debian 包名）
sudo apt-get update && sudo apt-get install -y libreoffice ffmpeg

# 3. 后端
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/init_db.py

# 4. 前端（本地开发时；预编译资源已合入仓库）
cd frontend && npm install && npm run build && cd ..

# 5. 跑起来
python scripts/run.py
# 或：make dev
```

- **管理后台** → <http://localhost:8000/>
- **Web 播放端** → <http://localhost:8000/player.html>
- **OpenAPI 文档** → <http://localhost:8000/docs>

### 默认账号

首次启动会自动 seed：

```
username: admin
password: changeme    # 生产环境请通过 .env 覆盖
```

> 加固清单见 [`docs/deployment/guide.md`](docs/deployment/guide.md)。

---

## 📸 它跑起来长什么样

> ⚠️ 真实截图用 `[TODO]` 占位。跑起来后截屏放进 `docs/screenshots/`，占位会自动替换。

### 管理后台

<p align="center">
  <a href="docs/screenshots/dashboard.png"><img src="docs/screenshots/dashboard.png" width="320" alt="CastPlay 管理后台仪表盘：设备在线/离线/总数卡片、最近上传、最后推送时间戳"></a>
  <a href="docs/screenshots/playlists.png"><img src="docs/screenshots/playlists.png" width="320" alt="播放列表编辑器：素材磁贴在拖拽顺序栏里，每项独立时长滑块，设备分配下拉"></a>
</p>
<p align="center"><sub><em>[TODO: dashboard.png] · [TODO: playlists.png]</em></sub></p>

### 媒体库 + Android 播放端

<p align="center">
  <a href="docs/screenshots/media.png"><img src="docs/screenshots/media.png" width="320" alt="媒体库：上传的图片、视频、转换后的 PPT 缩略图网格，带状态徽标"></a>
  <a href="docs/screenshots/android-player.png"><img src="docs/screenshots/android-player.png" width="320" alt="Android 播放端在 10 寸屏上全屏显示图片轮播 + 视频，无系统 chrome"></a>
</p>
<p align="center"><sub><em>[TODO: media.png] · [TODO: android-player.png]</em></sub></p>

---

## 🏗️ 架构

```mermaid
flowchart TB
    subgraph Browser[管理浏览器]
        Admin[管理后台<br/>React 18 + Ant Design]
        PlayerWeb[Web 播放端<br/>player.html]
    end
    subgraph Server[CastPlay 服务端 — 单进程]
        API[REST API<br/>FastAPI]
        WS[WebSocket<br/>/ws/{device_id}]
        Sched[调度器<br/>APScheduler · 3 worker]
        PptSvc[PPT 转码<br/>LibreOffice + ffmpeg]
        DB[(SQLite<br/>SQLAlchemy ORM)]
        Files[本地存储<br/>uploads / converted / thumbnails]
    end
    subgraph Devices[播放端]
        Web[浏览器播放端]
        Android[Android WebView<br/>Kiosk 模式 · CacheManager]
    end
    Admin -->|REST + WebSocket| API
    PlayerWeb -->|REST + WebSocket| API
    Web -->|REST + WebSocket| API
    Android -->|REST + WebSocket| API
    Sched --> API
    PptSvc --> Files
    API --> DB
    API --> Files
    WS --> Devices
```

**推送路径**：管理端 → `POST /api/playlists/{id}/devices/{deviceId}` → WebSocket 扇出 → 连接的客户端收到 diff 并重建本地播放列表。

---

## 📦 功能

### 🖼️ 素材管理

- 🧩 **多格式支持** — JPG/PNG/GIF 图片、MP4/AVI/MOV 视频、PPT/PPTX 幻灯片。
- 🎞️ **PPT → 视频管道** — LibreOffice 转 PDF、Poppler 拆页、ffmpeg 串成 MP4。
- 🔁 **单文件重试** — 失败的转码在管理端有一键重试按钮（`POST /api/media/{id}/retry`）。
- 🔍 **内容校验** — 扩展名 + Magic Number 双校验，不匹配的拒绝写入磁盘。
- 🖼️ **缩略图生成** — Pillow 为图片与 PPT 首页生成预览图。

### 📋 播放列表与设备

- 🎯 **拖拽排序** — 管理端用 `@dnd-kit`，排序通过 `PUT /api/playlists/{id}/items/reorder` 持久化。
- 📡 **≈ 2 秒同步** — 改动通过 WebSocket 推下去，设备无需轮询。
- 🎚️ **单条独立时长** — 每段播放多久单独配，默认 8 秒。
- 🎞️ **Web 播放端模拟器** — 分配之前在浏览器里整段预览（`/player.html`）。
- 📅 **定时感知** — 每设备每日开关机窗口、多时区、自动回退到默认播放列表。

### 🛡️ 运维

- 🖥️ **设备注册** — 以 MAC 地址为键的注册表，`registration_code` 作为生产环境 token 凭据。
- 🔐 **JWT + bcrypt** — 通过 `/api/auth/refresh` 轮换 token，`.env` 里轮换 `SECRET_KEY`。
- 🧹 **自清理存储** — Android `CacheManager.kt` 在存储用满前主动回收。
- 🚦 **3-worker 调度器** — PPT 转码 + 定时评估的并发上限。
- 🔁 **自动重连** — 设备网络断连后自动恢复，WebSocket 心跳保活。

### 📱 播放端

- 🌐 **浏览器播放端** — `frontend/player.html` 与 Android WebView 跑同一份代码。
- 🤖 **Android 播放端** — `MainActivity.kt` 是带 `DevicePolicyManager` 锁定模式 + `CacheManager.kt` 离线优先策略的 WebView 宿主。

---

## 🔧 安装

### 1. 系统前置

| 工具 | 用途 | 验证版本 |
|---|---|---|
| Python | 后端 | 3.10+ |
| Node.js | 前端开发模式 | 18+ |
| LibreOffice | PPT → PDF | 7+ |
| ffmpeg | 媒体拼接 | 4.4+ |
| Docker（可选） | 单次部署 | 24+ |

### 2. 安装路径

#### Docker（推荐）

```bash
docker compose up -d             # 用 docker-compose.yml
# 或
docker build -t castplay . && docker run -d -p 8000:8000 -v castplay-data:/app/data castplay
```

#### Pip + npm（开发者模式）

```bash
# 后端
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/init_db.py
python scripts/run.py

# 前端（可选 — 仓库内已带预编译资源）
cd frontend && npm install && npm run dev
```

#### Make（开发者快捷方式）

```bash
make install          # pip + npm install
make dev              # 后端 + 前端并行
make test             # pytest
make lint             # black + isort + mypy + pylint
make docker-build     # 构建镜像
make docker-run       # docker compose up
```

### 3. 配置

CastPlay 读取环境变量（`.env` 文件或容器环境变量）：

```bash
DATABASE_PATH=/app/data/castplay.db   # SQLite 路径
SECRET_KEY=...                        # JWT 签名密钥
DEBUG=false                           # 生产环境关掉详细日志
NUM_WORKERS=3                         # APScheduler 线程池大小
ENVIRONMENT=production                # 设为 production 时收紧鉴权
```

> 完整参考：[`docs/deployment/guide.md`](docs/deployment/guide.md)、`.env.example`。

---

## 🌐 API 接口

REST 路由统一挂载在 `/api/`。OpenAPI 浏览器见 `/docs`（Swagger UI）和 `/redoc`。

| 分组 | 端点（节选） | 备注 |
|---|---|---|
| **Auth** | `POST /auth/token`, `POST /auth/refresh`, `GET /auth/me` | JWT bearer |
| **Devices** | `POST /devices/register`, `GET /devices`, `PUT /devices/{id}/disable`, `* /schedule` | MAC 键注册 |
| **Media** | `POST /media/upload`, `GET /media`, `DELETE /media/{id}`, `POST /media/{id}/retry` | multipart 上传 + 缩略图 |
| **Playlists** | `POST /playlists`, `* /items`, `PUT /items/reorder`, `POST /playlists/{id}/devices/{deviceId}` | 拖拽排序落库 |
| **Schedules** | `GET/PUT /devices/{id}/schedule` | 每设备每日开关机窗口 |
| **Player** | `GET /playlists/{deviceId}`, `GET /config/{deviceId}`, `POST /status/{deviceId}` | 客户端读侧 |
| **WebSocket** | `WS /ws/{deviceId}` | 列表 diff + 心跳 |

> 完整 schema：启动后访问 <http://localhost:8000/docs>。

---

## 📱 Android 播放端

Android 播放端是同一份 Web 播放器代码的 Kotlin 外壳：

- **WebView 宿主** — [`MainActivity.kt`](android/app/src/main/java/com/castplay/player/MainActivity.kt) 加载 Web 播放器，并注入运行时 `deviceId`。
- **Kiosk 模式** — `MyDeviceAdminReceiver.kt` + `DevicePolicyManager` 锁定设备；`BootReceiver.kt` 在开机时重启播放器。
- **离线缓存** — `CacheManager.kt` 提前下载所分配播放列表的素材，校验 MD5，失败按指数退避最多重试 3 次。
- **JsBridge** — 向 WebView 暴露 MAC、IP、注册码、下载进度、网络状态。

构建：

```bash
# 默认后端地址（要改请编辑 android/app/build.gradle.kts）
./build-android.sh

# 或指向自己的服务：
./build-android.sh http://192.168.1.100:8000
```

产物：`android/app/build/outputs/apk/debug/app-debug.apk`（约 20–30 MB）。

> 详细 Android 流程：[`docs/android/deployment_guide.md`](docs/android/deployment_guide.md)。

---

## 🆚 同类对比

| 指标 | CastPlay 2.0 | CastPlay v1（旧版） | 商业 CMS |
|---|---|---|---|
| 外部依赖（Redis/Celery/PG） | **无** | 需要 | 需要 |
| 干净 VM 首次部署耗时 | **5 分钟** | 30 分钟 | 30+ 分钟 |
| 冷启动耗时 | **≈ 10 秒** | ≈ 2 分钟 | ≈ 30 秒 |
| Python 源文件数 | **36** | 79 | n/a |
| 相对 v1 代码量 | **−34 %** | 基准 | n/a |
| 适配规模 | **< 50 块屏** | 小-中 | 中-大 |
| 许可证 | **MIT** | 按席位 | 订阅 |
| WebSocket 推送（无需轮询） | ✅ | ✅ | ✅ |

---

## 🗓️ Roadmap

- [x] **v2.0** — bootstrap 架构；零外部依赖；3-worker 调度器；拖拽排序播放列表；WebSocket 推送；Android Kiosk 播放端。
- [ ] **v2.1** — 可选 Postgres + Redis 适配器（适配 50 块屏以上，与旧版兼容）。
- [ ] **v2.2** — 多用户角色（管理员 / 编辑 / 查看者）与按设备权限粒度。
- [ ] **v2.3** — 播放列表加入天气、RSS、实时数据小组件。
- [ ] **v2.4** — Apple TV 上的 tvOS 播放端。

> 最近一次代码评审见 [`docs/reports/PROJECT_REVIEW_REPORT.md`](docs/reports/PROJECT_REVIEW_REPORT.md)，评审衍生项见 [`OPTIMIZATION.md`](OPTIMIZATION.md)。

---

## 🧪 测试

```bash
# 全部测试
make test                            # = pytest tests/ -v

# 分组跑
make test-unit                       # pytest -m unit
make test-integration                # pytest -m integration
make test-e2e                        # 前端 E2E
make test-performance                # Locust 100 用户 / 60 秒

# 覆盖率
make test-coverage                   # htmlcov/index.html + coverage.xml
```

CI 期望见 [`docs/testing/`](docs/testing/)。

---

## 🤝 贡献

欢迎 PR。请先读 [`CLAUDE.md`](CLAUDE.md) 了解构建 / 测试约定。高杠杆贡献：

- **Bug 报告** — 附 OS、CastPlay 版本、`docker compose ps` 输出、`logs/` 节选。
- **翻译** — `frontend/src/locales/` 现带 `zh-CN` + `en-US`；新增一个 locale 后 ping 维护者。
- **API 修补** — 先在 `tests/integration/` 写测试；OpenAPI spec 在 `/docs` 会从代码重新生成。
- **Android 修复** — 按 [`docs/android/emulator_setup.md`](docs/android/emulator_setup.md) 起模拟器。

本项目遵循 [Contributor Covenant v2.1](https://www.contributor-covenant.org/zh-cn/version/2/1/code_of_conduct/) 精神。

---

## 🔒 安全

发现漏洞请私下披露 — **不要发公开 GitHub issue**。详见 [`SECURITY.md`](SECURITY.md)，含支持版本表、披露窗口、私下联系渠道。

CastPlay 的威胁姿态：

- **JWT bearer 鉴权** — 在 `.env` 轮换 `SECRET_KEY`；token 短期 + refresh 路径。
- **`registration_code` token** — 生产模式（设 `ENVIRONMENT=production`）下，每次 WebSocket 连接都必须带上注册码，code `4001`/`4003`/`4004` 拒绝未授权客户端。
- **WebSocket origin 白名单** — 生产模式仅接受配置中的管理端 host 来源。
- **硬默认** — `DEBUG=false`、`NUM_WORKERS=3`、无埋点、无第三方 CDN。
- **内容校验** — 上传先看扩展名再看 magic number，通过后才落盘。

---

## ⚖️ 法律

本项目按 [MIT License](LICENSE) 开源；不附带任何第三方样本素材，请自带。

---

<div align="center">

<sub>📌 CastPlay 由 <a href="https://github.com/davyzhong">qiming</a> 维护 · <a href="https://github.com/davyzhong/CastPlay/issues">🐛 报告 Bug</a> · <a href="https://github.com/davyzhong/CastPlay/discussions">💬 讨论</a></sub>

</div>
