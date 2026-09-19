# CastPlay 优化建议文档

> 本文档记录 CastPlay 项目的代码审查结果和未来优化建议，供后续 production 化时参考。

---

## 项目概述

CastPlay 是一个轻量级数字标牌管理系统，主要技术栈：

| 层级 | 技术 |
|------|------|
| 后端 | FastAPI + SQLAlchemy + SQLite + APScheduler |
| 前端 | React + TypeScript + Vite + Zustand + Ant Design |
| 移动端 | Android (Kotlin + WebView) |
| 测试 | pytest (unit/integration/performance/e2e 分层) |

---

## 主要优点

1. **Bootstrap 分离初始化逻辑** - `app/bootstrap/application.py` 避免 main.py 膨胀，职责清晰
2. **模块化架构清晰** - api/models/services/websocket 分层明确，低耦合高内聚
3. **SQLite WAL 模式优化** - `database.py` 启用 WAL + 64MB cache，提升并发性能
4. **测试分层完善** - unit/integration/performance/e2e 分开，共 116 个测试文件
5. **配置管理完善** - Pydantic Settings + .env 支持，类型安全
6. **设备注册码设计** - 哈希确定性 + 易读字符集（排除 0/O/1/I/L）
7. **播放列表模型简化** - v2.0 移除了 activation toggle，模型更简洁

---

## 优化建议

### 高优先级

#### 1. 引入正式数据库迁移系统

**现状**: `database.py` 的 `init_database()` 包含内联 migration 逻辑，手动检查列是否存在再 ADD。

**问题**:
- schema 变更需要手动写 SQL 补丁
- 多环境部署时迁移顺序难以保证
- 没有迁移版本记录

**建议**: 使用 Alembic 替代内联迁移

```
# 推荐方案
app/migrations/
├── versions/
│   ├── 001_add_device_type.py
│   ├── 002_add_playlist_schedule.py
│   └── ...
├── env.py
└── alembic.ini
```

**影响**: 降低数据库变更风险，支持 rollback

---

#### 2. 拆分 WebSocket Handler

**现状**: `app/websocket/handler.py` (511行) 承担了太多职责。

**建议**: 按功能拆分为多个模块

```
app/websocket/handlers/
├── __init__.py
├── heartbeat.py      # 心跳处理
├── device_register.py # 设备注册/注销
├── playlist_sync.py  # 播放列表同步
└── playback_control.py # 播放控制（暂停/继续/切换）
```

**影响**: 提高可维护性，便于独立测试和扩展

---

#### 3. 建立统一错误处理体系

**现状**: `logger.warning` 和 `logger.error` 混用，没有统一错误码。

**建议**: 引入 `AppError` 基类 + 错误码枚举

```python
# app/core/errors.py
class AppError(Exception):
    """应用异常基类"""
    def __init__(self, code: str, message: str, status_code: int = 500):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)

class NotFoundError(AppError):
    def __init__(self, resource: str):
        super().__init__("NOT_FOUND", f"{resource} not found", 404)

class ValidationError(AppError):
    def __init__(self, field: str, reason: str):
        super().__init__("VALIDATION_ERROR", f"{field}: {reason}", 422)
```

**影响**: 便于前端统一处理，利于日志聚合和监控

---

#### 4. 增加输入验证层

**现状**: API 路由直接接收参数做数据库操作，部分路由没有完全走 Pydantic schema 验证。

**建议**:
- 所有 request body 强制使用 Pydantic schema
- 敏感操作增加额外校验（如设备注册限制 MAC 地址格式）
- 考虑引入 `class-validator` 风格的嵌套校验

**影响**: 提高 API 健壮性，防止无效数据入库

---

### 中优先级

#### 5. 引入 API 版本控制

**现状**: 所有 endpoint 直接挂 `/api/` 下，没有版本前缀。

**建议**:

```
/api/v1/devices
/api/v1/playlists
/api/v1/media
```

**影响**: 便于后续升级，避免破坏性变更

---

#### 6. 增加 Rate Limiting

**现状**: 后端没有请求频率限制。

**建议**:
- 设备注册接口：`/api/devices/register` - 每 IP 5次/分钟
- 播放控制接口：每设备 10次/秒
- 媒体上传接口：每 IP 10次/分钟

