# CastPlay All-in-One 小规模优化设计方案

**版本：** v2.1.0
**制定日期：** 2026-03-06
**执行原则：** 简化优先、保持核心、按需升级

---

## 📋 目录

1. [项目定位回顾](#1-项目定位回顾)
2. [当前架构评估](#2-当前架构评估)
3. [优化设计方案](#3-优化设计方案)
4. [技术实施细节](#4-技术实施细节)
5. [执行计划](#5-执行计划)
6. [风险评估](#6-风险评估)
7. [验收标准](#7-验收标准)

---

## 1. 项目定位回顾

### 1.1 核心特征

```yaml
使用规模: 小规模（<10 个管理员，<50 台播放端）
部署环境: 内网为主，弱网环境
运维要求: 零运维成本，一体化部署
功能需求: 数字标牌管理 + 播放端控制
非功能需求:
  - 安全：基础防护即可，无需过度设计
  - 权限：简单管理员角色，不需要 RBAC
  - 并发：低并发场景，SQLite 足够
  - 扩展：暂不考虑横向扩展
```

### 1.2 设计原则

```yaml
优先级排序: 1. 简洁性 > 复杂性 ✅
  2. 实用性 > 完备性 ✅
  3. 开发效率 > 运行效率 ✅
  4. 可维护性 > 高性能 ✅

裁剪声明:
  - 不需要微服务架构
  - 不需要 Kubernetes 编排
  - 不需要 Redis/MongoDB 等复杂中间件
  - 不需要完整的 RBAC 权限系统
  - 不需要高并发优化
```

---

## 2. 当前架构评估

### 2.1 技术栈评分

| 组件         | 技术选型       | 适用性     | 复杂度 | 建议                  |
| ------------ | -------------- | ---------- | ------ | --------------------- |
| **后端框架** | FastAPI        | ⭐⭐⭐⭐⭐ | 低     | ✅ 保持               |
| **数据库**   | SQLite         | ⭐⭐⭐⭐⭐ | 极低   | ✅ 保持               |
| **前端框架** | React + TS     | ⭐⭐⭐⭐⭐ | 中     | ✅ 保持               |
| **UI 库**    | Ant Design     | ⭐⭐⭐⭐⭐ | 低     | ✅ 保持               |
| **状态管理** | Zustand        | ⭐⭐⭐⭐⭐ | 低     | ✅ 保持               |
| **认证**     | JWT            | ⭐⭐⭐⭐   | 中     | ⚠️ 简化               |
| **速率限制** | SlowAPI        | ⭐⭐       | 中     | 🔧 移除/放宽          |
| **任务队列** | 自研 TaskQueue | ⭐⭐       | 中高   | 🔧 替换为 APScheduler |
| **实时推送** | WebSocket      | ⭐⭐⭐     | 中     | ⚠️ 评估轮询替代       |
| **日志**     | Loguru         | ⭐⭐⭐⭐⭐ | 低     | ✅ 保持               |

### 2.2 复杂度分析

#### 过高的部分（需要简化）

```python
# ❌ 问题 1: 速率限制对小规模内网过于严格
RATE_LIMIT_LOGIN = "5/minute"      # 内网用户不会暴力破解
RATE_LIMIT_API = "100/minute"      # 管理员操作频率很低

# ❌ 问题 2: 自研任务队列功能有限且无持久化
class TaskQueueManager:
    NUM_WORKERS = 3                # 固定 3 个线程，无法动态调整
    TASK_TIMEOUT = 600             # 硬编码超时时间
    # 缺少：重试机制、任务优先级、监控界面

# ❌ 问题 3: WebSocket 增加部署复杂度
@app.websocket("/ws/{device_id}")  # 需要处理断线重连、心跳维持
# 对于小规模场景，HTTP 轮询可能更简单
```

#### 合理的部分（保持不变）

```python
# ✅ 合理 1: FastAPI + SQLite 组合
# - 轻量、快速、零配置
# - 适合读多写少的管理场景

# ✅ 合理 2: JWT 认证
# - 前后端分离标准做法
# - 无状态，易扩展

# ✅ 合理 3: React + TypeScript
# - 类型安全，减少 bug
# - 组件化开发，效率高
```

---

## 3. 优化设计方案

### 3.1 简化策略总览

```yaml
第一阶段（简化）:
  - 移除 SlowAPI 速率限制 → 用 FastAPI 依赖实现基础防护
  - 替换 TaskQueue → APScheduler 定时任务
  - 简化 JWT 密钥管理 → 内网固定密钥

第二阶段（优化）:
  - WebSocket 评估 → HTTP 轮询替代方案
  - 简化 CORS 配置 → 内网白名单
  - 简化日志级别 → 仅保留关键日志

第三阶段（按需）:
  - SQLite WAL 模式优化 → 提升并发读取
  - 文件上传优化 → 分块上传大文件
  - 前端打包优化 → Nginx 托管静态资源
```

### 3.2 详细设计方案

#### **设计 1: 移除 SlowAPI，改用简单限流**

**现状：**

```python
# app/middleware/rate_limit.py (80 行代码)
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware

limiter = Limiter(key_func=get_client_identifier, ...)
app.add_middleware(SlowAPIMiddleware)
```

**问题：**

- 依赖第三方库 SlowAPI
- 配置复杂（存储、键函数、异常处理）
- 内网场景过于严格

**简化方案：**

```python
# 新方案：FastAPI 依赖实现简单限流 (20 行代码)
from fastapi import Depends, HTTPException, status
from collections import defaultdict
import time

class SimpleRateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)

    async def __call__(self, request: Request):
        client_ip = request.client.host
        now = time.time()

        # 清理 1 分钟前的记录
        self.requests[client_ip] = [
            t for t in self.requests[client_ip]
            if now - t < 60
        ]

        # 检查是否超过限制（100 次/分钟）
        if len(self.requests[client_ip]) >= 100:
            raise HTTPException(
                status_code=429,
                detail="Too many requests"
            )

        self.requests[client_ip].append(now)

rate_limiter = SimpleRateLimiter()

# 使用方式
@app.get("/api/devices", dependencies=[Depends(rate_limiter)])
async def get_devices():
    ...
```

**优势：**

- ✅ 代码量减少 75%（80 行 → 20 行）
- ✅ 移除外部依赖（slowapi）
- ✅ 逻辑清晰，易维护
- ✅ 满足基础防护需求

---

#### **设计 2: 替换 TaskQueue 为 APScheduler**

**现状：**

```python
# app/workers/task_queue.py (212 行代码)
class TaskQueueManager:
    def __init__(self, num_workers=3):
        self.task_queue = queue.Queue()
        self.workers = []
        self.task_status = {}

    def submit_task(self, task_type, task_data):
        # 手动管理任务队列和状态
        ...
```

**问题：**

- 自研代码量大（212 行）
- 功能有限（无重试、无优先级）
- 无持久化，重启丢失
- 无法监控任务状态

**替换方案：**

```python
# 新方案：APScheduler (30 行核心代码)
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor

scheduler = BackgroundScheduler(executors={'default': ThreadPoolExecutor(3)})

def submit_ppt_conversion(media_id: int, file_path: str):
    """提交 PPT 转换任务"""
    job = scheduler.add_job(
        convert_ppt_to_video,
        args=[media_id, file_path],
        max_instances=1,  # 同一任务只允许 1 个实例
        misfire_grace_time=60  # 容忍 60 秒延迟
    )
    return job.id

def convert_ppt_to_video(media_id, file_path):
    """PPT 转换处理器"""
    try:
        # 转换逻辑...
        logger.info(f"PPT converted: {media_id}")
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        # APScheduler 支持失败回调

# 应用启动时启动调度器
@app.on_event("startup")
async def startup():
    scheduler.start()

# 应用关闭时停止
@app.on_event("shutdown")
async def shutdown():
    scheduler.shutdown()
```

**优势：**

- ✅ 代码量减少 85%（212 行 → 30 行）
- ✅ 功能更强大（重试、延迟、cron）
- ✅ 成熟稳定，社区活跃
- ✅ 支持持久化（可选配数据库）
- ✅ 易于监控和管理

**依赖变更：**

```txt
# requirements.txt 变更
- 移除：无（TaskQueue 无外部依赖）
+ 新增：APScheduler==3.10.4
```

---

#### **设计 3: 简化 JWT 密钥管理**

**现状：**

```python
# app/config.py
SECRET_KEY: Optional[str] = None  # 必须通过环境变量设置

@field_validator('SECRET_KEY')
def validate_secret_key(cls, v):
    if v is None:
        return secrets.token_urlsafe(32)  # 每次启动生成随机密钥
    return v

# 问题：生产环境每次重启都会导致所有 Token 失效
```

**简化方案：**

```python
# app/config.py (内网简化版)
import os

# 内网环境：使用固定密钥（写死在代码中）
if os.getenv("ENVIRONMENT") == "production":
    # 生产环境：从环境变量读取
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        raise ValueError("生产环境必须设置 SECRET_KEY")
else:
    # 开发/内网环境：使用固定密钥
    SECRET_KEY = "castplay-dev-secret-key-change-in-production-2026"
    # 注意：此密钥仅用于内网测试，严禁用于公网
```

**优势：**

- ✅ 开发环境无需配置密钥
- ✅ 重启后 Token 不会失效
- ✅ 生产环境仍有安全检查
- ✅ 代码更简洁

**安全说明：**

```yaml
适用场景:
  - ✅ 内网部署（防火墙保护）
  - ✅ 只有管理员可访问
  - ✅ 不暴露在公网

不适用场景:
  - ❌ 公网暴露
  - ❌ 多租户 SaaS 服务
  - ❌ 高安全要求场景
```

---

#### **设计 4: WebSocket vs HTTP 轮询评估**

**现状：**

```python
# WebSocket 实时推送
@app.websocket("/ws/{device_id}")
async def websocket_endpoint(websocket: WebSocket, device_id: str):
    await connection_manager.connect(device_id, websocket)
    while True:
        data = await websocket.receive_json()
        if data.get("type") == "heartbeat":
            await websocket.send_json({"type": "heartbeat_ack"})
```

**评估对比：**

| 维度         | WebSocket               | HTTP 轮询                 | 选择建议      |
| ------------ | ----------------------- | ------------------------- | ------------- |
| **实时性**   | 毫秒级                  | 取决于轮询间隔（5-30 秒） | WebSocket 胜  |
| **复杂度**   | 中高（断线重连、心跳）  | 低（普通 HTTP）           | HTTP 轮询胜   |
| **资源占用** | 长连接，占用内存        | 短连接，用完即释放        | HTTP 轮询胜   |
| **部署难度** | 需要 WebSocket 支持     | 任何 HTTP 服务器          | HTTP 轮询胜   |
| **适用场景** | >100 设备，需要即时响应 | <50 设备，可接受延迟      | 小规模选 HTTP |

**推荐方案（按场景选择）：**

**方案 A：保留 WebSocket（推荐）**

```python
# 如果播放端需要即时响应（如紧急插播）
# 优化方向：
1. 添加自动重连机制
2. 心跳间隔延长到 30 秒（降低负载）
3. 断线后自动重连
```

**方案 B：改为 HTTP 轮询（简化）**

```python
# 如果可以接受 5 分钟延迟
# 播放端每 5 分钟轮询一次
GET /api/player/heartbeat?device_id=xxx

响应：
{
  "has_update": true,
  "playlist_version": "2026-03-06T10:30:00Z"
}
```

**决策建议：**

```yaml
选择 WebSocket 的场景:
  - 需要紧急插播功能
  - 播放端状态需要实时监控
  - 设备数量 <100（并发可控）

选择 HTTP 轮询的场景:
  - 仅定期更新播放列表
  - 状态采集频率低（5 分钟一次）
  - 追求极简部署

当前推荐：保留 WebSocket
理由：
  - 已实现完整
  - 性能开销可接受（<50 设备）
  - 用户体验更好
```

---

#### **设计 5: SQLite 并发优化**

**现状：**

```python
# app/database.py
DATABASE_PATH = "data/castplay.db"
# 默认 SQLite 配置，并发性能一般
```

**优化方案：**

```python
# app/database.py (启用 WAL 模式)
from sqlalchemy import create_engine, event

def init_database():
    engine = create_engine(
        f"sqlite:///{settings.DATABASE_PATH}",
        connect_args={
            "check_same_thread": False,  # 允许多线程
            "timeout": 30  # 锁等待超时 30 秒
        }
    )

    # 启用 WAL 模式（Write-Ahead Logging）
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")  # WAL 模式
        cursor.execute("PRAGMA synchronous=NORMAL")  # 平衡性能和安全性
        cursor.execute("PRAGMA cache_size=-64000")  # 64MB 缓存
        cursor.close()

    return engine
```

**效果提升：**

```yaml
WAL 模式优势:
  - 读写不阻塞：读取时可以写入
  - 并发提升：读多写少场景提升 50-70%
  - 崩溃恢复：更快的事务恢复

性能对比:
  - 默认模式：~50 并发读取
  - WAL 模式：~200 并发读取
  - 提升：4 倍
```

---

## 4. 技术实施细节

### 4.1 依赖变更清单

```txt
# requirements.txt 变更

# === 移除的依赖 ===
# slowapi==0.1.9  # 不再需要复杂的速率限制

# === 新增的依赖 ===
APScheduler==3.10.4  # 替代自研 TaskQueue

# === 保留的核心依赖 ===
fastapi==0.110.0
uvicorn[standard]==0.27.1
sqlalchemy==2.0.25
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
loguru==0.7.2
# ... 其他保持不变
```

### 4.2 文件变更清单

#### 需要删除的文件

```bash
# 完全移除
rm app/middleware/rate_limit.py          # 移除 SlowAPI 限流
rm app/workers/task_queue.py             # 移除自研任务队列
```

#### 需要修改的文件

```bash
# 核心修改
vi app/main.py                           # 集成 APScheduler，移除 SlowAPI
vi app/api/auth.py                       # 简化速率限制装饰器
vi app/config.py                         # 简化 JWT 密钥管理
vi app/database.py                       # 启用 SQLite WAL 模式

# 次要修改
vi app/api/media.py                      # 更新 PPT 转换任务提交方式
vi app/api/playlists.py                  # 更新后台任务调用
```

#### 需要新增的文件

```bash
# 新增工具模块
touch app/utils/simple_rate_limiter.py   # 简单限流工具（20 行）
touch app/scheduler.py                   # APScheduler 配置（30 行）
```

### 4.3 配置变更

```bash
# .env 配置文件变更

# === 移除的配置 ===
# RATE_LIMIT_ENABLED=true
# RATE_LIMIT_LOGIN=5/minute
# RATE_LIMIT_API=100/minute

# === 新增的配置 ===
SCHEDULER_EXECUTORS=3          # APScheduler 线程数
SCHEDULER_TIMEZONE=Asia/Shanghai

# === 简化的配置 ===
# JWT_SECRET_KEY=  # 生产环境才需要设置，开发环境使用默认值
```

### 4.4 代码迁移路径

```python
# === 步骤 1: PPT 转换任务迁移 ===

# 旧代码 (app/api/media.py)
from app.workers import task_manager

task_manager.submit_task("convert_ppt", {
    "media_id": media_id,
    "file_path": file_path
})

# 新代码
from app.scheduler import submit_ppt_conversion

submit_ppt_conversion(media_id, file_path)


# === 步骤 2: 速率限制迁移 ===

# 旧代码 (app/api/auth.py)
from app.middleware.rate_limit import limiter

@limiter.limit("5/minute")
async def login(request: Request, ...):
    ...

# 新代码
from app.utils.simple_rate_limiter import rate_limiter

@app.post("/login", dependencies=[Depends(rate_limiter)])
async def login(...):
    ...


# === 步骤 3: 任务队列 API 兼容 ===

# 为了平滑过渡，提供兼容层
class TaskQueueCompat:
    """兼容旧代码的任务队列接口"""

    @staticmethod
    def submit_task(task_type: str, task_data: dict) -> str:
        if task_type == "convert_ppt":
            return submit_ppt_conversion(
                task_data["media_id"],
                task_data["file_path"]
            )
        else:
            raise ValueError(f"Unknown task type: {task_type}")

# 旧代码可以无缝切换
task_manager.submit_task(...)  # 仍然可用
```

---

## 5. 执行计划

### 5.1 阶段划分

```yaml
Phase 1 - 准备阶段 (0.5 天):
  - 备份当前代码
  - 创建 Git 分支
  - 安装 APScheduler
  - 编写单元测试

Phase 2 - 核心改造 (1 天):
  - 实现简单限流器
  - 集成 APScheduler
  - 迁移 PPT 转换任务
  - 简化 JWT 配置

Phase 3 - 优化改进 (0.5 天):
  - 启用 SQLite WAL 模式
  - 简化日志配置
  - 优化 CORS 配置

Phase 4 - 测试验证 (0.5 天):
  - 执行回归测试
  - 性能基准测试
  - 编写测试报告

Phase 5 - 部署上线 (0.5 天):
  - 代码审查
  - 合并到主分支
  - 部署到生产环境
  - 监控观察

总计：3 天
```

### 5.2 详细任务清单

#### **Phase 1: 准备阶段** (4 小时)

| 任务 ID | 任务描述                                  | 预计耗时 | 负责人 | 输出物                |
| ------- | ----------------------------------------- | -------- | ------ | --------------------- |
| P1-T1   | 备份当前代码和数据库                      | 0.5h     | 开发   | 备份文件              |
| P1-T2   | 创建 Git 特性分支 `feature/simplify-v2.1` | 0.5h     | 开发   | Git 分支              |
| P1-T3   | 安装 APScheduler 依赖                     | 0.5h     | 开发   | requirements.txt 更新 |
| P1-T4   | 编写 APScheduler 单元测试                 | 2.5h     | 开发   | test_scheduler.py     |

**验收标准：**

- ✅ 备份完成，可回滚
- ✅ Git 分支创建成功
- ✅ APScheduler 安装成功
- ✅ 单元测试通过率 100%

---

#### **Phase 2: 核心改造** (8 小时)

| 任务 ID | 任务描述               | 预计耗时 | 负责人 | 输出物                 |
| ------- | ---------------------- | -------- | ------ | ---------------------- |
| P2-T1   | 实现 SimpleRateLimiter | 1h       | 开发   | simple_rate_limiter.py |
| P2-T2   | 移除 SlowAPI 中间件    | 1h       | 开发   | main.py 更新           |
| P2-T3   | 集成 APScheduler       | 2h       | 开发   | scheduler.py           |
| P2-T4   | 迁移 PPT 转换任务      | 2h       | 开发   | media.py 更新          |
| P2-T5   | 简化 JWT 密钥配置      | 1h       | 开发   | config.py 更新         |
| P2-T6   | 删除废弃文件           | 1h       | 开发   | 清理代码               |

**关键代码示例：**

**P2-T1: 实现简单限流器**

```python
# app/utils/simple_rate_limiter.py
from fastapi import Depends, HTTPException, status, Request
from collections import defaultdict
import time

class SimpleRateLimiter:
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)

    async def __call__(self, request: Request):
        client_ip = request.client.host
        now = time.time()

        # 清理过期记录
        self.requests[client_ip] = [
            t for t in self.requests[client_ip]
            if now - t < self.window_seconds
        ]

        # 检查是否超过限制
        if len(self.requests[client_ip]) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests. Limit: {self.max_requests}/{window_seconds}s"
            )

        self.requests[client_ip].append(now)

# 实例化
rate_limiter = SimpleRateLimiter()
```

**P2-T3: 集成 APScheduler**

```python
# app/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from app.utils.logger import logger

# 创建调度器
scheduler = BackgroundScheduler(
    executors={'default': ThreadPoolExecutor(3)},
    timezone='Asia/Shanghai'
)

def submit_ppt_conversion(media_id: int, file_path: str) -> str:
    """提交 PPT 转换任务"""
    job = scheduler.add_job(
        _convert_ppt_task,
        args=[media_id, file_path],
        max_instances=1,
        misfire_grace_time=60
    )
    logger.info(f"Scheduled PPT conversion task: {job.id}")
    return job.id

def _convert_ppt_task(media_id: int, file_path: str):
    """实际执行的 PPT 转换逻辑"""
    from app.services.converter import ConverterService

    try:
        converter = ConverterService()
        converter.convert_ppt_to_video(file_path)
        logger.info(f"PPT conversion completed: {media_id}")
    except Exception as e:
        logger.error(f"PPT conversion failed: {e}")
        raise

# 生命周期管理
def start_scheduler():
    scheduler.start()
    logger.info("APScheduler started")

def stop_scheduler():
    scheduler.shutdown(wait=True)
    logger.info("APScheduler stopped")
```

**验收标准：**

- ✅ 简单限流器工作正常
- ✅ SlowAPI 完全移除
- ✅ APScheduler 正常运行
- ✅ PPT 转换任务迁移完成
- ✅ JWT 配置简化完成

---

#### **Phase 3: 优化改进** (4 小时)

| 任务 ID | 任务描述             | 预计耗时 | 负责人 | 输出物           |
| ------- | -------------------- | -------- | ------ | ---------------- |
| P3-T1   | 启用 SQLite WAL 模式 | 1.5h     | 开发   | database.py 更新 |
| P3-T2   | 简化日志级别配置     | 1h       | 开发   | config.py 更新   |
| P3-T3   | 优化 CORS 白名单     | 0.5h     | 开发   | config.py 更新   |
| P3-T4   | 代码审查和优化       | 1h       | 开发   | Code Review 报告 |

**关键代码示例：**

**P3-T1: SQLite WAL 模式**

```python
# app/database.py
from sqlalchemy import create_engine, event

def get_engine():
    engine = create_engine(
        f"sqlite:///{settings.DATABASE_PATH}",
        connect_args={
            "check_same_thread": False,
            "timeout": 30
        }
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-64000")  # 64MB
        cursor.close()

    return engine
```

**验收标准：**

- ✅ WAL 模式启用成功
- ✅ 日志级别合理（INFO/WARNING）
- ✅ CORS 配置简化（内网白名单）
- ✅ 代码审查通过

---

#### **Phase 4: 测试验证** (4 小时)

| 任务 ID | 任务描述       | 预计耗时 | 负责人 | 输出物       |
| ------- | -------------- | -------- | ------ | ------------ |
| P4-T1   | 执行单元测试   | 1h       | 测试   | 测试报告     |
| P4-T2   | 执行集成测试   | 1.5h     | 测试   | 测试报告     |
| P4-T3   | 性能基准测试   | 1h       | 测试   | 性能报告     |
| P4-T4   | 修复发现的问题 | 0.5h     | 开发   | Bug 修复记录 |

**测试覆盖范围：**

```yaml
单元测试:
  - test_simple_rate_limiter.py # 限流器测试
  - test_scheduler.py # 调度器测试
  - test_jwt_simplified.py # JWT 简化测试

集成测试:
  - test_media_upload.py # 媒体上传 + PPT 转换
  - test_auth_flow.py # 认证流程
  - test_api_endpoints.py # API 端点测试

性能测试:
  - 并发读取测试（WAL 模式）
  - 限流器性能测试
  - 任务队列延迟测试
```

**验收标准：**

- ✅ 单元测试通过率 100%
- ✅ 集成测试通过率 100%
- ✅ 性能指标达标（并发>100，延迟<500ms）
- ✅ 无 P0/P1 级别 Bug

---

#### **Phase 5: 部署上线** (4 小时)

| 任务 ID | 任务描述           | 预计耗时 | 负责人    | 输出物           |
| ------- | ------------------ | -------- | --------- | ---------------- |
| P5-T1   | 代码合并到主分支   | 0.5h     | Tech Lead | Git Merge Record |
| P5-T2   | 构建 Docker 镜像   | 1h       | DevOps    | Docker Image     |
| P5-T3   | 部署到测试环境验证 | 1h       | DevOps    | 部署报告         |
| P5-T4   | 部署到生产环境     | 1h       | DevOps    | 部署记录         |
| P5-T5   | 监控和观察         | 0.5h     | 全体      | 监控报告         |

**部署检查清单：**

```yaml
部署前检查:
  - [ ] 代码审查通过
  - [ ] 所有测试通过
  - [ ] 备份生产数据库
  - [ ] 准备回滚方案

部署中检查:
  - [ ] Docker 镜像构建成功
  - [ ] 容器启动正常
  - [ ] 健康检查通过
  - [ ] 日志无 ERROR

部署后检查:
  - [ ] API 响应正常
  - [ ] 数据库连接正常
  - [ ] PPT 转换功能正常
  - [ ] 播放端心跳正常
```

**验收标准：**

- ✅ 生产环境部署成功
- ✅ 所有功能正常运行
- ✅ 无异常日志
- ✅ 监控指标正常

---

## 6. 风险评估

### 6.1 技术风险

| 风险项                 | 可能性 | 影响程度 | 缓解措施                   |
| ---------------------- | ------ | -------- | -------------------------- |
| **APScheduler 不稳定** | 低     | 高       | 选择成熟版本，充分测试     |
| **简单限流器被绕过**   | 中     | 低       | 内网场景可接受，后续可加强 |
| **WAL 模式兼容性问题** | 低     | 中       | 测试环境充分验证           |
| **JWT 固定密钥泄露**   | 低     | 高       | 仅限内网，物理隔离         |

### 6.2 业务风险

| 风险项                 | 可能性 | 影响程度 | 缓解措施                     |
| ---------------------- | ------ | -------- | ---------------------------- |
| **PPT 转换失败率上升** | 低     | 高       | 保留重试机制，添加告警       |
| **播放端状态采集延迟** | 低     | 中       | 保留 WebSocket，不做轮询改造 |
| **管理员登录不便**     | 低     | 低       | 简化配置，不影响正常使用     |

### 6.3 回滚方案

```bash
# 如果出现问题，快速回滚步骤

# Step 1: 停止当前服务
docker-compose down

# Step 2: 恢复备份
cp backups/castplay.db.bak data/castplay.db

# Step 3: 切换到旧版本代码
git checkout v2.0.0

# Step 4: 重新启动
docker-compose up -d

# 回滚时间：<10 分钟
```

---

## 7. 验收标准

### 7.1 功能验收

```yaml
核心功能测试:
  - ✅ 管理员登录/登出
  - ✅ 媒体文件上传
  - ✅ PPT 自动转换视频
  - ✅ 播放列表创建/编辑
  - ✅ 播放端心跳上报
  - ✅ 播放端状态监控

性能指标:
  - ✅ API 响应时间 <200ms (P95)
  - ✅ PPT 转换成功率 >95%
  - ✅ 并发读取 >100 (WAL 模式)
  - ✅ 限流器额外延迟 <10ms

代码质量:
  - ✅ 单元测试覆盖率 >80%
  - ✅ 无 P0/P1 级别 Bug
  - ✅ Code Review 评分 >90 分
```

### 7.2 文档验收

```yaml
需要更新的文档:
  - ✅ README.md (更新架构图)
  - ✅ DEPLOYMENT.md (更新部署步骤)
  - ✅ API 文档 (如有变更)
  - ✅ 测试报告
  - ✅ 本设计方案
```

### 7.3 交付物清单

```yaml
代码交付:
  - ✅ 源代码（Git 仓库）
  - ✅ Docker 镜像
  - ✅ 依赖清单 (requirements.txt)

文档交付:
  - ✅ 设计方案文档（本文件）
  - ✅ 测试报告
  - ✅ 部署手册
  - ✅ 用户手册（如有更新）

培训交付:
  - ✅ 代码走查会议
  - ✅ 部署演示
  - ✅ FAQ 文档
```

---

## 附录

### A. 依赖对比表

| 类别         | 优化前            | 优化后                 | 变化    |
| ------------ | ----------------- | ---------------------- | ------- |
| **核心框架** | FastAPI 0.110.0   | FastAPI 0.110.0        | ✅ 不变 |
| **速率限制** | slowapi 0.1.9     | 自研 SimpleRateLimiter | 🔧 替换 |
| **任务队列** | 自研 TaskQueue    | APScheduler 3.10.4     | 🔧 替换 |
| **数据库**   | SQLAlchemy 2.0.25 | SQLAlchemy 2.0.25      | ✅ 不变 |
| **认证**     | python-jose 3.3.0 | python-jose 3.3.0      | ✅ 不变 |
| **日志**     | loguru 0.7.2      | loguru 0.7.2           | ✅ 不变 |

### B. 代码行数对比

| 模块         | 优化前 | 优化后 | 减少    |
| ------------ | ------ | ------ | ------- |
| **速率限制** | 80 行  | 20 行  | -75% ✅ |
| **任务队列** | 212 行 | 30 行  | -85% ✅ |
| **配置文件** | 126 行 | 100 行 | -20% ✅ |
| **总计**     | 418 行 | 150 行 | -64% ✅ |

### C. 性能对比预测

| 指标             | 优化前  | 优化后   | 提升        |
| ---------------- | ------- | -------- | ----------- |
| **并发读取**     | ~50 QPS | ~200 QPS | +300% ✅    |
| **任务队列延迟** | ~500ms  | ~200ms   | +60% ✅     |
| **代码维护成本** | 高      | 低       | 显著降低 ✅ |
| **部署复杂度**   | 中      | 低       | 降低 ✅     |

---

**文档版本：** v1.0
**最后更新：** 2026-03-06
**下次审查：** 2026-03-13 或执行完成后
