# CastPlay MCP/Skills/CLI 改造分析设计方案

## 一、背景分析

### 1.1 项目现状

CastPlay 是一个轻量级数字标牌管理系统，当前已有的基础设施：

| 类别 | 现状 |
|------|------|
| **MCP Servers** | 3个已存在：ppt-converter, android-tools, file-processor |
| **CLI** | 完整的 Typer CLI：config, devices, playlists, control, status, media, db |
| **Backend API** | FastAPI REST + WebSocket 实时通信 |
| **前端** | React 管理面板 + 播放器页面 |

### 1.2 现有 MCP 工具清单

```
mcp/ppt-converter/     → get_ppt_info, ppt_to_pdf, ppt_to_images, ppt_to_video, check_tools
mcp/android-tools/     → check_android_env, list_avds, list_devices, start/stop_emulator,
                         build_apk, install_apk, take_screenshot, get_device_logs, launch/stop_app
mcp/file-processor/    → get_video_info, extract_video_thumbnail, compress_video,
                         generate_video_preview, check_ffmpeg_available
```

---

## 二、功能改造分析

### 2.1 MCP Server 候选分析

| 候选功能 | 优先级 | 理由 | 复用资源 |
|----------|--------|------|----------|
| **Device Management MCP** | 🔴 高 | Claude 可直接控制设备，是 AI 集成的核心能力 | `NotificationService`, `ConnectionManager`, `/api/control` |
| **Playlist Management MCP** | 🔴 高 | 内容管理的核心，AI 可编程管理播放列表 | `/api/playlists`, `/api/media` |
| **Schedule Management MCP** | 🟡 中 | 时间排程是 001-playlist-scheduling 核心功能 | `/api/schedules`, `ScheduleService` |
| **Analytics MCP** | 🟢 低 | 查询播放统计、设备使用模式 | 数据库查询 |

### 2.2 Skills 候选分析

| 候选功能 | 优先级 | 理由 | 复用资源 |
|----------|--------|------|----------|
| **`/device-control`** | 🔴 高 | 交互式设备控制，带确认机制 | Device MCP, `/api/control` |
| **`/deploy-content`** | 🔴 高 | 端到端内容部署工作流 | Playlist MCP, Media API |
| **`/ppt-to-signage`** | 🟡 中 | 一键 PPT 转数字标牌 | ppt-converter MCP + Device MCP |
| **`/build-android`** | 🟡 中 | APK 构建部署全流程 | android-tools MCP |
| **`/test-push`** | 🟢 低 | WebSocket 推送测试 | `scripts/testing/test_playlist_push.py` |

### 2.3 CLI 增强分析

| 缺失功能 | 优先级 | 理由 |
|----------|--------|------|
| **`castplay schedules`** | 🔴 高 | 排程功能无 CLI 支持，是主要功能缺口 |
| **`castplay playlists items`** | 🔴 高 | 播放列表媒体项管理未暴露 |
| **`castplay server`** | 🟡 中 | 服务启停统一到 CLI |
| **`castplay media upload`** | 🟡 中 | CLI 媒体上传支持自动化 |
| **`castplay users`** | 🟢 低 | 用户管理操作 |

---

## 三、详细设计方案

### 3.1 Device Management MCP Server

**目标**：让 Claude 能直接控制 CastPlay 设备

**文件路径**：`mcp/device-control/`

**工具清单**：

```python
tools = [
    # 设备查询
    "list_devices",           # 获取设备列表，支持过滤（在线/离线）
    "get_device_info",        # 获取设备详细信息
    "get_device_status",      # 获取设备播放状态

    # 播放控制
    "pause_playback",         # 暂停播放
    "resume_playback",        # 恢复播放
    "set_volume",             # 设置音量 (0-100)
    "next_media",             # 下一个媒体
    "prev_media",             # 上一个媒体
    "switch_playlist",        # 切换播放列表
    "reload_playlist",        # 重新加载播放列表

    # 设备管理
    "enable_device",          # 启用设备
    "disable_device",         # 禁用设备
    "reboot_device",          # 重启设备（Android）

    # 实时状态
    "get_online_devices",     # 获取在线设备列表
    "check_device_online",    # 检查设备是否在线
]
```

**实现方式**：
- 复用 `app/api/control.py` 的控制接口
- 复用 `app/services/notification.py` 的 WebSocket 通知
- 复用 `app/api/devices.py` 的设备管理接口

**关键代码复用**：
```
app/api/control.py         → 控制端点实现
app/services/notification.py → NotificationService
app/websocket/handler.py   → ConnectionManager（在线状态）
```

