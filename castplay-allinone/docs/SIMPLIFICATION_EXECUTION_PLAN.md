# CastPlay All-in-One 小规模优化执行计划

**版本：** v1.0
**制定日期：** 2026-03-06
**总工期：** 3 天
**执行人：** 开发团队

---

## 📋 目录

1. [执行概览](#1-执行概览)
2. [阶段详细计划](#2-阶段详细计划)
3. [每日工作计划](#3-每日工作计划)
4. [风险管理](#4-风险管理)
5. [沟通机制](#5-沟通机制)

---

## 1. 执行概览

### 1.1 项目信息

```yaml
项目名称：CastPlay 小规模优化 v2.1
开始日期：2026-03-07
结束日期：2026-03-11
总工时：24 小时（3 人天）
关键路径：Phase 2 核心改造
里程碑:
  - M1: Phase 1 完成（准备就绪）
  - M2: Phase 2 完成（核心功能迁移）
  - M3: Phase 4 完成（测试通过）
  - M4: Phase 5 完成（上线成功）
```

### 1.2 团队角色

```yaml
开发负责人 (Dev Lead):
  - 负责：核心代码改造、Code Review
  - 工时：2 天

测试工程师 (QA Engineer):
  - 负责：测试用例编写和执行
  - 工时：1 天

运维工程师 (DevOps):
  - 负责：部署脚本、Docker 镜像
  - 工时：0.5 天

项目经理 (PM):
  - 负责：进度跟踪、风险管控
  - 工时：0.5 天
```

### 1.3 关键依赖

```yaml
外部依赖:
  - APScheduler 包安装：无风险（成熟库）
  - Docker 环境：已就绪
  - 测试环境：已就绪

内部依赖:
  - 备份完成前：不可开始 Phase 2
  - 单元测试通过前：不可开始集成测试
  - Code Review 通过前：不可合并主分支
```

---

## 2. 阶段详细计划

### Phase 1: 准备阶段 (Day 1 上午，4 小时)

#### 📍 里程碑 M1: 准备就绪

**完成标准：** 所有准备工作完成，可以开始核心改造

| 时间        | 任务                    | 负责人   | 输出物                 | 验收方式                       |
| ----------- | ----------------------- | -------- | ---------------------- | ------------------------------ |
| 09:00-09:30 | P1-T1: 备份代码和数据库 | DevOps   | backup_20260307.tar.gz | 检查备份文件完整性             |
| 09:30-10:00 | P1-T2: 创建 Git 分支    | Dev Lead | feature/simplify-v2.1  | `git branch` 验证              |
| 10:00-10:30 | P1-T3: 安装 APScheduler | Dev Lead | requirements.txt 更新  | `pip list \| grep APScheduler` |
| 10:30-12:00 | P1-T4: 编写单元测试     | QA       | test_scheduler.py      | 运行测试通过率 100%            |

**详细步骤：**

**P1-T1: 备份操作**

```bash
# 1. 备份数据库
cd /Users/Davy/PycharmProjects/CastPlay/castplay-allinone
tar -czf backups/backup_$(date +%Y%m%d).tar.gz \
    data/castplay.db \
    data/uploads \
    .env

# 2. 验证备份
tar -tzf backups/backup_*.tar.gz | head -20

# 3. 记录备份日志
echo "Backup completed at $(date)" >> logs/backup.log
```

**P1-T2: Git 分支管理**

```bash
# 1. 确保在 master 分支
git checkout master
git pull origin master

# 2. 创建特性分支
git checkout -b feature/simplify-v2.1

# 3. 推送到远程
git push -u origin feature/simplify-v2.1
```

**P1-T3: 依赖安装**

```bash
# 1. 更新 requirements.txt
cat >> requirements.txt << EOF

# APScheduler - 后台任务调度
APScheduler==3.10.4
EOF

# 2. 安装依赖
pip install -r requirements.txt

# 3. 验证安装
python -c "from apscheduler.schedulers.background import BackgroundScheduler; print('OK')"
```

**P1-T4: 单元测试框架**

```python
# tests/test_scheduler.py
import pytest
from unittest.mock import Mock, patch
from app.scheduler import scheduler, submit_ppt_conversion

class TestScheduler:
    """测试 APScheduler 功能"""

    def test_scheduler_initialization(self):
        """测试调度器初始化"""
        assert scheduler is not None
        assert len(scheduler.executors) > 0

    @patch('app.scheduler._convert_ppt_task')
    def test_submit_ppt_conversion(self, mock_convert):
        """测试提交 PPT 转换任务"""
        job_id = submit_ppt_conversion(1, "/tmp/test.pptx")
        assert job_id is not None
        assert isinstance(job_id, str)

        # 验证任务已添加到调度器
        job = scheduler.get_job(job_id)
        assert job is not None
```

**阶段评审会：**

- 时间：Day 1 12:00
- 参与：全体
- 内容：确认 M1 达成，进入 Phase 2

---

### Phase 2: 核心改造 (Day 1 下午 + Day 2 全天，8 小时)

#### 📍 里程碑 M2: 核心功能迁移完成

**完成标准：** SlowAPI 移除，APScheduler 集成，所有核心功能正常

#### Day 1 下午 (13:30-18:00, 4.5 小时)

| 时间        | 任务                          | 负责人   | 输出物                 | 验收方式         |
| ----------- | ----------------------------- | -------- | ---------------------- | ---------------- |
| 13:30-14:30 | P2-T1: 实现 SimpleRateLimiter | Dev Lead | simple_rate_limiter.py | Code Review      |
| 14:30-15:30 | P2-T2: 移除 SlowAPI           | Dev Lead | main.py, auth.py       | 启动应用验证     |
| 15:30-16:00 | ☕ 休息                       | -        | -                      | -                |
| 16:00-18:00 | P2-T3: 集成 APScheduler       | Dev Lead | scheduler.py           | 手动触发任务验证 |

**详细步骤：**

**P2-T1: 简单限流器实现**

```python
# app/utils/simple_rate_limiter.py
"""
简单速率限制器 - 替代 SlowAPI
适用于内网小规模场景
"""
from fastapi import Depends, HTTPException, status, Request
from collections import defaultdict
import time

class SimpleRateLimiter:
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, list[float]] = defaultdict(list)

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
                detail=f"请求过于频繁，请稍后再试"
            )

        self.requests[client_ip].append(now)

# 全局实例
rate_limiter = SimpleRateLimiter(max_requests=100, window_seconds=60)
```

**P2-T2: 移除 SlowAPI**

```python
# app/main.py 修改
# === 删除的代码 ===
# from app.middleware.rate_limit import setup_rate_limit
# setup_rate_limit(app)  # 删除此行

# app/api/auth.py 修改
# === 删除的代码 ===
# from app.middleware.rate_limit import limiter
# @limiter.limit("5/minute")  # 删除此装饰器

# === 新增的代码 ===
from app.utils.simple_rate_limiter import rate_limiter

@app.post("/login", dependencies=[Depends(rate_limiter)])
async def login(...):
    ...
```

**P2-T3: APScheduler 集成**

```python
# app/scheduler.py
"""
后台任务调度器 - 使用 APSScheduler 替代自研 TaskQueue
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from app.config import settings
from app.utils.logger import logger

# 创建调度器（3 个 Worker 线程）
scheduler = BackgroundScheduler(
    executors={'default': ThreadPoolExecutor(3)},
    timezone='Asia/Shanghai'
)

def submit_ppt_conversion(media_id: int, file_path: str) -> str:
    """提交 PPT 转换任务"""
    logger.info(f"Scheduling PPT conversion: media_id={media_id}")

    job = scheduler.add_job(
        _convert_ppt_task,
        args=[media_id, file_path],
        max_instances=1,  # 同一任务只允许 1 个实例
        misfire_grace_time=60,  # 容忍 60 秒延迟
        replace_existing=True  # 替换同名任务
    )

    logger.info(f"Task scheduled with job_id: {job.id}")
    return job.id

def _convert_ppt_task(media_id: int, file_path: str):
    """实际执行的 PPT 转换逻辑"""
    from app.services.converter import ConverterService

    try:
        logger.info(f"Starting PPT conversion: {media_id}")
        converter = ConverterService()
        result = converter.convert_ppt_to_video(file_path)
        logger.info(f"PPT conversion completed: {result}")
    except Exception as e:
        logger.error(f"PPT conversion failed: {e}", exc_info=True)
        raise

# 生命周期管理
def start():
    """启动调度器"""
    scheduler.start()
    logger.info("APScheduler started")

def stop():
    """停止调度器"""
    scheduler.shutdown(wait=True)
    logger.info("APScheduler stopped")
```

#### Day 2 全天 (09:00-18:00, 8 小时，含午休)

| 时间        | 任务                     | 负责人        | 输出物         | 验收方式            |
| ----------- | ------------------------ | ------------- | -------------- | ------------------- |
| 09:00-10:30 | P2-T4: 迁移 PPT 转换任务 | Dev Lead      | media.py 更新  | 上传 PPT 并验证转换 |
| 10:30-11:30 | P2-T5: 简化 JWT 配置     | Dev Lead      | config.py 更新 | 登录验证 Token 有效 |
| 11:30-12:00 | P2-T6: 删除废弃文件      | Dev Lead      | 代码清理       | `git status` 验证   |
| 12:00-13:30 | 🍽️ 午休                  | -             | -              | -                   |
| 13:30-15:00 | P2-T7: 兼容性测试        | Dev Lead + QA | 测试报告       | 核心流程测试通过    |
| 15:00-16:30 | P2-T8: Bug 修复          | Dev Lead      | Bug 修复记录   | 回归测试通过        |
| 16:30-18:00 | P2-T9: Code Review       | 全体          | CR 报告        | 评分>90 分          |

**详细步骤：**

**P2-T4: PPT 转换任务迁移**

```python
# app/api/media.py 修改
# === 旧代码 ===
# from app.workers import task_manager
# task_manager.submit_task("convert_ppt", {...})

# === 新代码 ===
from app.scheduler import submit_ppt_conversion

@app.post("/api/media/{media_id}/convert")
async def convert_media(media_id: int):
    """将 PPT 转换为视频"""
    media = get_media_or_404(media_id)

    if not media.file_path.endswith(('.ppt', '.pptx')):
        raise HTTPException(400, "Only PPT files can be converted")

    # 提交任务到 APScheduler
    job_id = submit_ppt_conversion(media_id, media.file_path)

    return {
        "status": "processing",
        "job_id": job_id,
        "message": "PPT conversion started"
    }
```

**P2-T5: JWT 密钥简化**

```python
# app/config.py 修改
import os

class Settings(BaseSettings):
    # ... 其他配置 ...

    @property
    def SECRET_KEY(self) -> str:
        """JWT 密钥 - 内网简化版"""
        env_key = os.getenv("SECRET_KEY")

        if self.ENVIRONMENT == "production":
            # 生产环境必须设置
            if not env_key:
                raise ValueError(
                    "生产环境必须通过环境变量设置 SECRET_KEY"
                )
            return env_key
        else:
            # 开发/内网环境使用固定密钥
            return env_key or "castplay-dev-secret-key-2026-do-not-use-in-production"
```

**P2-T6: 删除废弃文件**

```bash
# 1. 删除 SlowAPI 相关文件
rm app/middleware/rate_limit.py

# 2. 删除 TaskQueue 相关文件
rm app/workers/task_queue.py

# 3. 更新 __init__.py 导入
# app/middleware/__init__.py - 删除 rate_limit 导入
# app/workers/__init__.py - 删除 task_manager 导入

# 4. 验证删除
git status
```

**P2-T7: 兼容性测试**

```python
# tests/test_compatibility.py
class TestCompatibility:
    """测试新旧代码兼容性"""

    def test_ppt_conversion_flow(self, client, test_db):
        """测试完整的 PPT 转换流程"""
        # 1. 上传 PPT
        response = client.post("/api/media/upload", files={...})
        media_id = response.json()["id"]

        # 2. 触发转换
        response = client.post(f"/api/media/{media_id}/convert")
        assert response.status_code == 200

        # 3. 等待转换完成（轮询）
        for _ in range(10):
            response = client.get(f"/api/media/{media_id}")
            if response.json()["converted"]:
                break
            time.sleep(2)

        assert response.json()["converted"] is True
```

**阶段评审会：**

- 时间：Day 2 18:00
- 参与：全体
- 内容：确认 M2 达成，进入 Phase 3

---

### Phase 3: 优化改进 (Day 3 上午，4 小时)

#### 📍 里程碑 M3: 优化完成

**完成标准：** SQLite WAL 启用，配置优化完成

| 时间        | 任务                   | 负责人   | 输出物           | 验收方式     |
| ----------- | ---------------------- | -------- | ---------------- | ------------ |
| 09:00-10:30 | P3-T1: SQLite WAL 模式 | Dev Lead | database.py 更新 | 并发测试验证 |
| 10:30-11:30 | P3-T2: 简化日志配置    | Dev Lead | config.py 更新   | 日志级别验证 |
| 11:30-12:00 | P3-T3: CORS 优化       | Dev Lead | config.py 更新   | 跨域请求验证 |
| 12:00-13:30 | 🍽️ 午休                | -        | -                | -            |
| 13:30-15:00 | P3-T4: Code Review     | 全体     | CR 报告          | 问题清单     |
| 15:00-16:00 | P3-T5: 文档更新        | Dev Lead | README.md 等     | 文档审查     |

**详细步骤：**

**P3-T1: SQLite WAL 模式**

```python
# app/database.py 修改
from sqlalchemy import create_engine, event

def init_database():
    """初始化数据库（启用 WAL 模式）"""
    engine = create_engine(
        f"sqlite:///{settings.DATABASE_PATH}",
        connect_args={
            "check_same_thread": False,
            "timeout": 30  # 锁等待超时 30 秒
        }
    )

    # 启用 WAL 模式和其他优化
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-64000")  # 64MB 缓存
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    return engine
```

**P3-T2: 简化日志配置**

```python
# app/config.py 添加
import sys

class Settings(BaseSettings):
    # ... 其他配置 ...

    @property
    def LOG_LEVEL(self) -> str:
        """日志级别 - 根据环境自动调整"""
        if self.ENVIRONMENT == "production":
            return "INFO"  # 生产环境仅记录关键日志
        else:
            return "DEBUG"  # 开发环境记录详细日志

# app/utils/logger.py 修改
from loguru import logger
from app.config import settings

logger.remove()  # 移除默认处理器
logger.add(
    sys.stderr,
    level=settings.LOG_LEVEL,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
)
```

**P3-T3: CORS 优化**

```python
# app/config.py 修改
class Settings(BaseSettings):
    # ... 其他配置 ...

    @property
    def CORS_ORIGINS(self) -> list[str]:
        """CORS 白名单 - 内网简化版"""
        if self.ENVIRONMENT == "production":
            # 生产环境从环境变量读取
            origins_str = os.getenv("CORS_ORIGINS", "")
            return [o.strip() for o in origins_str.split(",") if o.strip()]
        else:
            # 开发环境允许所有来源
            return ["*"]
```

**阶段评审会：**

- 时间：Day 3 15:00
- 参与：全体
- 内容：确认 M3 达成，进入 Phase 4

---

### Phase 4: 测试验证 (Day 3 下午，4 小时)

#### 📍 里程碑 M4: 测试通过

**完成标准：** 所有测试通过，无 P0/P1 Bug

| 时间        | 任务            | 负责人   | 输出物   | 验收方式           |
| ----------- | --------------- | -------- | -------- | ------------------ |
| 15:00-16:00 | P4-T1: 单元测试 | QA       | 测试报告 | 覆盖率>80%         |
| 16:00-17:00 | P4-T2: 集成测试 | QA       | 测试报告 | 核心流程 100% 通过 |
| 17:00-17:30 | P4-T3: 性能测试 | Dev Lead | 性能报告 | 指标达标           |
| 17:30-18:00 | P4-T4: Bug 修复 | Dev Lead | Bug 清单 | 无 P0/P1 Bug       |

**测试执行计划：**

**P4-T1: 单元测试**

```bash
# 执行所有单元测试
cd /Users/Davy/PycharmProjects/CastPlay/castplay-allinone

# 运行测试并生成覆盖率报告
pytest tests/unit/ \
    --cov=app \
    --cov-report=html \
    --cov-report=term-missing \
    -v \
    --tb=short

# 查看覆盖率
open htmlcov/index.html
```

**P4-T2: 集成测试**

```bash
# 执行集成测试
pytest tests/integration/ \
    -v \
    --tb=long \
    -k "test_media or test_auth or test_playlist"

# 关键测试用例:
# - test_media_upload_and_convert.py
# - test_auth_flow.py
# - test_playlist_crud.py
```

**P4-T3: 性能测试**

```python
# tests/performance/test_simplification.py
import pytest
import time
from concurrent.futures import ThreadPoolExecutor

class TestPerformance:
    """性能测试"""

    def test_concurrent_read(self, client):
        """测试并发读取（WAL 模式）"""
        def make_request():
            start = time.time()
            response = client.get("/api/devices")
            elapsed = time.time() - start
            return response.status_code, elapsed

        # 100 个并发请求
        with ThreadPoolExecutor(max_workers=100) as executor:
            results = list(executor.map(make_request, range(100)))

        # 验证成功率
        success_count = sum(1 for status, _ in results if status == 200)
        assert success_count >= 95  # 95% 成功率

        # 验证平均响应时间
        avg_time = sum(t for _, t in results) / len(results)
        assert avg_time < 0.5  # 平均<500ms

    def test_rate_limiter_performance(self, client):
        """测试限流器性能"""
        start = time.time()

        # 连续 1000 次请求
        for _ in range(1000):
            try:
                client.get("/api/devices")
            except:
                pass

        elapsed = time.time() - start
        # 限流器额外延迟应<10ms/请求
        assert elapsed < 10.0  # 1000 次<10 秒
```

**阶段评审会：**

- 时间：Day 3 18:00
- 参与：全体
- 内容：确认 M4 达成，准备上线

---

### Phase 5: 部署上线 (Day 4 上午，4 小时)

#### 📍 里程碑 M5: 上线成功

**完成标准：** 生产环境正常运行，监控指标正常

| 时间        | 任务                   | 负责人   | 输出物           | 验收方式        |
| ----------- | ---------------------- | -------- | ---------------- | --------------- |
| 09:00-09:30 | P5-T1: 代码合并        | Dev Lead | Git Merge Record | `git log` 验证  |
| 09:30-10:30 | P5-T2: Docker 镜像构建 | DevOps   | Docker Image     | `docker images` |
| 10:30-11:30 | P5-T3: 测试环境验证    | DevOps   | 部署报告         | 功能验证        |
| 11:30-12:00 | 🍽️ 午休准备            | -        | -                | -               |
| 12:00-13:00 | P5-T4: 生产部署        | DevOps   | 部署记录         | 健康检查        |
| 13:00-13:30 | P5-T5: 监控观察        | 全体     | 监控报告         | 无异常告警      |

**详细步骤：**

**P5-T1: 代码合并**

```bash
# 1. 切换到 master 分支
git checkout master
git pull origin master

# 2. 合并特性分支
git merge --no-ff feature/simplify-v2.1 \
    -m "feat: 小规模优化 v2.1

- 移除 SlowAPI，改用简单限流器
- 替换 TaskQueue 为 APScheduler
- 简化 JWT 密钥管理
- 启用 SQLite WAL 模式

BREAKING CHANGE: 需要安装 APScheduler 依赖"

# 3. 推送到远程
git push origin master
```

**P5-T2: Docker 镜像构建**

```bash
# 1. 构建新镜像
cd /Users/Davy/PycharmProjects/CastPlay/castplay-allinone
docker build -t castplay-allinone:v2.1 .

# 2. 验证镜像
docker images | grep castplay

# 3. 推送镜像（如有仓库）
docker tag castplay-allinone:v2.1 registry.example.com/castplay:v2.1
docker push registry.example.com/castplay:v2.1
```

**P5-T3: 测试环境验证**

```bash
# 1. 停止测试环境
docker-compose -f docker-compose.test.yml down

# 2. 启动新版本
docker-compose -f docker-compose.test.yml up -d

# 3. 健康检查
curl http://localhost:5000/health

# 4. 功能验证
# - 登录测试
# - 上传 PPT 测试
# - 播放端心跳测试
```

**P5-T4: 生产部署**

```bash
# 1. 备份生产数据
ssh production-server
cd /opt/castplay
tar -czf /backups/backup_$(date +%Y%m%d_%H%M%S).tar.gz \
    data/ \
    .env

# 2. 停止旧版本
docker-compose down

# 3. 拉取新镜像
docker pull registry.example.com/castplay:v2.1

# 4. 启动新版本
docker-compose up -d

# 5. 健康检查
curl http://localhost:5000/health
docker-compose logs -f
```

**P5-T5: 监控观察**

```python
# 监控检查清单
monitoring_checklist = {
    "API 响应时间": {"目标": "<200ms", "实际": "..."},
    "错误率": {"目标": "<1%", "实际": "..."},
    "CPU 使用率": {"目标": "<70%", "实际": "..."},
    "内存使用率": {"目标": "<80%", "实际": "..."},
    "数据库连接": {"目标": "正常", "实际": "..."},
    "PPT 转换成功率": {"目标": ">95%", "实际": "..."}
}
```

**项目总结会：**

- 时间：Day 4 14:00
- 参与：全体 + 利益相关者
- 内容：
  - 展示成果
  - 回顾过程
  - 经验总结
  - 下一步规划

---

## 3. 每日工作计划

### Day 1: 准备 + 核心改造启动

```
09:00-09:30  站会（同步今日计划）
09:30-12:00  Phase 1: 准备阶段
12:00-13:30  午休
13:30-18:00  Phase 2: 核心改造（上）
18:00-18:30  站会（同步进度和问题）
```

### Day 2: 核心改造完成

```
09:00-09:15  站会（快速同步）
09:15-12:00  Phase 2: 核心改造（中）
12:00-13:30  午休
13:30-18:00  Phase 2: 核心改造（下）+ Code Review
18:00-18:30  站会（确认 M2 达成）
```

### Day 3: 优化 + 测试

```
09:00-09:15  站会
09:15-12:00  Phase 3: 优化改进
12:00-13:30  午休
13:30-18:00  Phase 4: 测试验证
18:00-18:30  站会（确认 M4 达成）
```

### Day 4: 部署上线

```
09:00-09:15  站会
09:15-12:00  Phase 5: 部署上线
12:00-13:30  午休
13:30-14:30  项目总结会
14:30-     庆功宴 🎉
```

---

## 4. 风险管理

### 4.1 技术风险应对

| 风险                    | 概率 | 影响 | 应对措施                    |
| ----------------------- | ---- | ---- | --------------------------- |
| **APScheduler 不兼容**  | 低   | 高   | 预留 2 小时缓冲，必要时回退 |
| **SQLite WAL 模式失败** | 低   | 中   | 立即切换回默认模式          |
| **限流器性能不达标**    | 中   | 低   | 放宽限制或临时启用 SlowAPI  |
| **JWT 密钥泄露**        | 低   | 高   | 仅限内网，物理隔离          |

### 4.2 进度风险应对

```yaml
缓冲时间:
  - Phase 2: 预留 2 小时缓冲
  - Phase 4: 预留 1 小时缓冲

赶工计划:
  - 如果 Phase 2 延期：压缩 Phase 3 时间
  - 如果 Phase 4 延期：部分非关键测试延后执行

最小可用版本 (MVP):
  - 必须完成：P2-T1/T2/T3 (限流器 + APScheduler)
  - 可选延后：P3-T1/T2/T3 (优化改进)
```

### 4.3 回滚方案

```bash
#!/bin/bash
# rollback.sh - 紧急回滚脚本

echo "🚨 Starting emergency rollback..."

# 1. 停止服务
docker-compose down

# 2. 恢复数据库
cp backups/backup_*.tar.gz data/restore.tar.gz
tar -xzf data/restore.tar.gz -C data/

# 3. 切换代码
git checkout master
git reset --hard HEAD~1  # 回退一个版本

# 4. 重启旧版本
docker-compose up -d

echo "✅ Rollback completed!"
echo "⏱️  预计耗时：10 分钟"
```

---

## 5. 沟通机制

### 5.1 会议安排

```yaml
每日站会:
  - 时间：每天 09:00, 18:00
  - 时长：15 分钟
  - 内容：昨日进展、今日计划、阻塞问题

阶段评审会:
  - Phase 1 完成：Day 1 12:00
  - Phase 2 完成：Day 2 18:00
  - Phase 3 完成：Day 3 15:00
  - Phase 4 完成：Day 3 18:00

项目总结会:
  - 时间：Day 4 14:00
  - 参与：全体 + 利益相关者
  - 内容：成果展示、经验总结
```

### 5.2 沟通渠道

```yaml
即时通讯：
  - 微信群：CastPlay 项目组
  - 紧急联系：电话

项目管理:
  - GitLab Issues: 任务跟踪
  - GitLab Merge Requests: 代码审查

文档协作:
  - 腾讯文档：会议纪要
  - GitLab Wiki: 技术文档
```

### 5.3 升级机制

```yaml
问题分级:
  - P0 (阻塞): 立即电话通知 Tech Lead
  - P1 (严重): 微信群@相关负责人，30 分钟内响应
  - P2 (一般): GitLab Issue, 当天解决
  - P3 (轻微): 记录，后续迭代处理

升级路径: 开发工程师 → Tech Lead → 项目经理 → 技术总监
```

---

## 附录

### A. 任务分解 WBS

```
CastPlay 小规模优化 v2.1
├── Phase 1: 准备阶段
│   ├── P1-T1: 备份代码和数据库
│   ├── P1-T2: 创建 Git 分支
│   ├── P1-T3: 安装 APScheduler
│   └── P1-T4: 编写单元测试
├── Phase 2: 核心改造
│   ├── P2-T1: 实现 SimpleRateLimiter
│   ├── P2-T2: 移除 SlowAPI
│   ├── P2-T3: 集成 APScheduler
│   ├── P2-T4: 迁移 PPT 转换任务
│   ├── P2-T5: 简化 JWT 配置
│   ├── P2-T6: 删除废弃文件
│   ├── P2-T7: 兼容性测试
│   ├── P2-T8: Bug 修复
│   └── P2-T9: Code Review
├── Phase 3: 优化改进
│   ├── P3-T1: SQLite WAL 模式
│   ├── P3-T2: 简化日志配置
│   ├── P3-T3: CORS 优化
│   ├── P3-T4: Code Review
│   └── P3-T5: 文档更新
├── Phase 4: 测试验证
│   ├── P4-T1: 单元测试
│   ├── P4-T2: 集成测试
│   ├── P4-T3: 性能测试
│   └── P4-T4: Bug 修复
└── Phase 5: 部署上线
    ├── P5-T1: 代码合并
    ├── P5-T2: Docker 镜像构建
    ├── P5-T3: 测试环境验证
    ├── P5-T4: 生产部署
    └── P5-T5: 监控观察
```

### B. 资源需求

```yaml
人力资源:
  - 开发工程师：2 人 × 3 天 = 6 人天
  - 测试工程师：1 人 × 1 天 = 1 人天
  - 运维工程师：0.5 人天
  - 项目经理：0.5 人天
  总计：8 人天

硬件资源:
  - 测试服务器：1 台（已有）
  - 生产服务器：1 台（已有）
  - 开发电脑：按需

软件资源:
  - GitLab: 代码管理（已有）
  - Docker: 容器化（已有）
  - APScheduler: 新增依赖
```

### C. 验收检查清单

```markdown
## Phase 1 验收清单

- [ ] 备份文件完整
- [ ] Git 分支创建成功
- [ ] APScheduler 安装成功
- [ ] 单元测试通过率 100%

## Phase 2 验收清单

- [ ] SimpleRateLimiter 工作正常
- [ ] SlowAPI 完全移除
- [ ] APScheduler 正常运行
- [ ] PPT 转换功能正常
- [ ] JWT 认证正常
- [ ] 废弃文件已删除
- [ ] Code Review 通过

## Phase 3 验收清单

- [ ] SQLite WAL 模式启用
- [ ] 日志级别合理
- [ ] CORS 配置简化
- [ ] 文档更新完成

## Phase 4 验收清单

- [ ] 单元测试覆盖率>80%
- [ ] 集成测试 100% 通过
- [ ] 性能指标达标
- [ ] 无 P0/P1 Bug

## Phase 5 验收清单

- [ ] 代码合并成功
- [ ] Docker 镜像构建成功
- [ ] 测试环境验证通过
- [ ] 生产部署成功
- [ ] 监控指标正常
```

---

**文档版本：** v1.0
**最后更新：** 2026-03-06
**下次更新：** 执行完成后更新实际数据

**批准签字：**

- 开发负责人：****\_\_\_\_**** 日期：**\_\_\_**
- 项目经理：****\_\_\_\_**** 日期：**\_\_\_**
- 技术总监：****\_\_\_\_**** 日期：**\_\_\_**
