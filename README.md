# CastPlay All-in-One v2.0 - 轻量化智能投屏播放系统


> ⚡ 快速启动的轻量化智能投屏播放系统
> 🎉 **v2.0 全新发布** - 零依赖、极简部署、bootstrap 架构

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
- 🎯 **小规模优化** - 专为<50 设备场景设计
- 📊 **34% 代码精简** - 比原项目更轻量
- 🔧 **bootstrap 架构** - 模块化设计，易维护

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
- API 文档：http://localhost:8000/docs
- API 文档 (ReDoc): http://localhost:8000/redoc

## 📈 与原项目对比

| 指标            | CastPlay        | All-in-One v2.0 | 改进         |
| --------------- | --------------- | --------------- | ------------ |
| **代码量**      | 8,106 行        | 5,330 行        | **-34%** ✅  |
| **Python 文件** | 79 个           | 36 个           | **-54%** ✅  |
| **外部依赖**    | Redis+Celery+PG | 无              | **-100%** ✅ |
| **部署时间**    | 30 分钟         | 5 分钟          | **-83%** ✅  |
| **启动时间**    | ~2 分钟         | ~10 秒          | **-92%** ✅  |
| **运维成本**    | 高              | 几乎为零        | **-90%** ✅  |

## 🆕 v2.0 新特性

```
castplay-allinone/
├── app/                  # 应用主目录
│   ├── api/             # API 路由
│   ├── bootstrap/       # ⭐ 应用引导模块
│   ├── models/          # 数据模型
│   ├── schemas/         # Pydantic 模型
│   ├── services/        # 业务服务
│   ├── utils/           # 工具函数
│   └── websocket/       # WebSocket 处理
├── frontend/            # 前端代码
├── data/                # 数据目录
├── docs/                # ⭐ 文档目录
│   ├── MIGRATION.md     # 迁移指南
│   ├── FINAL_REPORT.md  # 整合报告
│   └── ...
└── scripts/             # 工具脚本
```

## 📚 文档

### 核心文档

- 📖 [README.md](./README.md) - 项目介绍和快速开始
- 📖 [DEPLOYMENT.md](./DEPLOYMENT.md) - 部署指南
- 📖 [DEVELOPER.md](./DEVELOPER.md) - 开发手册
- 📖 [docs/MIGRATION.md](./docs/MIGRATION.md) - **从原项目迁移指南** ⭐
- 📖 [docs/FINAL_REPORT.md](./docs/FINAL_REPORT.md) - **项目整合报告** ⭐
- 📖 [docs/REVIEW_REPORT.md](./docs/REVIEW_REPORT.md) - **审查报告** ⭐

### API 文档

启动服务后访问：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🧪 测试

### 运行测试

```bash
pytest tests/ -v
```

**测试覆盖**: 685 个测试用例，覆盖率 ~85%

## 🔄 从原项目迁移

如果你正在使用 CastPlay 原项目，请参考 **[迁移指南](docs/MIGRATION.md)**

**迁移收益**:

- ✅ API 接口 95% 兼容
- ✅ 数据完全兼容
- ✅ 零 Redis/Celery 依赖
- ✅ 部署更简单

## 📊 项目状态

- ✅ 核心功能完成
- ✅ 单元测试覆盖率 85%+
- ✅ 集成测试通过
- ✅ Phase 1-5 圆满完成
- 🎉 **v2.0.0 正式发布**

## 🤝 贡献

## 📝 许可证

MIT License

---

**版本**: v2.0.0
**发布时间**: 2026-03-07
**核心改进**: Bootstrap 架构、零依赖、代码精简 34%
