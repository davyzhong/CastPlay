# CastPlay 项目 MCP/Skill 适配分析

## Context

分析 CastPlay 项目的哪些功能和环节最适合改为 MCP（Model Context Protocol）和 Skill。

**分析原则**：只推荐最合适的场景，不强行改造不适合的部分。

---

## 分析结论总览

| 类型 | 推荐项 | 适配度 | 状态 |
|------|--------|--------|------|
| **MCP** | PPT 转换服务 | ★★★★★ | ✅ 已实现 |
| **MCP** | Android 构建/调试 | ★★★★★ | ✅ 已实现 |
| **MCP** | 文件处理服务 | ★★★★ | ✅ 已实现 |
| **Skill** | android-test | ★★★★★ | ✅ 已完成 |
| **Skill** | web-test | ★★★★ | ✅ 已实现 |
| **Skill** | build-android | ★★★★ | ✅ 已实现 |
| **Skill** | test-push | ★★★ | ✅ 已实现 |
| **Skill** | db-maintenance | ★★★ | ✅ 已实现 |
| **Skill** | quality-check | ★★★ | ✅ 已实现 |

---

## 一、适合改为 MCP 的功能

### 1. PPT 转换服务 ★★★★★

**文件**: `app/services/ppt_converter.py`

**适配理由**:
- 独立的外部服务调用（LibreOffice + pdf2image）
- 有明确的输入输出（PPT → 图片）
- 可被多个项目复用
- 需要特定环境（LibreOffice、poppler）
- 错误处理复杂，适合封装

**MCP 工具设计**:
```python
# tools
- ppt_to_images(ppt_file_path, output_dir, dpi) -> List[image_paths]
- ppt_to_pdf(ppt_file_path, output_path) -> pdf_path
- get_ppt_info(ppt_file_path) -> {page_count, file_size, ...}
```

**收益**:
- 解耦 PPT 处理逻辑
- 可独立部署和扩展
- 便于测试和维护

---

### 2. Android 构建/调试服务 ★★★★★

**文件**: `scripts/testing/android-test.sh`, `android/` 目录

**适配理由**:
- 需要特定环境（Android SDK、Gradle、模拟器）
- 命令行工具链复杂（adb、emulator、gradlew）
- 操作步骤固定但繁琐
- 可被其他 Android 项目复用

**MCP 工具设计**:
```python
# tools
- android_build_apk(project_path, build_type) -> apk_path
- android_start_emulator(avd_name) -> device_id
- android_install_apk(device_id, apk_path) -> success
- android_take_screenshot(device_id) -> image_path
- android_get_logs(device_id, filter) -> logs
- android_run_tests(device_id) -> test_results
```

**收益**:
- 标准化 Android 测试流程
- 跨项目复用
- 简化 CI/CD 集成

---

### 3. 文件处理服务 ★★★★

**文件**: `app/services/file_processor.py`, `app/services/video_processor.py`

**适配理由**:
- 媒体文件处理需要 FFmpeg 等外部工具
- 操作类型固定（缩略图、转码、压缩）
- 处理逻辑可抽象

**MCP 工具设计**:
```python
# tools
- extract_video_thumbnail(video_path, time_offset) -> image_path
- get_video_info(video_path) -> {duration, resolution, codec, ...}
- compress_video(video_path, quality) -> compressed_path
- generate_video_preview(video_path, options) -> preview_path
```

**收益**:
- 统一媒体处理接口
- 便于替换底层实现

---

### 4. WebSocket 通知服务 ★★★

**文件**: `app/services/notification.py`, `app/services/connection_manager.py`

**适配理由**:
- 实时推送能力可独立服务化
- 支持多客户端类型
- 连接管理逻辑可复用

**MCP 资源设计**:
```python
# resources
- ws://server/notifications -> real-time notification stream

# tools
- send_notification(device_id, message) -> success
- broadcast_notification(channel, message) -> success
```

**注意**: 这个改动较大，需要评估是否值得

---

## 二、适合改为 Skill 的功能

### 1. android-test ✅ 已完成

**文件**: `scripts/testing/android-test.sh`

**Skill 路径**: `~/.claude/skills/android-test/SKILL.md`

**已实现功能**:
- 依赖检查 → 前端构建 → APK 构建 → 模拟器启动 → 安装 → 测试
- 支持 --skip-build、--skip-emulator、--auto-close 参数

---

### 2. web-test ★★★★

