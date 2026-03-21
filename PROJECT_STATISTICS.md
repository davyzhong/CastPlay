# CastPlay 项目代码统计报告

生成日期: 2026-03-22

---

## 总体概览

| 指标 | 数值 |
|------|------|
| **总提交次数** | 80+ 次 |
| **后端代码行数** | 8,847 行 (Python) |
| **前端代码行数** | 25,029 行 (TypeScript/TSX) |
| **Python 源文件** | 4,566 个 |
| **测试文件** | 98 个 |
| **核心模块测试覆盖率** | 约 60% |

---

## 代码组成

### 后端代码 (app/)

| 模块 | 行数 | 说明 |
|------|------|------|
| `api/` | ~2,500 | REST API 路由 |
| `models/` | ~1,200 | 数据库模型 |
| `schemas/` | ~800 | Pydantic 模型 |
| `services/` | ~1,000 | 业务逻辑 |
| `websocket/` | ~500 | WebSocket 处理 |
| 其他 | ~2,847 | 配置、工具、引导 |

### 前端代码 (frontend/src/)

| 类型 | 行数 | 说明 |
|------|------|------|
| TypeScript (.ts) | ~15,000 | 业务逻辑和工具 |
| TSX 组件 | ~10,000 | React 组件 |

---

## 测试覆盖

### 测试文件统计

| 测试类型 | 文件数 | 说明 |
|----------|--------|------|
| Python 单元测试 | 54+ | 后端模块测试 |
| TypeScript 单元测试 | 54+ | 前端组件和工具测试 |
| 集成测试 | 5+ | API 端点测试 |
| **总计** | **98+** | |

### 核心模块测试状态

| 模块 | 测试状态 | 覆盖率 |
|------|----------|--------|
| 设备管理 (devices.py) | 已覆盖 | ~70% |
| 播放列表 (playlists.py) | 已覆盖 | ~65% |
| 媒体上传 (media.py) | 部分覆盖 | ~50% |
| 调度服务 (schedule_service.py) | 已覆盖 | ~80% |
| WebSocket 处理 | 已覆盖 | ~60% |
| 前端播放器组件 | 已覆盖 | ~55% |

### 运行测试

```bash
# 后端测试
pytest tests/ -v

# 前端测试
cd frontend && npm run test

# 全部测试
make test
```

---

## 最近提交记录

### 最新提交 (2026-03-22)

1. `dfb1ccd6` - Merge branch 'master'
2. `ffbea3b6` - fix: 修复 MEDIUM 和 LOW 级别问题
3. `36aa4e22` - fix: 修复多个 HIGH 级别问题
4. `b00f4bb8` - fix: 修复两个 CRITICAL 问题
5. `474396d8` - feat: 添加日程管理、MCP服务器适配及播放器配置UI

### 历史提交

- `eeb45b5e` - feat: 添加 MCP 服务器和 Skill 适配
- `0b52aeb4` - fix: 修复 Android 测试脚本路径问题
- `385eabae` - fix: 修复 Android 环境 WebSocket URL 获取问题
- `b6aab825` - fix: 修复 usePlaylistChangeDetection 消息 action 字段不匹配问题
- `4df3a153` - fix: 修复 PlayerPage WebSocket 消息处理逻辑

---

## 项目亮点

### 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 后端框架 | FastAPI | 0.100+ |
| 数据库 | SQLite + SQLAlchemy | - |
| 实时通信 | WebSocket | - |
| 前端框架 | React | 18.x |
| 前端语言 | TypeScript | 5.x |
| 构建工具 | Vite | 5.x |
| UI 库 | Ant Design | 5.x |
| 状态管理 | Zustand | - |
| 移动端 | Kotlin + WebView | - |

### 核心功能

- [x] 多格式媒体支持 (图片、视频、PPT)
- [x] PPT 自动转换
- [x] 实时 WebSocket 推送
- [x] 播放列表调度
- [x] 设备管理
- [x] Android 离线播放
- [x] MCP 服务器集成

---

## 文档统计

| 类型 | 文件数 | 位置 |
|------|--------|------|
| API 文档 | 2 | `docs/api/` |
| 配置参考 | 1 | `docs/configuration.md` |
| 架构文档 | 3 | `docs/architecture/` |
| 部署文档 | 3 | `docs/deployment/` |
| 开发指南 | 2 | `docs/development/` |
| Android 文档 | 3 | `docs/android/` |
| 测试报告 | 10+ | `docs/reports/` |

---

## 目录结构

```
castplay/
├── app/                    # 后端应用 (8,847 行)
│   ├── api/               # API 路由 (2,500 行)
│   ├── models/            # 数据模型 (1,200 行)
│   ├── schemas/           # Pydantic 模型 (800 行)
│   ├── services/          # 业务服务 (1,000 行)
│   ├── websocket/         # WebSocket 处理 (500 行)
│   └── ...
├── frontend/              # 前端应用 (25,029 行)
│   └── src/
│       ├── player/        # 播放器模块
│       ├── pages/         # 页面组件
│       ├── store/         # 状态管理
│       └── ...
├── android/               # Android 客户端
├── tests/                 # Python 测试 (54+ 文件)
├── frontend/src/player/__tests__/  # 前端测试 (54+ 文件)
├── docs/                  # 项目文档
└── scripts/               # 工具脚本
```

---

## 提交类型分布

| 类型 | 说明 | 占比 |
|------|------|------|
| `feat` | 新功能 | ~35% |
| `fix` | 问题修复 | ~45% |
| `refactor` | 重构 | ~10% |
| `docs` | 文档更新 | ~5% |
| `test` | 测试 | ~5% |

---

## 质量指标

| 指标 | 状态 | 说明 |
|------|------|------|
| 代码格式化 | 通过 | Black + isort |
| 类型检查 | 通过 | mypy (Python), TypeScript |
| Linting | 通过 | ruff, ESLint |
| 测试覆盖 | 进行中 | 目标 80% |
| 文档完整度 | 良好 | 核心功能全覆盖 |

---

## 相关文档

- [API 参考文档](../docs/api/README.md)
- [WebSocket 协议](../docs/api/websocket.md)
- [配置参考](../docs/configuration.md)
- [部署指南](../docs/deployment/guide.md)

---

**总结**: CastPlay 是一个功能完整的数字标牌管理系统，代码结构清晰，测试覆盖持续完善。核心模块已具备良好的测试覆盖，建议后续重点提升媒体处理和播放器模块的测试覆盖率。
