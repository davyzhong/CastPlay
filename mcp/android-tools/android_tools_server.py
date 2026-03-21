"""
Android Tools MCP Server

Provides MCP tools for Android APK building and device management.
"""
import os
import sys
import subprocess
import re
import shutil
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from mcp.server import FastMCP
from loguru import logger

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")

mcp = FastMCP("castplay-android-tools")


class AndroidTools:
    """Android SDK and build utilities"""

    def __init__(self, sdk_path: Optional[str] = None):
        self.sdk_path = sdk_path or os.environ.get(
            "ANDROID_SDK",
            "/opt/homebrew/share/android-commandlinetools"
        )
        self._setup_paths()

    def _setup_paths(self):
        """Setup Android SDK environment paths"""
        os.environ["ANDROID_HOME"] = self.sdk_path
        os.environ["ANDROID_SDK_ROOT"] = self.sdk_path

    @property
    def emulator_path(self) -> str:
        return os.path.join(self.sdk_path, "emulator", "emulator", "emulator")

    @property
    def adb_path(self) -> str:
        return os.path.join(self.sdk_path, "platform-tools", "adb")

    def check_tool(self, tool_path: str, tool_name: str) -> dict:
        """Check if a tool exists and is executable"""
        if os.path.exists(tool_path):
            return {"available": True, "path": tool_path}
        return {"available": False, "path": tool_path, "error": f"{tool_name} not found"}

    def run_command(self, cmd: List[str], timeout: int = 300, cwd: Optional[str] = None) -> dict:
        """Run a shell command and return result"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd
            )
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}


android_tools = AndroidTools()


@mcp.tool()
def check_android_environment() -> dict:
    """
    Check if Android SDK and required tools are properly configured.

    Returns:
        Dictionary with environment status and available tools
    """
    tools = {
        "adb": android_tools.check_tool(android_tools.adb_path, "adb"),
        "emulator": android_tools.check_tool(android_tools.emulator_path, "emulator"),
    }

    # Check gradlew
    gradlew_exists = shutil.which("gradlew") is not None or os.path.exists("./gradlew")

    issues = []
    for name, info in tools.items():
        if not info["available"]:
            issues.append(f"{name} not found at {info['path']}")
    if not gradlew_exists:
        issues.append("gradlew not found in PATH or current directory")

    return {
        "success": len(issues) == 0,
        "sdk_path": android_tools.sdk_path,
        "tools": tools,
        "gradlew_available": gradlew_exists,
        "issues": issues if issues else None,
        "message": "Android environment ready" if not issues else "; ".join(issues)
    }


@mcp.tool()
def list_avds() -> dict:
    """
    List available Android Virtual Devices (AVDs).

    Returns:
        Dictionary with list of AVD names
    """
    if not os.path.exists(android_tools.emulator_path):
        return {
            "success": False,
            "error": "Emulator not found. Check Android SDK installation."
        }

    result = android_tools.run_command(
        [android_tools.emulator_path, "-list-avds"],
        timeout=30
    )

    if result["success"]:
        avds = [line for line in result["stdout"].strip().split("\n") if line]
        return {
            "success": True,
            "avds": avds,
            "count": len(avds)
        }

    return {
        "success": False,
        "error": result.get("stderr", "Failed to list AVDs")
    }


@mcp.tool()
def list_devices() -> dict:
    """
    List connected Android devices and emulators.

    Returns:
        Dictionary with list of connected devices
    """
    if not os.path.exists(android_tools.adb_path):
        return {
            "success": False,
            "error": "ADB not found. Check Android SDK installation."
        }

    result = android_tools.run_command(
        [android_tools.adb_path, "devices", "-l"],
        timeout=10
    )

    if result["success"]:
        devices = []
        lines = result["stdout"].strip().split("\n")
        for line in lines[1:]:  # Skip header
            if line.strip():
                parts = line.split()
                if len(parts) >= 2:
                    device_id = parts[0]
                    status = parts[1]
                    device_info = {"id": device_id, "status": status}
                    # Parse additional info
                    for part in parts[2:]:
                        if ":" in part:
                            key, value = part.split(":", 1)
                            device_info[key] = value
                    devices.append(device_info)

        return {
            "success": True,
            "devices": devices,
            "count": len(devices)
        }

    return {
        "success": False,
        "error": result.get("stderr", "Failed to list devices")
    }


@mcp.tool()
def start_emulator(
    avd_name: str,
    wait_for_boot: bool = True,
    no_snapshot: bool = True,
    headless: bool = False
) -> dict:
    """
    Start an Android emulator with the specified AVD.

    Args:
        avd_name: Name of the AVD to start
        wait_for_boot: Wait for emulator to fully boot (default: true)
        no_snapshot: Start with clean state (default: true)
        headless: Run in headless mode without GUI (default: false)

    Returns:
        Dictionary with emulator status and device ID
    """
    # Check if AVD exists
    avds_result = list_avds()
    if not avds_result["success"]:
        return avds_result

    if avd_name not in avds_result["avds"]:
        return {
            "success": False,
            "error": f"AVD '{avd_name}' not found. Available: {avds_result['avds']}"
        }

    # Check if device already running
    devices_result = list_devices()
    if devices_result["success"]:
        for device in devices_result["devices"]:
            if "emulator" in device["id"]:
                return {
                    "success": True,
                    "message": f"Emulator already running: {device['id']}",
                    "device_id": device["id"],
                    "already_running": True
                }

    # Build emulator command
    cmd = [android_tools.emulator_path, "-avd", avd_name]
    if no_snapshot:
        cmd.append("-no-snapshot-load")
    if headless:
        cmd.extend(["-no-window", "-no-audio", "-gpu", "swiftshader_indirect"])

    try:
        # Start emulator in background
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        if not wait_for_boot:
            return {
                "success": True,
                "message": f"Emulator starting in background (PID: {process.pid})",
                "pid": process.pid,
                "avd": avd_name
            }

        # Wait for device to appear
        result = android_tools.run_command(
            [android_tools.adb_path, "wait-for-device"],
            timeout=120
        )

        # Wait for boot complete
        boot_complete = False
        for _ in range(60):
            check_result = android_tools.run_command(
                [android_tools.adb_path, "shell", "getprop", "sys.boot_completed"],
                timeout=5
            )
            if check_result["success"] and "1" in check_result["stdout"]:
                boot_complete = True
                break

        if boot_complete:
            # Get device ID
            devices_result = list_devices()
            device_id = None
            if devices_result["success"]:
                for device in devices_result["devices"]:
                    if "emulator" in device["id"]:
                        device_id = device["id"]
                        break

            return {
                "success": True,
                "message": f"Emulator started successfully",
                "device_id": device_id,
                "avd": avd_name,
                "pid": process.pid
            }
        else:
            return {
                "success": False,
                "error": "Emulator started but boot did not complete in time"
            }

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def stop_emulator(device_id: Optional[str] = None) -> dict:
    """
    Stop an Android emulator.

    Args:
        device_id: Device ID to stop (optional, stops all emulators if not specified)

    Returns:
        Dictionary with operation result
    """
    if not os.path.exists(android_tools.adb_path):
        return {"success": False, "error": "ADB not found"}

    if device_id:
        result = android_tools.run_command(
            [android_tools.adb_path, "-s", device_id, "emu", "kill"],
            timeout=10
        )
    else:
        # Kill all emulators
        devices_result = list_devices()
        if not devices_result["success"]:
            return devices_result

        stopped = []
        for device in devices_result["devices"]:
            if "emulator" in device["id"]:
                result = android_tools.run_command(
                    [android_tools.adb_path, "-s", device["id"], "emu", "kill"],
                    timeout=10
                )
                if result["success"]:
                    stopped.append(device["id"])

        return {
            "success": True,
            "message": f"Stopped {len(stopped)} emulator(s)",
            "stopped_devices": stopped
        }

    return {
        "success": result["success"],
        "message": "Emulator stopped" if result["success"] else result.get("stderr", "Failed to stop emulator")
    }


@mcp.tool()
def build_apk(
    project_path: str,
    build_type: str = "debug",
    clean_first: bool = False
) -> dict:
    """
    Build an Android APK from a project.

    Args:
        project_path: Path to the Android project root (contains app/ and gradlew)
        build_type: Build type - debug or release (default: debug)
        clean_first: Run clean before build (default: false)

    Returns:
        Dictionary with build result and APK path
    """
    project_dir = Path(project_path)
    if not project_dir.exists():
        return {"success": False, "error": f"Project directory not found: {project_path}"}

    # Find gradlew
    gradlew = project_dir / "gradlew"
    if not gradlew.exists():
        # Try gradle wrapper on Windows
        gradlew_bat = project_dir / "gradlew.bat"
        if gradlew_bat.exists():
            gradlew = gradlew_bat
        else:
            return {"success": False, "error": "gradlew not found in project directory"}

    # Make gradlew executable
    os.chmod(str(gradlew), 0o755)

    try:
        # Clean if requested
        if clean_first:
            clean_result = android_tools.run_command(
                [str(gradlew), "clean"],
                timeout=120,
                cwd=str(project_dir)
            )
            if not clean_result["success"]:
                return {
                    "success": False,
                    "error": f"Clean failed: {clean_result.get('stderr', 'Unknown error')}"
                }

        # Build APK
        task = "assembleDebug" if build_type.lower() == "debug" else "assembleRelease"
        build_result = android_tools.run_command(
            [str(gradlew), task],
            timeout=600,  # 10 minutes for build
            cwd=str(project_dir)
        )

        if not build_result["success"]:
            return {
                "success": False,
                "error": f"Build failed: {build_result.get('stderr', 'Unknown error')}",
                "stdout": build_result.get("stdout")
            }

        # Find APK
        apk_pattern = "**/build/outputs/apk/**/*.apk"
        apks = list(project_dir.glob(apk_pattern))

        if not apks:
            return {
                "success": False,
                "error": "Build succeeded but APK not found"
            }

        # Filter by build type
        build_type_lower = build_type.lower()
        matching_apks = [apk for apk in apks if build_type_lower in str(apk).lower()]

        apk_path = matching_apks[0] if matching_apks else apks[0]
        apk_size = apk_path.stat().st_size

        return {
            "success": True,
            "apk_path": str(apk_path.absolute()),
            "file_size_bytes": apk_size,
            "file_size_mb": round(apk_size / (1024 * 1024), 2),
            "build_type": build_type,
            "message": f"APK built successfully: {apk_path.name}"
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def install_apk(
    apk_path: str,
    device_id: Optional[str] = None,
    reinstall: bool = True
) -> dict:
    """
    Install an APK on a connected device.

    Args:
        apk_path: Path to the APK file
        device_id: Target device ID (optional, uses first available device)
        reinstall: Reinstall if app exists (default: true)

    Returns:
        Dictionary with installation result
    """
    apk = Path(apk_path)
    if not apk.exists():
        return {"success": False, "error": f"APK not found: {apk_path}"}

    if not os.path.exists(android_tools.adb_path):
        return {"success": False, "error": "ADB not found"}

    # Build command
    cmd = [android_tools.adb_path]
    if device_id:
        cmd.extend(["-s", device_id])

    # Uninstall first if reinstalling
    if reinstall:
        # Try to get package name from APK
        dump_result = android_tools.run_command(
            cmd + ["shell", "pm", "list", "packages", "-3"],
            timeout=30
        )

    cmd.extend(["install"])
    if reinstall:
        cmd.append("-r")  # Reinstall flag
    cmd.append(str(apk.absolute()))

    result = android_tools.run_command(cmd, timeout=120)

    if result["success"] and "Success" in result["stdout"]:
        return {
            "success": True,
            "message": "APK installed successfully",
            "apk_path": str(apk.absolute()),
            "device_id": device_id
        }

    return {
        "success": False,
        "error": result.get("stderr", "Installation failed"),
        "stdout": result.get("stdout")
    }


@mcp.tool()
def take_screenshot(
    output_path: Optional[str] = None,
    device_id: Optional[str] = None
) -> dict:
    """
    Take a screenshot from a connected device.

    Args:
        output_path: Path to save screenshot (optional, defaults to timestamp)
        device_id: Device ID (optional)

    Returns:
        Dictionary with screenshot path
    """
    if not os.path.exists(android_tools.adb_path):
        return {"success": False, "error": "ADB not found"}

    # Generate output path if not provided
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"screenshot_{timestamp}.png"

    # Build command
    cmd = [android_tools.adb_path]
    if device_id:
        cmd.extend(["-s", device_id])
    cmd.extend(["exec-out", "screencap", "-p"])

    try:
        with open(output_path, "wb") as f:
            result = subprocess.run(
                cmd,
                stdout=f,
                stderr=subprocess.PIPE,
                timeout=30
            )

        if result.returncode == 0 and os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            return {
                "success": True,
                "screenshot_path": os.path.abspath(output_path),
                "file_size_bytes": file_size
            }

        return {
            "success": False,
            "error": result.stderr.decode() if result.stderr else "Screenshot failed"
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_device_logs(
    device_id: Optional[str] = None,
    filter_tags: Optional[List[str]] = None,
    lines: int = 100
) -> dict:
    """
    Get logcat logs from a device.

    Args:
        device_id: Device ID (optional)
        filter_tags: List of tags to filter (e.g., ["MainActivity", "chromium"])
        lines: Number of recent lines to retrieve (default: 100)

    Returns:
        Dictionary with log content
    """
    if not os.path.exists(android_tools.adb_path):
        return {"success": False, "error": "ADB not found"}

    cmd = [android_tools.adb_path]
    if device_id:
        cmd.extend(["-s", device_id])
    cmd.extend(["logcat", "-d", "-t", str(lines)])

    # Add tag filters
    if filter_tags:
        tag_filter = " ".join(f"{tag}:*" for tag in filter_tags)
        cmd.extend(["-s", tag_filter])

    result = android_tools.run_command(cmd, timeout=30)

    if result["success"]:
        return {
            "success": True,
            "logs": result["stdout"],
            "lines": lines,
            "filter_tags": filter_tags
        }

    return {
        "success": False,
        "error": result.get("stderr", "Failed to get logs")
    }


@mcp.tool()
def launch_app(
    package_name: str,
    activity_name: str,
    device_id: Optional[str] = None
) -> dict:
    """
    Launch an app on a device.

    Args:
        package_name: App package name (e.g., com.example.app)
        activity_name: Main activity name (e.g., .MainActivity or full path)
        device_id: Device ID (optional)

    Returns:
        Dictionary with launch result
    """
    if not os.path.exists(android_tools.adb_path):
        return {"success": False, "error": "ADB not found"}

    # Build full activity name if needed
    if activity_name.startswith("."):
        full_activity = f"{package_name}/{activity_name}"
    else:
        full_activity = f"{package_name}/{activity_name}"

    cmd = [android_tools.adb_path]
    if device_id:
        cmd.extend(["-s", device_id])
    cmd.extend(["shell", "am", "start", "-n", full_activity])

    result = android_tools.run_command(cmd, timeout=30)

    if result["success"]:
        return {
            "success": True,
            "message": f"App launched: {full_activity}",
            "package": package_name,
            "activity": activity_name
        }

    return {
        "success": False,
        "error": result.get("stderr", "Failed to launch app")
    }


@mcp.tool()
def stop_app(
    package_name: str,
    device_id: Optional[str] = None
) -> dict:
    """
    Force stop an app on a device.

    Args:
        package_name: App package name
        device_id: Device ID (optional)

    Returns:
        Dictionary with result
    """
    if not os.path.exists(android_tools.adb_path):
        return {"success": False, "error": "ADB not found"}

    cmd = [android_tools.adb_path]
    if device_id:
        cmd.extend(["-s", device_id])
    cmd.extend(["shell", "am", "force-stop", package_name])

    result = android_tools.run_command(cmd, timeout=10)

    return {
        "success": result["success"],
        "message": f"App stopped: {package_name}" if result["success"] else result.get("stderr", "Failed to stop app")
    }


def main():
    """Run the MCP server"""
    mcp.run()


if __name__ == "__main__":
    main()