**文件**: `scripts/testing/` (待创建)

**Skill 用途**:
- 启动 Web 播放端测试环境
- 自动打开 player.html 并监控日志
- 验证 WebSocket 连接和播放列表切换

**Skill 触发词**:
- "启动 Web 端测试"
- "测试 Web 播放端"
- "测试 player.html"

**Skill 内容**:
```markdown
---
name: web-test
description: CastPlay Web 播放端测试技能。用于启动 Web 播放端并验证功能。
---

## 测试流程
1. 启动前端开发服务器 (npm run dev)
2. 打开 player.html 页面
3. 监控控制台日志
4. 验证 WebSocket 连接
5. 测试播放列表自动切换
```

---

### 3. build-android ★★★★

**文件**: `android/` 目录

**Skill 用途**:
- 快速构建 Android APK
- 支持 Debug/Release 配置
- 自动处理前端资源复制

**Skill 触发词**:
- "构建 Android APK"
- "编译 Android 应用"
- "打包 Android"

---

### 4. db-maintenance ★★★

**文件**: `scripts/db/` 目录

**Skill 用途**:
- 数据库备份和恢复
- 清理过期数据
- 数据迁移

**Skill 触发词**:
- "备份数据库"
- "清理数据库"
- "数据库维护"

---

### 5. test-push ★★★

**文件**: WebSocket 推送测试

**Skill 用途**:
- 测试 WebSocket 消息推送
- 模拟各种推送场景
- 验证客户端响应

**Skill 触发词**:
- "测试推送"
- "测试 WebSocket 推送"
- "模拟消息推送"

---

### 6. quality-check ★★★

**Skill 用途**:
- 运行 ESLint、TypeScript 检查
- 运行 Python 代码检查（ruff、mypy）
- 生成代码质量报告

**Skill 触发词**:
- "代码检查"
- "运行 lint"
- "质量检查"

---

## 三、不适合改为 MCP/Skill 的功能

### 1. 简单 CRUD 操作 ❌

**原因**:
- 后端 API 已经足够简洁
- Claude Code 可以直接调用 API
- 封装反而增加复杂度

**示例**:
- 设备管理 API (`/api/devices/`)
- 播放列表管理 API (`/api/playlists/`)
- 媒体管理 API (`/api/media/`)

---

### 2. 简单配置读取 ❌

**原因**:
- 配置文件直接读取更简单
- 不需要额外抽象

**示例**:
- `app/config.py`
- `frontend/vite.config.ts`

---

### 3. 一次性脚本 ❌

**原因**:
- 使用频率低
- 不需要工作流自动化

**示例**:
- 数据迁移脚本
- 初始化脚本

---

### 4. 前端组件/页面 ❌

**原因**:
- 前端代码不适合 MCP/Skill
- 需要在浏览器环境中运行

**示例**:
- React 组件
- 页面模板
- 样式文件

---

## 四、优先级推荐

### 高优先级（立即实施）

1. **PPT 转换 MCP** - 核心业务功能，使用频繁
2. **Android 构建 MCP** - 环境复杂，复用价值高

### 中优先级（近期实施）

3. **web-test Skill** - 配合 android-test 形成完整测试体系
4. **文件处理 MCP** - 提升媒体处理能力

### 低优先级（按需实施）

5. **db-maintenance Skill** - 维护需求较少
6. **quality-check Skill** - 可用现有工具替代

---

## 五、实施路线图

```
Phase 1: MCP 基础设施 ✅ 已完成
├── 创建 MCP 项目结构
├── PPT 转换服务 MCP
└── Android 构建 MCP

Phase 2: Skill 扩展 ✅ 已完成
├── web-test Skill
├── build-android Skill
└── test-push Skill

Phase 3: 高级功能 ✅ 已完成
├── 文件处理 MCP
├── db-maintenance Skill
└── quality-check Skill
```

---

## 六、技术实现建议

### MCP 开发框架

推荐使用 **FastMCP** (Python):

```python
from mcp.server import FastMCP

mcp = FastMCP("castplay-tools")

@mcp.tool()
def ppt_to_images(ppt_path: str, output_dir: str) -> list[str]:
    """Convert PPT to images"""
    # ... implementation
    return image_paths
```

### Skill 目录结构

```
~/.claude/skills/
├── android-test/
│   ├── SKILL.md
│   └── evals/
│       └── evals.json
├── web-test/
│   └── SKILL.md
└── build-android/
    └── SKILL.md
```
