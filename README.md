# CastPlay - 智能投屏播放系统

> ⚡ 轻量级智能投屏播放系统，支持 Android 离线播放

## ✨ 功能特性

### 🎯 核心功能

- **多格式支持** - 支持图片（JPG/PNG/GIF）、视频（MP4/AVI/MOV）、PPT 文件
- **PPT 自动转换** - PPT 文件自动转换为视频，保留动画效果
- **离线播放** - Android 设备支持离线缓存播放，无需实时网络
- **实时推送** - WebSocket 实时推送播放列表和配置更新
- **定时控制** - 支持设备定时开关机，可配置工作日
- **远程管理** - Web 管理后台实现设备监控和内容管理
- **混合播放** - 图片、视频、PPT 混合播放，自动循环切换
- **播放列表自动切换** - 支持按时间自动切换播放列表

### 📊 管理功能

- **设备管理** - 设备注册、在线监控、批量操作
- **媒体库管理** - 文件上传、分类管理、缩略图预览
- **播放列表** - 拖拽排序、批量添加、多设备分配
- **定时任务** - 可视化定时配置，支持多时区
- **统计分析** - 设备状态统计、播放数据分析

## 🎯 使用场景

- **企业宣传** - 公司大厅、展厅的企业介绍和产品宣传
- **会议室显示** - 会议室门口的会议信息和日程显示
- **广告投放** - 商场、餐厅等场所的广告轮播
- **信息公告** - 学校、医院等场所的通知公告
- **数据大屏** - 数据中心、控制室的实时数据展示

## ✨ 核心优势

- 🚀 **零依赖部署** - 无需 Redis、Celery、PostgreSQL
- 📦 **一体化设计** - 后端 + 前端 + 数据库，开箱即用
- ⚡ **极速启动** - 5 分钟完成部署，10 秒启动
- 🎯 **小规模优化** - 专为 <50 设备场景设计
- 🔧 **模块化架构** - 易于维护和扩展

## 🚀 快速开始

### 1. 系统要求

- Python 3.10+
- Node.js 18+ (仅前端开发时需要)
- LibreOffice (PPT 转换)
- ffmpeg (视频处理)

### 2. 安装依赖

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装 Python 依赖
pip install -r requirements.txt
```

### 3. 初始化数据库

```bash
python scripts/init_db.py
```

### 4. 启动服务

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. 访问服务

- 管理后台：http://localhost:8000/
- 播放器页面：http://localhost:8000/player
- API 文档：http://localhost:8000/docs
- API 文档 (ReDoc)：http://localhost:8000/redoc

## 📁 项目结构

```
castplay/
├── app/                  # 后端应用
│   ├── api/             # API 路由
│   ├── bootstrap/       # 应用引导模块
│   ├── models/          # 数据模型
│   ├── schemas/         # Pydantic 模型
│   ├── services/        # 业务服务
│   ├── utils/           # 工具函数
│   └── websocket/       # WebSocket 处理
├── frontend/            # 前端代码 (React + TypeScript)
│   └── src/
│       ├── api/         # API 调用
│       ├── pages/       # 页面组件
│       ├── player/      # 播放器核心
│       └── store/       # 状态管理
├── android/             # Android 客户端
├── data/                # 数据目录
├── tests/               # 测试文件
│   ├── unit/           # 单元测试
│   ├── integration/    # 集成测试
│   └── e2e/            # 端到端测试
├── scripts/            # 工具脚本
└── docs/               # 文档
```

## 📚 文档

### 核心文档

- 📖 [DEPLOYMENT.md](./DEPLOYMENT.md) - 部署指南
- 📖 [DEVELOPER.md](./DEVELOPER.md) - 开发手册
- 📖 [Android_部署与测试指南.md](./Android_部署与测试指南.md) - Android 部署
- 📖 [WEB_PLAYER_SIMULATOR.md](./WEB_PLAYER_SIMULATOR.md) - Web 播放器模拟器

### 架构文档

- 📖 [docs/PROJECT_ARCHITECTURE.md](./docs/PROJECT_ARCHITECTURE.md) - 项目架构
- 📖 [docs/PLAYER_CLIENT_DESIGN_V3.md](./docs/PLAYER_CLIENT_DESIGN_V3.md) - 播放器设计

### API 文档

启动服务后访问：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🧪 测试

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行单元测试
pytest tests/unit/ -v

# 运行集成测试
pytest tests/integration/ -v

# Android 端测试
./scripts/android-test.sh
```

## 📱 Android 客户端

### 构建 APK

```bash
./build-android.sh [serverUrl]
# 例如: ./build-android.sh http://192.168.1.100:8000
```

### 测试

```bash
./scripts/android-test.sh [选项]
# --skip-build     跳过 APK 构建
# --skip-emulator  使用已连接的设备
# --auto-close     测试完成后自动关闭
```

## 🔧 开发命令

```bash
# 启动后端开发服务器
python -m uvicorn app.main:app --reload

# 启动前端开发服务器
cd frontend && npm run dev

# 构建前端
cd frontend && npm run build

# 运行测试
pytest tests/ -v

# 代码格式化
make format
```

## 📊 项目状态

- ✅ 核心功能完成
- ✅ 单元测试覆盖
- ✅ 集成测试通过
- ✅ Android 客户端可用
- ✅ 播放列表自动切换功能

## 📝 许可证

MIT License
