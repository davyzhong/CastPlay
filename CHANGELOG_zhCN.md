# 更新日志

本文档记录 CastPlay 项目所有重要的变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，遵循[语义化版本](https://semver.org/lang/zh-CN/spec/v2.0.0.html)。

## [未发布]

### 新增

- GitHub Actions CI/CD 流水线（自动化测试和安全扫描）
- MCP 服务器单元测试基础设施（`mcp/tests/`）
- CLI 单元测试基础设施（`cli/tests/`）
- 安全令牌存储（使用系统 keyring，`cli/secure_storage.py`）
- 共享 API 客户端模块，支持连接池（`mcp/castplay_shared/`）
- 基于 Python `contextvars` 的上下文配置
- 代码审查问题清单（24 个问题已记录）
- MCP README 中英双语文档

### 安全

- **重要**: 用安全的帧率解析替代 `eval()`（file-processor，CVE 类修复）
- **重要**: 令牌存储从明文迁移到系统 keyring
- 对非 localhost URL 且无 HTTPS 的情况发出警告

### 变更

- CLI 配置迁移到 Pydantic v2 `ConfigDict` 语法
- 所有 MCP 服务器版本统一为 2.0.0
- 将废弃的 `datetime.utcnow()` 替换为 `datetime.now(timezone.utc)`
- **简化播放列表分配模型**：播放列表对设备只有"已分配"和"未分配"两种状态（取消激活/停用开关）

### 修复

- MCP README 中的硬编码用户路径替换为占位符
- 移除 CLI API 客户端中未使用的导入
- 正确处理带 `items` 键的分页 API 响应
- 正确处理 204 No Content 响应
- 修正播放列表分配 API 端点
- schedule-manager 中添加缺失的 `httpx` 导入
- schedule-manager 中添加时间格式验证（HH:MM:SS）

### 移除

- MCP API 客户端中的全局状态变更（改用 contextvars）
- **破坏性变更**: 播放列表激活端点（`/api/playlists/{id}/devices/{device_id}/activate`）
- **破坏性变更**: WebSocket 消息类型 `playlist_activated` 和 `playlist_deactivated`
- **破坏性变更**: `DevicePlaylist` 模型中 `is_active` 字段的实际使用（保留字段以兼容，始终为 `True`）

### 破坏性变更

- **播放列表分配简化**：播放列表激活功能已移除。分配给设备的播放列表现在始终被视为"已激活"。这简化了数据模型和 API。
  - 移除：`/api/playlists/{playlist_id}/devices/{device_id}/activate` 端点
  - 移除：`playlist_activated` 和 `playlist_deactivated` WebSocket 消息
  - 变更：`DevicePlaylist.is_active` 对已分配的播放列表始终为 `True`
  - 迁移：现有的未激活分配将被视为已激活，无需数据迁移

## [2.0.0] - 2026-03-18

### 新增

- **MCP 服务器**：Claude Code 集成的 Model Context Protocol 服务器
  - `device-control`：设备管理和播放控制
  - `playlist-manager`：播放列表和媒体管理
  - `schedule-manager`：基于时间的播放列表调度
  - `ppt-converter`：PPT 转视频/图片转换
  - `android-tools`：Android SDK 集成（模拟器、APK）
  - `file-processor`：媒体文件处理工具
- **CLI 命令**：基于 Typer 的命令行界面
  - `castplay devices`：设备管理命令
  - `castplay playlists`：播放列表管理命令
  - `castplay schedules`：调度管理命令
  - `castplay media`：媒体管理命令
  - `castplay control`：设备控制命令
  - `castplay status`：系统状态命令
  - `castplay server`：服务器管理命令
  - `castplay db`：数据库管理命令
- **Claude Code Skills**：工作流自动化技能
  - `/device-control`：交互式设备控制工作流
  - `/deploy-content`：端到端内容部署工作流
  - `/ppt-to-signage`：一键 PPT 转数字标牌

### 变更

- **破坏性变更**：API 客户端重构为使用连接池的共享模块
- **破坏性变更**：配置改用基于上下文的依赖注入
- 改进所有 MCP 服务器的错误处理

### 修复

- 正确处理带 `items` 键的分页 API 响应
- 正确处理 204 No Content 响应
- 修正播放列表分配 API 端点

## [1.0.0] - 2024-12-01

### 新增

- CastPlay 数字标牌系统初始版本
- FastAPI 后端 + SQLite 数据库
- React 前端 + 管理后台
- Android 播放器客户端（离线缓存）
- WebSocket 实时通信
- 多格式媒体支持（图片、视频、PPT）
- 设备注册和管理
- 播放列表调度系统
