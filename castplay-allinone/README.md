# CastPlay All-in-One

> 快速启动的一体化数字标牌管理系统

## 特性

- 一体化部署，无需复杂配置
- SQLite 本地数据库，零运维成本
- 内置 PPT 转换服务
- WebSocket 实时推送
- RESTful API + 自动文档

## 快速开始

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
python -m uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

### 5. 访问服务

- 管理后台: http://localhost:5000/
- API 文档: http://localhost:5000/docs
- API 文档 (ReDoc): http://localhost:5000/redoc

## 目录结构

```
castplay-allinone/
├── app/                  # 应用主目录
│   ├── api/             # API 路由
│   ├── models/          # 数据模型
│   ├── schemas/         # Pydantic 模型
│   ├── services/        # 业务服务
│   ├── workers/         # 后台任务
│   └── utils/          # 工具函数
├── frontend/           # 前端代码
├── data/              # 数据目录
│   ├── uploads/       # 上传文件
│   ├── converted/     # 转换文件
│   └── thumbnails/    # 缩略图
└── scripts/           # 工具脚本
```

## API 端点

详见 [API 文档](./docs/API.md) 或访问 `/docs`

## 开发

### 启动开发服务器

```bash
# 后端
python -m uvicorn app.main:app --reload

# 前端 (开发模式)
cd frontend
npm install
npm run dev
```

### 运行测试

```bash
pytest tests/
```

## 数据备份

```bash
python scripts/backup_db.py
```

## 许可证

MIT
