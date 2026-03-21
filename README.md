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
python scripts/db/init.py
```

### 4. 启动服务

```bash
# 方式1: 直接启动
python scripts/server/start.py

# 方式2: 使用 uvicorn
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. 访问服务

- 管理后台：http://localhost:8000/
- 播放器页面：http://localhost:8000/player.html
- API 文档：http://localhost:8000/docs

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
├── android/             # Android 客户端
├── data/                # 数据目录
├── tests/               # 测试文件
├── scripts/             # 工具脚本
│   ├── server/         # 服务器启动脚本
│   ├── db/             # 数据库脚本
│   ├── migration/      # 数据迁移脚本
│   ├── testing/        # 测试脚本
│   └── dev/            # 开发工具脚本
└── docs/               # 文档
    ├── architecture/   # 架构设计文档
    ├── deployment/     # 部署文档
    ├── development/    # 开发指南
    ├── features/       # 功能文档
    ├── android/        # Android 相关文档
    ├── testing/        # 测试文档
    └── reports/        # 测试报告
```

## 📚 文档

### 核心文档

- 📖 [部署指南](./docs/deployment/guide.md)
- 📖 [开发手册](./docs/development/guide.md)
- 📖 [项目架构](./docs/architecture/README.md)

### Android 相关

- 📖 [Android 部署与测试指南](./docs/android/deployment_testing_guide.md)
- 📖 [模拟器配置](./docs/android/emulator_setup.md)

### 测试相关

- 📖 [Web 播放器模拟器](./docs/features/web_player_simulator.md)
- 📖 [播放列表推送测试](./docs/testing/playlist_push_guide.md)

## 🧪 测试

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行单元测试
pytest tests/unit/ -v

# 运行集成测试
pytest tests/integration/ -v

# 运行 Android 测试
python scripts/testing/run_android_tests.py

# 运行 Web 播放端测试
python scripts/testing/run_web_tests.py --e2e --headed
```

### 测试环境启动

```bash
# 启动 Web 播放端测试环境
python scripts/testing/start_web_env.py

# 启动 Android 测试环境
python scripts/testing/start_android_env.py
```

## 📱 Android 客户端

### 构建 APK

```bash
./build-android.sh [serverUrl]
# 例如: ./build-android.sh http://192.168.1.100:8000
```

### 测试

```bash
python scripts/testing/android-test.sh [选项]
# --skip-build     跳过 APK 构建
# --skip-emulator  使用已连接的设备
# --auto-close     测试完成后自动关闭
```

## 🔧 常用命令

### 服务管理

```bash
# 启动服务器
python scripts/server/start.py

# 初始化数据库
python scripts/db/init.py

# 备份数据库
python scripts/db/backup.py
```

### 开发

```bash
# 启动前端开发服务器
cd frontend && npm run dev

# 构建前端
cd frontend && npm run build

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
