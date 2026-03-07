# CastPlay - 智能投屏播放系统

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18.x-blue.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-blue.svg)](https://www.typescriptlang.org/)
[![Android](https://img.shields.io/badge/Android-5.0+-green.svg)](https://developer.android.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

一个功能强大的智能投屏播放系统，支持图片、视频、PPT 等多种媒体格式，提供完整的设备管理、内容管理和远程控制功能。

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [文档](#-文档) • [技术栈](#️-技术栈) • [贡献指南](#-贡献)

</div>

---

## ✨ 功能特性

### 🎯 核心功能

- **多格式支持** - 支持图片（JPG/PNG/GIF）、视频（MP4/AVI/MOV）、PPT 文件
- **PPT 自动转换** - PPT 文件自动转换为视频，保留动画效果
- **离线播放** - Android 设备支持离线缓存播放，无需实时网络
- **实时推送** - WebSocket 实时推送播放列表和配置更新
- **定时控制** - 支持设备定时开关机，可配置工作日
- **远程管理** - Web 管理后台实现设备监控和内容管理
- **混合播放** - 图片、视频、PPT 混合播放，自动循环切换

### 📊 管理功能

- **设备管理** - 设备注册、在线监控、批量操作
- **媒体库管理** - 文件上传、分类管理、缩略图预览
- **播放列表** - 拖拽排序、批量添加、多设备分配
- **定时任务** - 可视化定时配置，支持多时区
- **统计分析** - 设备状态统计、播放数据分析

---

## 🚀 快速开始

### 系统要求

- **后端**: Python 3.10+, Redis, PostgreSQL（可选）
- **前端**: Node.js 18+, npm 9+
- **Android**: Android Studio 2022+, Android 5.0+

### 安装部署

#### 1. 克隆代码

```bash
git clone <repository-url>
cd CastPlay
```

#### 2. 后端服务

```bash
cd castplay-server

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 安装系统依赖（Ubuntu/Debian）
sudo apt install -y libreoffice ffmpeg poppler-utils redis-server

# 启动 Redis
sudo systemctl start redis

# 初始化数据库
flask db upgrade

# 启动服务
python run.py

# 新终端 - 启动 Celery Worker
celery -A app.tasks.celery_app:celery worker --loglevel=info
```

#### 3. 前端管理后台

```bash
cd castplay-admin

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问：http://localhost:3000

#### 4. Android 播放端

1. 使用 Android Studio 打开 `android-app/` 目录
2. 修改 `app/build.gradle` 中的 API 地址
3. 同步 Gradle 依赖
4. 运行到设备或模拟器

详细部署说明请参考 [部署指南](DEPLOYMENT_GUIDE.md)

---

## 📚 文档

### 核心文档

| 文档                                | 描述                                                 |
| ----------------------------------- | ---------------------------------------------------- |
| [项目架构](PROJECT_ARCHITECTURE.md) | 完整的项目架构说明，包含目录结构、模块职责、设计模式 |
| [API 文档](API_DOCUMENTATION.md)    | 详细的 REST API 和 WebSocket 接口文档                |
| [部署指南](DEPLOYMENT_GUIDE.md)     | 开发环境搭建和生产环境部署指南                       |
| [开发规范](CONTRIBUTING.md)         | 代码规范、Git 工作流、测试规范                       |
| [实现指南](IMPLEMENTATION_GUIDE.md) | 技术实现细节和示例代码                               |
| [项目状态](PROJECT_STATUS.md)       | 当前开发进度和待办事项                               |

### 快速链接

- **API 文档**: [查看完整 API](API_DOCUMENTATION.md)
- **架构图**: [系统架构](PROJECT_ARCHITECTURE.md#数据流架构)
- **数据库设计**: [ER 图](PROJECT_ARCHITECTURE.md#数据库设计)
- **部署方案**: [Docker 部署](DEPLOYMENT_GUIDE.md#docker-部署)

---

## 🏗️ 技术栈

### 后端 (castplay-server/)

- **框架**: Flask 2.x
- **ORM**: SQLAlchemy
- **数据库**: PostgreSQL / SQLite
- **缓存**: Redis
- **任务队列**: Celery
- **WebSocket**: Flask-SocketIO
- **认证**: Flask-JWT-Extended (预留)

**第三方工具**:

- LibreOffice - PPT 转 PDF
- FFmpeg - 视频处理
- pdftoppm - PDF 转图片

### 前端 (castplay-admin/)

- **框架**: React 18.x
- **语言**: TypeScript 5.x
- **构建工具**: Vite 5.x
- **UI 库**: Ant Design 5.x
- **HTTP 客户端**: Axios
- **路由**: React Router DOM
- **时间处理**: dayjs

### Android (android-app/)

- **语言**: Java 8+
- **最低 SDK**: 21 (Android 5.0)
- **目标 SDK**: 33 (Android 13)
- **数据库**: Room
- **网络**: Retrofit 2 + OkHttp 3
- **视频播放**: ExoPlayer 2
- **图片加载**: Glide 4
- **WebSocket**: OkHttp WebSocket

---

## 📊 项目结构

```
CastPlay/
├── castplay-server/          # 后端服务
│   ├── app/                  # 应用核心代码
│   │   ├── api/             # RESTful API 路由
│   │   ├── models/          # 数据模型
│   │   ├── services/        # 业务服务
│   │   ├── tasks/           # 异步任务
│   │   └── websocket/       # WebSocket 推送
│   ├── storage/             # 文件存储
│   ├── config.py            # 配置文件
│   └── run.py               # 启动入口
│
├── castplay-admin/           # 前端管理后台
│   ├── src/
│   │   ├── api/             # API 服务
│   │   ├── pages/           # 页面组件
│   │   ├── layouts/         # 布局组件
│   │   └── components/      # 可复用组件
│   └── package.json
│
├── android-app/              # Android 播放端
│   └── app/src/main/java/
│       └── com/castplay/player/
│           ├── MainActivity.java
│           ├── network/     # 网络层
│           ├── data/        # 数据层
│           ├── service/     # 业务服务
│           ├── player/      # 播放引擎
│           └── receiver/    # 广播接收器
│
├── docs/                     # 额外文档（建议）
└── scripts/                  # 部署脚本（建议）
```

完整结构说明请参考 [项目架构文档](PROJECT_ARCHITECTURE.md)

---

## 🔄 数据流

### 内容发布流程

```
管理后台 → 上传媒体 → 后端 API → Celery 异步转换（PPT）
       ↓                              ↓
    创建播放列表 ← 转换完成 ← Worker 处理
       ↓
    分配到设备
       ↓
WebSocket 推送 → Android 设备 → 同步下载 → 本地播放
```

### 实时推送流程

```
管理后台操作（更新播放列表/定时配置）
       ↓
   后端 API 更新数据库
       ↓
WebSocket emit 事件到指定设备
       ↓
Android 接收事件 → 触发重新同步 → 更新本地数据
```

---

## 🎯 使用场景

- **企业宣传** - 公司大厅、展厅的企业介绍和产品宣传
- **会议室显示** - 会议室门口的会议信息和日程显示
- **广告投放** - 商场、餐厅等场所的广告轮播
- **信息公告** - 学校、医院等场所的通知公告
- **数据大屏** - 数据中心、控制室的实时数据展示

---

## 🛠️ 开发

### 本地开发

```bash
# 后端
cd castplay-server
python run.py

# 前端
cd castplay-admin
npm run dev

# Android
# 使用 Android Studio 打开并运行
```

### 运行测试

```bash
# 后端测试
cd castplay-server
pytest

# 前端测试
cd castplay-admin
npm run test

# Android 测试
./gradlew test
```

### 代码检查

```bash
# Python
black app/
flake8 app/

# TypeScript
npm run lint
npm run format

# Java
# Android Studio → Code → Reformat Code
```

---

## 🤝 贡献

欢迎贡献代码、报告问题或提出建议！

### 贡献流程

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

详细规范请参考 [贡献指南](CONTRIBUTING.md)

---

## 📝 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 👥 团队

- **项目负责人**: [待填写]
- **后端开发**: [待填写]
- **前端开发**: [待填写]
- **Android 开发**: [待填写]

---

## 📧 联系方式

- **Issue**: [GitHub Issues](https://github.com/your-repo/issues)
- **Email**: [your-email@example.com]
- **文档**: [在线文档地址]

---

## 🙏 致谢

感谢以下开源项目：

- [Flask](https://flask.palletsprojects.com/)
- [React](https://reactjs.org/)
- [Ant Design](https://ant.design/)
- [ExoPlayer](https://exoplayer.dev/)
- [LibreOffice](https://www.libreoffice.org/)
- [FFmpeg](https://ffmpeg.org/)

---

## ⚠️ 重要通知 - 项目已归档

**📦 此项目（CastPlay）已归档，请迁移至新版本：**

### 👉 推荐使用：[castplay-allinone](./castplay-allinone)

**为什么选择 all-in-one?**

| 特性            | CastPlay（当前）            | castplay-allinone（新） | 改进         |
| --------------- | --------------------------- | ----------------------- | ------------ |
| **代码量**      | 8,106 行                    | 5,330 行                | **-34%** ✅  |
| **Python 文件** | 79 个                       | 36 个                   | **-54%** ✅  |
| **外部依赖**    | Redis + Celery + PostgreSQL | 无                      | **-100%** ✅ |
| **部署时间**    | 30 分钟                     | 5 分钟                  | **-83%** ✅  |
| **运维成本**    | 高                          | 几乎为零                | **-90%** ✅  |

**核心优势:**

- 🚀 **零依赖部署** - 无需 Redis、Celery、PostgreSQL
- 📦 **一体化设计** - 后端 + 前端 + 数据库，开箱即用
- ⚡ **极速启动** - 5 分钟完成部署
- 🎯 **小规模优化** - 专为<50 设备场景设计

**快速开始:**

```bash
# 1. 进入 all-in-one 目录
cd castplay-allinone

# 2. 安装依赖
pip install -r requirements.txt

# 3. 初始化数据库
python scripts/init_db.py

# 4. 启动服务
python -m uvicorn app.main:app --reload

# 5. 访问管理后台
open http://localhost:8000
```

**迁移帮助:**

- 📖 详细文档：[castplay-allinone/README.md](./castplay-allinone/README.md)
- 🔧 部署指南：[castplay-allinone/DEPLOYMENT.md](./castplay-allinone/DEPLOYMENT.md)
- 📝 API 文档：[castplay-allinone/docs/API.md](./castplay-allinone/docs/API.md)

---

_最后更新时间：2026-03-04 • 版本：v1.0-archive_

---

<div align="center">

**[⬆ 回到顶部](#castplay---智能投屏播放系统)**

由 ❤️ 使用 Python, React, Java 构建

</div>
