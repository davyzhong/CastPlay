#!/bin/bash
# =============================================================================
# CastPlay 快速启动模拟器脚本
# =============================================================================
# 用于快速启动已配置好的模拟器
#
# 使用方法：
#   ./scripts/start_emulator.sh [--rebuild]
#
# 参数：
#   --rebuild  重新构建 APK后再安装
# =============================================================================

set -e

# 配置
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ANDROID_SDK_ROOT="${ANDROID_SDK_ROOT:-$PROJECT_ROOT/android-sdk}"
AVD_NAME="CastPlay_Test"
APK_PATH="$PROJECT_ROOT/android/app/build/outputs/apk/debug/app-debug.apk"

# 颜色
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[OK]${NC} $1"; }

# 检查是否需要重新构建
if [ "$1" == "--rebuild" ]; then
    print_info "重新构建 APK..."
    cd "$PROJECT_ROOT/android"
    gradle assembleDebug --no-daemon 2>&1 | tail -10
    print_success "APK 构建完成"
fi

# 检查模拟器是否已运行
if pgrep -f "emulator.*$AVD_NAME" > /dev/null 2>&1; then
    print_info "模拟器已在运行"
else
    print_info "启动模拟器..."
    "$ANDROID_SDK_ROOT/emulator/emulator" \
        -avd "$AVD_NAME" \
        -no-snapshot \
        -no-audio &
    sleep 5
fi

# 等待设备
print_info "等待设备就绪..."
adb wait-for-device

for i in {1..30}; do
    if [ "$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = "1" ]; then
        break
    fi
    sleep 2
done

print_success "设备就绪"

# 安装 APK
print_info "安装 APK..."
adb install -r "$APK_PATH"
print_success "安装完成"

# 启动应用
print_info "启动应用..."
adb shell monkey -p com.castplay.player.debug -c android.intent.category.LAUNCHER 1

print_success "完成! CastPlay 已在模拟器中运行"
