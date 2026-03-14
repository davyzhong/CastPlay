# CastPlay MCP 服务器配置示例

将以下配置添加到 Claude Code 的设置文件中：

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

## 完整配置

```json
{
  "mcpServers": {
    "ppt-converter": {
      "command": "python",
      "args": ["/Users/Davy/PycharmProjects/CastPlay/mcp/ppt-converter/ppt_converter_server.py"],
      "env": {}
    },
    "android-tools": {
      "command": "python",
      "args": ["/Users/Davy/PycharmProjects/CastPlay/mcp/android-tools/android_tools_server.py"],
      "env": {
        "ANDROID_SDK": "/opt/homebrew/share/android-commandlinetools"
      }
    }
  }
}
```

## 按需启用

### 只启用 PPT 转换

```json
{
  "mcpServers": {
    "ppt-converter": {
      "command": "python",
      "args": ["/Users/Davy/PycharmProjects/CastPlay/mcp/ppt-converter/ppt_converter_server.py"]
    }
  }
}
```

### 只启用 Android 工具

```json
{
  "mcpServers": {
    "android-tools": {
      "command": "python",
      "args": ["/Users/Davy/PycharmProjects/CastPlay/mcp/android-tools/android_tools_server.py"],
      "env": {
        "ANDROID_SDK": "/opt/homebrew/share/android-commandlinetools"
      }
    }
  }
}
```

## 可用工具

### PPT Converter MCP

| 工具 | 描述 |
|------|------|
| `get_ppt_info` | 获取 PPT 文件信息 |
| `ppt_to_pdf` | PPT 转 PDF |
| `ppt_to_images` | PPT 转图片序列 |
| `ppt_to_video` | PPT 转视频 |
| `check_tools` | 检查依赖工具 |

### Android Tools MCP

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

## 依赖安装

```bash
# PPT Converter 依赖
# - LibreOffice: https://www.libreoffice.org/
# - poppler-utils: brew install poppler
# - ffmpeg: brew install ffmpeg

# Android Tools 依赖
# - Android SDK: https://developer.android.com/studio
```

## Python 依赖

```bash
pip install mcp loguru
```
