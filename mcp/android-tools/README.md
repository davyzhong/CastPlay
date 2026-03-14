# CastPlay Android Tools MCP Server

MCP server providing Android build and debug tools for CastPlay.

## Features

- **check_android_environment**: Verify Android SDK setup
- **list_avds**: List available Android Virtual Devices
- **list_devices**: List connected devices and emulators
- **start_emulator**: Start an Android emulator
- **stop_emulator**: Stop an emulator
- **build_apk**: Build an APK from an Android project
- **install_apk**: Install APK on a device
- **take_screenshot**: Capture device screenshot
- **get_device_logs**: Retrieve logcat logs
- **launch_app**: Launch an app on device
- **stop_app**: Force stop an app

## Requirements

- Android SDK (ANDROID_SDK environment variable or default path)
- For APK builds: Gradle wrapper (gradlew) in project directory

## Installation

```bash
cd mcp/android-tools
pip install -e .
```

## Usage

### As MCP Server

Add to your Claude Code configuration:

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

### Environment Variables

- `ANDROID_SDK`: Path to Android SDK (default: `/opt/homebrew/share/android-commandlinetools`)

## Tools

### check_android_environment

Check if Android SDK and tools are properly configured.

```
check_android_environment() -> dict
```

### list_avds

List available Android Virtual Devices.

```
list_avds() -> dict
```

### list_devices

List connected Android devices and emulators.

```
list_devices() -> dict
```

### start_emulator

Start an Android emulator.

```
start_emulator(
    avd_name: str,
    wait_for_boot: bool = True,
    no_snapshot: bool = True,
    headless: bool = False
) -> dict
```

### stop_emulator

Stop an emulator.

```
stop_emulator(device_id: Optional[str] = None) -> dict
```

### build_apk

Build an Android APK.

```
build_apk(
    project_path: str,
    build_type: str = "debug",
    clean_first: bool = False
) -> dict
```

### install_apk

Install APK on device.

```
install_apk(
    apk_path: str,
    device_id: Optional[str] = None,
    reinstall: bool = True
) -> dict
```

### take_screenshot

Take a screenshot from device.

```
take_screenshot(
    output_path: Optional[str] = None,
    device_id: Optional[str] = None
) -> dict
```

### get_device_logs

Get logcat logs from device.

```
get_device_logs(
    device_id: Optional[str] = None,
    filter_tags: Optional[List[str]] = None,
    lines: int = 100
) -> dict
```

### launch_app

Launch an app on device.

```
launch_app(
    package_name: str,
    activity_name: str,
    device_id: Optional[str] = None
) -> dict
```

### stop_app

Force stop an app.

```
stop_app(
    package_name: str,
    device_id: Optional[str] = None
) -> dict
```

## Example Workflow

1. Check environment: `check_android_environment()`
2. List AVDs: `list_avds()`
3. Start emulator: `start_emulator("CastPlay_Test")`
4. Build APK: `build_apk("/path/to/android/project")`
5. Install APK: `install_apk("/path/to/app.apk")`
6. Launch app: `launch_app("com.castplay.player.debug", ".MainActivity")`
7. Take screenshot: `take_screenshot()`
8. Get logs: `get_device_logs(filter_tags=["MainActivity"])`