```python
# 可用方案
# 1. slowapi (基于 Limiter)
# 2. 自定义中间件 + Redis (生产环境)
# 3. 简单版：内存字典 + 时间窗口 (开发环境)
```

**影响**: 防止恶意请求和意外大量重试

---

#### 7. 静态文件服务优化

**现状**: 前端 dist 直接从 `application.py` 挂载。

**建议**:
- 添加 Cache-Control 头（HTML: no-cache, 静态资源: max-age=31536000）
- 启用 gzip/brotli 压缩
- 考虑 CDN 加速（生产环境）

```python
# app/bootstrap/application.py
from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory="static"), name="static")
# 或使用 nginx/CDN 处理静态资源
```

**影响**: 提高页面加载速度，降低服务器压力

---

#### 8. 添加 Health Check 端点

**现状**: 没有 `/health` 端点。

**建议**:

```python
# app/api/health.py
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": check_db(),
        "scheduler": scheduler.is_running(),
        "websocket": ws_manager.connection_count(),
    }

@app.get("/ready")
async def readiness_check():
    """K8s readiness probe"""
    if not db.is_connected():
        raise HTTPException(503, "Database unavailable")
    return {"status": "ready"}
```

**影响**: 支持容器编排（K8s/Docker Compose）健康检查

---

### 低优先级

#### 9. 改进 SECRET_KEY 管理

**现状**: `config.py` 里 `DEV_SECRET_KEY_FILE` 写入 data 目录。

**建议**:
- `.env.example` 明确标注生产环境必须设置
- 启动时检测是否使用默认密钥，是则警告并退出
- 考虑使用 Docker Secrets 或 K8s Secret

**影响**: 防止误用开发密钥

---

#### 10. 日志轮转配置

**现状**: `loguru` 没有配置日志轮转。

**建议**:

```python
# app/utils/logger.py
from loguru import logger

logger.add(
    "logs/app.log",
    rotation="100 MB",      # 单文件超过 100MB 轮转
    retention="30 days",    # 保留 30 天
    compression="zip",      # 压缩旧日志
    level="INFO",
)
```

**影响**: 防止日志无限增长

---

#### 11. 测试 Fixture 复用

**现状**: 部分 API 测试重复创建相同数据。

**建议**:
- 使用 `factory_boy` 创建可复用测试 fixture
- 考虑引入 `pytest-randomly` 避免测试顺序依赖
- 提取公共 fixture 到 `tests/fixtures/`

**影响**: 减少测试代码重复，提高测试速度

---

#### 12. 考虑引入依赖注入

**现状**: 依赖通过函数参数传递（如 `get_db`），没有统一 DI 容器。

**建议**: 可考虑 FastAPI 原生的 `Depends()` 已足够，不强制引入 DI 框架。

---

## 建议的目录结构优化（可选）

```
app/
├── api/
│   └── v1/                    # 版本控制
│       ├── devices.py
│       ├── playlists.py
│       └── ...
├── core/                      # 核心公共模块
│   ├── errors.py              # 统一错误体系
│   ├── health.py              # 健康检查
│   └── pagination.py          # 分页工具
├── handlers/                  # WebSocket handlers 拆分
│   ├── heartbeat.py
│   ├── device_register.py
│   └── playlist_sync.py
├── migrations/                # Alembic 迁移
│   ├── versions/
│   └── env.py
└── services/
    └── notification.py
```

---

## 优先级汇总

| 优先级 | 建议 | 复杂度 |
|--------|------|--------|
| 高 | 数据库迁移系统 | 中 |
| 高 | WebSocket Handler 拆分 | 低 |
| 高 | 统一错误处理 | 低 |
| 高 | 输入验证层 | 中 |
| 中 | API 版本控制 | 中 |
| 中 | Rate Limiting | 中 |
| 中 | 静态文件优化 | 低 |
| 中 | Health Check | 低 |
| 低 | SECRET_KEY 管理 | 低 |
| 低 | 日志轮转 | 低 |
| 低 | 测试 Fixture 复用 | 中 |
| 低 | 依赖注入 | 中 |

---

## 备注

- 当前版本为简化测试版，以上优化建议主要针对后续 production 化场景
- 高优先级项目建议在上生产前完成
- 实施优化前应先完善单元测试覆盖，避免回归