---

### 3.2 Playlist Management MCP Server

**目标**：让 Claude 能管理播放列表和媒体内容

**文件路径**：`mcp/playlist-manager/`

**工具清单**：

```python
tools = [
    # 播放列表管理
    "list_playlists",         # 获取播放列表
    "get_playlist",           # 获取播放列表详情
    "create_playlist",        # 创建播放列表
    "update_playlist",        # 更新播放列表
    "delete_playlist",        # 删除播放列表
    "activate_playlist",      # 激活播放列表
    "deactivate_playlist",    # 停用播放列表

    # 播放列表内容管理
    "add_media_to_playlist",  # 添加媒体到播放列表
    "remove_media_from_playlist",  # 从播放列表移除媒体
    "reorder_playlist_items", # 重新排序播放列表项
    "set_item_duration",      # 设置媒体播放时长

    # 设备分配
    "assign_playlist_to_device",   # 分配播放列表到设备
    "unassign_playlist_from_device", # 取消分配

    # 媒体管理
    "list_media",             # 获取媒体列表
    "get_media_info",         # 获取媒体信息
    "delete_media",           # 删除媒体
]
```

**实现方式**：
- 复用 `/api/playlists` 端点
- 复用 `/api/media` 端点

**关键代码复用**：
```
app/api/playlists.py  → 播放列表 CRUD
app/api/media.py      → 媒体管理
app/models/playlist.py → Playlist 模型
```

---

### 3.3 Schedule Management MCP Server

**目标**：让 Claude 能配置时间排程

**文件路径**：`mcp/schedule-manager/`

**工具清单**：

```python
tools = [
    # 排程管理
    "list_schedules",         # 获取排程列表（按设备）
    "get_schedule",           # 获取排程详情
    "create_schedule",        # 创建排程规则
    "update_schedule",        # 更新排程规则
    "delete_schedule",        # 删除排程规则
    "get_active_schedule",    # 获取当前激活的排程

    # 排程参数
    # - device_id: 设备 ID
    # - playlist_id: 播放列表 ID
    # - start_time: 开始时间 (HH:MM)
    # - end_time: 结束时间 (HH:MM)
    # - weekdays: 星期几 (0-6, 0=周一)
]
```

**实现方式**：
- 复用 `/api/schedules` 端点
- 复用 `ScheduleService` 服务

**关键代码复用**：
```
app/api/schedules.py        → 排程 API
app/services/schedule.py    → ScheduleService
app/models/schedule.py      → Schedule 模型
```

---

### 3.4 CLI 增强：schedules 命令组

**文件路径**：`cli/commands/schedules.py`

**命令设计**：

```bash
# 列出排程
castplay schedules list --device-id 1

# 创建排程
castplay schedules create \
    --device-id 1 \
    --playlist-id 2 \
    --start-time 08:00 \
    --end-time 18:00 \
    --weekdays 1,2,3,4,5  # 周一到周五

# 更新排程
castplay schedules update 1 --start-time 09:00

# 删除排程
castplay schedules delete 1

# 查看当前激活的排程
castplay schedules active --device-id 1
```

**参数说明**：
- `--weekdays`: 0=周一, 1=周二, ..., 6=周日
- `--start-time/--end-time`: 24小时制，格式 HH:MM

---

### 3.5 CLI 增强：playlists items 子命令

**文件路径**：`cli/commands/playlists.py` (增强)

**命令设计**：

```bash
# 列出播放列表项
castplay playlists items 1

# 添加媒体到播放列表
castplay playlists add-item 1 --media-id 5 --duration 10

# 批量添加
castplay playlists add-items 1 --media-ids 5,6,7 --duration 10

# 移除媒体项
castplay playlists remove-item 1 3

# 重新排序
castplay playlists reorder 1 --order 3,1,2,4
```

---

### 3.6 Skills 设计

#### `/device-control` Skill

**触发场景**：用户说"控制设备"、"暂停播放"、"切换播放列表"

**工作流程**：
1. 调用 `list_devices` 获取可用设备
2. 展示设备列表让用户选择
3. 根据用户意图调用相应控制命令
4. 返回执行结果

**示例对话**：
```
用户: 帮我暂停大厅的显示屏
Claude: [调用 list_devices 过滤名称含"大厅"]
        找到设备"大厅显示屏"(ID: 3)，当前正在播放。
        确认要暂停吗？
用户: 确认
Claude: [调用 pause_playback(3)]
        已暂停大厅显示屏的播放。
```

