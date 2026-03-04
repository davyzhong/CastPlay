#!/usr/bin/env python3
"""环境检查脚本"""
import subprocess
import os
import sys
import shutil


def run_cmd(cmd):
    """运行命令并返回输出"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout.strip() or result.stderr.strip() or "(empty)"
    except Exception as e:
        return f"Error: {e}"


print("=" * 60)
print("E2E 测试环境检查")
print("=" * 60)

# 1. 检查基础环境
print("\n[1] 基础环境")
print(f"  Python: {sys.version.split()[0]}")
print(f"  工作目录: {os.getcwd()}")

# 2. 检查 npm/appium
print("\n[2] Appium 环境")
npm_path = shutil.which("npm")
print(f"  npm: {npm_path or '未找到'}")
if npm_path:
    print(f"  npm version: {run_cmd('npm --version')}")

appium_path = shutil.which("appium")
print(f"  appium: {appium_path or '未找到'}")
if appium_path:
    print(f"  appium version: {run_cmd('appium --version')}")

# 3. 检查 Android SDK
print("\n[3] Android SDK")
android_home = os.environ.get(
    "ANDROID_HOME", "/Users/Davy/PycharmProjects/CastPlay/android-sdk")
print(f"  ANDROID_HOME: {android_home}")
adb_path = os.path.join(android_home, "platform-tools", "adb")
print(f"  adb exists: {os.path.exists(adb_path)}")
emulator_path = os.path.join(android_home, "emulator", "emulator")
print(f"  emulator exists: {os.path.exists(emulator_path)}")

# 4. 检查模拟器状态
print("\n[4] 模拟器状态")
if os.path.exists(adb_path):
    devices = run_cmd(f"{adb_path} devices")
    print(f"  设备列表:\n{devices}")

# 5. 检查 Appium 服务器
print("\n[5] Appium 服务器")
try:
    import requests
    resp = requests.get("http://127.0.0.1:4723/status", timeout=5)
    print(f"  状态: 运行中 (HTTP {resp.status_code})")
except Exception as e:
    print(f"  状态: 未运行 ({e})")

# 6. 检查 APK 文件
print("\n[6] APK 文件")
apk_dirs = [
    "/Users/Davy/PycharmProjects/CastPlay/android-app/app/build/outputs/apk/debug",
    "/Users/Davy/PycharmProjects/CastPlay/android-app/app/build/outputs/apk/release"
]
for d in apk_dirs:
    if os.path.exists(d):
        files = os.listdir(d)
        apks = [f for f in files if f.endswith(".apk")]
        print(f"  {d}: {apks or '无 APK'}")
    else:
        print(f"  {d}: 目录不存在")

# 7. Gradle wrapper
print("\n[7] Gradle Wrapper")
wrapper_jar = "/Users/Davy/PycharmProjects/CastPlay/android-app/gradle/wrapper/gradle-wrapper.jar"
print(
    f"  gradle-wrapper.jar: {'存在' if os.path.exists(wrapper_jar) else '不存在'}")
if os.path.exists(wrapper_jar):
    print(f"  大小: {os.path.getsize(wrapper_jar)} bytes")

print("\n" + "=" * 60)
print("检查完成")
print("=" * 60)
