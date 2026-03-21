# CastPlay MCP Servers / CastPlay MCP 服务器

[English](#english) | [中文](#中文)

---

<a name="english"></a>
## English

Add the following configuration to your Claude Code settings file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### Full Configuration

```json
{
  "mcpServers": {
    "ppt-converter": {
      "command": "python",
      "args": ["/path/to/CastPlay/mcp/ppt-converter/ppt_converter_server.py"],
      "env": {}
    },
    "android-tools": {
      "command": "python",
      "args": ["/path/to/CastPlay/mcp/android-tools/android_tools_server.py"],
      "env": {
        "ANDROID_SDK": "/path/to/android-sdk"
      }
    },
    "device-control": {
      "command": "python",
      "args": ["/path/to/CastPlay/mcp/device-control/device_control_server.py"],
      "env": {}
    },
    "playlist-manager": {
      "command": "python",
      "args": ["/path/to/CastPlay/mcp/playlist-manager/playlist_manager_server.py"],
      "env": {}
    },
    "schedule-manager": {
      "command": "python",
      "args": ["/path/to/CastPlay/mcp/schedule-manager/schedule_manager_server.py"],
      "env": {}
    },
    "file-processor": {
      "command": "python",
      "args": ["/path/to/CastPlay/mcp/file-processor/file_processor_server.py"],
      "env": {}
    }
  }
}
```

### Available Tools

#### PPT Converter MCP

| Tool | Description |
|------|-------------|
| `get_ppt_info` | Get PPT file information |
| `ppt_to_pdf` | Convert PPT to PDF |
| `ppt_to_images` | Convert PPT to image sequence |
| `ppt_to_video` | Convert PPT to video |
| `check_tools` | Check dependency tools |

#### Android Tools MCP

| Tool | Description |
|------|-------------|
| `check_android_environment` | Check Android SDK environment |
| `list_avds` | List available AVDs |
| `list_devices` | List connected devices |
| `start_emulator` | Start emulator |
| `stop_emulator` | Stop emulator |
| `build_apk` | Build APK |
| `install_apk` | Install APK |
| `take_screenshot` | Take screenshot |
| `get_device_logs` | Get device logs |
| `launch_app` | Launch app |
| `stop_app` | Stop app |

#### Device Control MCP

| Tool | Description |
|------|-------------|
| `list_devices` | List all devices |
| `get_device` | Get device details |
| `pause_playback` | Pause playback |
| `resume_playback` | Resume playback |
| `set_volume` | Set volume (0-100) |
| `switch_playlist` | Switch playlist |

#### Playlist Manager MCP

| Tool | Description |
|------|-------------|
| `list_playlists` | List all playlists |
| `get_playlist` | Get playlist details |
| `create_playlist` | Create playlist |
| `delete_playlist` | Delete playlist |
| `add_media_to_playlist` | Add media to playlist |

#### Schedule Manager MCP

| Tool | Description |
|------|-------------|
| `list_schedules` | List schedules for device |
| `create_schedule` | Create schedule |
| `update_schedule` | Update schedule |
| `delete_schedule` | Delete schedule |
| `get_active_schedule` | Get active schedule |

#### File Processor MCP

| Tool | Description |
|------|-------------|
| `get_video_info` | Get video file information |
| `extract_video_thumbnail` | Extract thumbnail from video |
| `compress_video` | Compress video file |
| `generate_video_preview` | Generate preview grid |

### Dependencies

```bash
# PPT Converter dependencies
# - LibreOffice: https://www.libreoffice.org/
# - poppler-utils: brew install poppler
# - ffmpeg: brew install ffmpeg

# Android Tools dependencies
# - Android SDK: https://developer.android.com/studio
```

### Python Dependencies

```bash
pip install mcp loguru httpx pydantic
```

---

<a name="中文"></a>
## 中文

将以下配置添加到 Claude Code 的设置文件中：

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### 完整配置

```json
{
  "mcpServers": {
    "ppt-converter": {
      "command": "python",
      "args": ["/path/to/CastPlay/mcp/ppt-converter/ppt_converter_server.py"],
      "env": {}
    },
    "android-tools": {
      "command": "python",
      "args": ["/path/to/CastPlay/mcp/android-tools/android_tools_server.py"],
      "env": {
        "ANDROID_SDK": "/path/to/android-sdk"
      }
    },
    "device-control": {
      "command": "python",
      "args": ["/path/to/CastPlay/mcp/device-control/device_control_server.py"],
      "env": {}
    },
    "playlist-manager": {
      "command": "python",
      "args": ["/path/to/CastPlay/mcp/playlist-manager/playlist_manager_server.py"],
      "env": {}
    },
    "schedule-manager": {
      "command": "python",
      "args": ["/path/to/CastPlay/mcp/schedule-manager/schedule_manager_server.py"],
      "env": {}
    },
    "file-processor": {
      "command": "python",
      "args": ["/path/to/CastPlay/mcp/file-processor/file_processor_server.py"],
      "env": {}
    }
  }
}
```

### 按需启用

#### 只启用 PPT 转换

```json
{
  "mcpServers": {
    "ppt-converter": {
      "command": "python",
      "args": ["/path/to/CastPlay/mcp/ppt-converter/ppt_converter_server.py"]
    }
  }
}
```

#### 只启用 Android 工具

```json
{
  "mcpServers": {
    "android-tools": {
      "command": "python",
      "args": ["/path/to/CastPlay/mcp/android-tools/android_tools_server.py"],
      "env": {
        "ANDROID_SDK": "/path/to/android-sdk"
      }
    }
  }
}
```

### 可用工具

#### PPT Converter MCP

| 工具 | 描述 |
|------|------|
| `get_ppt_info` | 获取 PPT 文件信息 |
| `ppt_to_pdf` | PPT 转 PDF |
| `ppt_to_images` | PPT 转图片序列 |
| `ppt_to_video` | PPT 转视频 |
| `check_tools` | 检查依赖工具 |

#### Android Tools MCP

| 工具 | 描述 |
|------|------|
| `check_android_environment` | 检查 Android SDK 环境 |
| `list_avds` | 列出可用 AVD |
| `list_devices` | 列出已连接设备 |
| `start_emulator` | 启动模拟器 |
| `stop_emulator` | 停止模拟器 |
| `build_apk` | 构建 APK |
| `install_apk` | 安装 APK |
| `take_screenshot` | 截图 |
| `get_device_logs` | 获取设备日志 |
| `launch_app` | 启动应用 |
| `stop_app` | 停止应用 |

#### Device Control MCP

| 工具 | 描述 |
|------|------|
| `list_devices` | 列出所有设备 |
| `get_device` | 获取设备详情 |
| `pause_playback` | 暂停播放 |
| `resume_playback` | 恢复播放 |
| `set_volume` | 设置音量 (0-100) |
| `switch_playlist` | 切换播放列表 |

#### Playlist Manager MCP

| 工具 | 描述 |
|------|------|
| `list_playlists` | 列出所有播放列表 |
| `get_playlist` | 获取播放列表详情 |
| `create_playlist` | 创建播放列表 |
| `delete_playlist` | 删除播放列表 |
| `add_media_to_playlist` | 添加媒体到播放列表 |

#### Schedule Manager MCP

| 工具 | 描述 |
|------|------|
| `list_schedules` | 列出排程 |
| `create_schedule` | 创建排程 |
| `update_schedule` | 更新排程 |
| `delete_schedule` | 删除排程 |
| `get_active_schedule` | 获取激活的排程 |

#### File Processor MCP

| 工具 | 描述 |
|------|------|
| `get_video_info` | 获取视频文件信息 |
| `extract_video_thumbnail` | 提取视频缩略图 |
| `compress_video` | 压缩视频文件 |
| `generate_video_preview` | 生成预览图 |

### 依赖安装

```bash
# PPT Converter 依赖
# - LibreOffice: https://www.libreoffice.org/
# - poppler-utils: brew install poppler
# - ffmpeg: brew install ffmpeg

# Android Tools 依赖
# - Android SDK: https://developer.android.com/studio
```

### Python 依赖

```bash
pip install mcp loguru httpx pydantic
```