#### `/deploy-content` Skill

**触发场景**：用户说"部署内容"、"发布到设备"

**工作流程**：
1. 选择目标设备
2. 选择或创建播放列表
3. 选择/上传媒体
4. 分配播放列表到设备
5. 通知设备刷新

#### `/ppt-to-signage` Skill

**触发场景**：用户说"把 PPT 部署到屏幕"

**工作流程**：
1. 调用 `ppt-converter` MCP 转换 PPT 为视频
2. 调用 `playlist-manager` MCP 创建播放列表
3. 调用 `device-control` MCP 分配到设备
4. 返回部署结果

---

## 四、实现优先级

**用户选择**: Device Management MCP + Playlist Management MCP + CLI schedules + 全部按计划实现

**实现风格**: 独立 HTTP 调用（每个工具直接调用 REST API）

### Phase 1: 核心 MCP Servers (高优先级)

| 任务 | 预计工时 | 文件路径 |
|------|----------|----------|
| Device Management MCP | 4h | `mcp/device-control/server.py` |
| Playlist Management MCP | 3h | `mcp/playlist-manager/server.py` |
| CLI `schedules` 命令组 | 2h | `cli/commands/schedules.py` |

### Phase 2: CLI 增强 (中优先级)

| 任务 | 预计工时 | 文件路径 |
|------|----------|----------|
| CLI `playlists items` 子命令 | 1h | `cli/commands/playlists.py` (增强) |
| CLI `media upload` 命令 | 1h | `cli/commands/media.py` (增强) |
| CLI `server` 命令组 | 1h | `cli/commands/server.py` |

### Phase 3: Schedule MCP & Skills (后续)

| 任务 | 预计工时 | 文件路径 |
|------|----------|----------|
| Schedule Management MCP | 2h | `mcp/schedule-manager/server.py` |
| `/device-control` Skill | 2h | `.claude/skills/device-control/` |
| `/deploy-content` Skill | 2h | `.claude/skills/deploy-content/` |
| `/ppt-to-signage` Skill | 2h | `.claude/skills/ppt-to-signage/` |

---

## 五、MCP 实现风格

采用**独立 HTTP 调用**方式：

```python
# mcp/device-control/server.py 示例

import httpx
from mcp.server import Server

BASE_URL = "http://localhost:8000/api"

async def list_devices(online_only: bool = False) -> list[dict]:
    """获取设备列表"""
    async with httpx.AsyncClient() as client:
        params = {"online_only": online_only} if online_only else {}
        resp = await client.get(f"{BASE_URL}/devices", params=params, headers=get_auth_header())
        resp.raise_for_status()
        return resp.json()

async def pause_playback(device_id: int) -> dict:
    """暂停设备播放"""
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{BASE_URL}/control/{device_id}/pause", headers=get_auth_header())
        resp.raise_for_status()
        return resp.json()
```

**优点**：
- 简单直接，易于调试
- 与 CLI 保持一致的风格
- 无需共享状态

**认证处理**：
- 从 `~/.castplay/config.json` 读取 token
- 请求头添加 `Authorization: Bearer {token}`

---

## 六、验证方案

### 6.1 MCP Server 测试

```bash
# 1. 启动 MCP server
cd mcp/device-control && python server.py

# 2. 使用 MCP Inspector 测试
npx @anthropic-ai/mcp-inspector

# 3. 验证工具调用
- list_devices 应返回设备列表
- pause_playback 应触发设备暂停
```

### 6.2 CLI 测试

```bash
# 1. 测试 schedules 命令
castplay schedules list --device-id 1
castplay schedules create --device-id 1 --playlist-id 1 --start-time 08:00 --end-time 18:00 --weekdays 1,2,3,4,5

# 2. 测试 playlists items 命令
castplay playlists items 1
castplay playlists add-item 1 --media-id 1 --duration 10
```

### 6.3 Skills 测试

通过 Claude Code 交互测试各 Skills 的工作流。

---

## 七、关键文件路径

| 类别 | 路径 |
|------|------|
| **现有 MCP** | `mcp/ppt-converter/`, `mcp/android-tools/`, `mcp/file-processor/` |
| **新增 MCP** | `mcp/device-control/`, `mcp/playlist-manager/`, `mcp/schedule-manager/` |
| **CLI 命令** | `cli/commands/` |
| **Backend API** | `app/api/control.py`, `app/api/playlists.py`, `app/api/schedules.py` |
| **Services** | `app/services/notification.py`, `app/scheduler.py` |
| **WebSocket** | `app/websocket/handler.py` |
