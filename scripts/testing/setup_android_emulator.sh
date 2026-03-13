#!/bin/bash
# =============================================================================
# CastPlay Android 模拟器设置脚本
# =============================================================================
# 此脚本用于在 macOS (Apple Silicon) 上设置 Android 模拟器并安装 CastPlay 应用
#
# 前置要求：
# 1. macOS (Apple Silicon M1/M2/M3)
# 2. Homebrew 已安装
# 3. Java 17+ 已安装
# 4. Android SDK 已下载到项目中
#
# 使用方法：
#   chmod +x scripts/setup_android_emulator.sh
#   ./scripts/setup_android_emulator.sh
#
# 作者: CastPlay Team
# 日期: 2026-03-11
# =============================================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# =============================================================================
# 配置变量
# =============================================================================

# 获取脚本所在目录的父目录（项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Android SDK 路径（可根据需要修改）
ANDROID_SDK_ROOT="${ANDROID_SDK_ROOT:-$PROJECT_ROOT/android-sdk}"

# AVD 名称
AVD_NAME="CastPlay_Test"

# 系统镜像版本
ANDROID_VERSION="30"
SYSTEM_IMAGE="system-images;android-${ANDROID_VERSION};google_apis;arm64-v8a"

# APK 路径
APK_PATH="$PROJECT_ROOT/android/app/build/outputs/apk/debug/app-debug.apk"

# =============================================================================
# 步骤 1: 检查前置条件
# =============================================================================

print_info "步骤 1/7: 检查前置条件..."

# 检查 Homebrew
if ! command -v brew &> /dev/null; then
    print_error "Homebrew 未安装，请先安装 Homebrew"
    print_info "安装命令: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi
print_success "Homebrew 已安装"

# 检查 Java
if ! command -v java &> /dev/null; then
    print_error "Java 未安装，请先安装 Java 17+"
    print_info "安装命令: brew install openjdk@17"
    exit 1
fi
JAVA_VERSION=$(java -version 2>&1 | head -n 1 | awk -F '"' '{print $2}' | cut -d'.' -f1)
if [ "$JAVA_VERSION" -lt 17 ]; then
    print_error "Java 版本过低，需要 Java 17+"
    exit 1
fi
print_success "Java 已安装 (版本: $(java -version 2>&1 | head -n 1))"

# 检查 sdkmanager
if ! command -v sdkmanager &> /dev/null; then
    print_info "sdkmanager 未找到，正在安装 Android command line tools..."
    brew install android-commandlinetools
fi
print_success "sdkmanager 已就绪"

# =============================================================================
# 步骤 2: 设置 Android SDK 目录
# =============================================================================

print_info "步骤 2/7: 设置 Android SDK 目录..."

# 创建 SDK 目录
mkdir -p "$ANDROID_SDK_ROOT"
mkdir -p "$ANDROID_SDK_ROOT/licenses"
mkdir -p "$ANDROID_SDK_ROOT/platforms"
mkdir -p "$ANDROID_SDK_ROOT/system-images"

# 创建许可证文件
print_info "创建 Android SDK 许可证文件..."
echo -e "\n24333f8a63b6825ea9c5514f83c2829b004d1fee" > "$ANDROID_SDK_ROOT/licenses/android-sdk-license"
echo -e "\n84831b9409646a918e30573bab4c9c91346d8abd" >> "$ANDROID_SDK_ROOT/licenses/android-sdk-license"
echo -e "\nd975f751698a77b662f1254ddbeed3901e976f5a" >> "$ANDROID_SDK_ROOT/licenses/android-sdk-license"

print_success "Android SDK 目录已创建: $ANDROID_SDK_ROOT"

# =============================================================================
# 步骤 3: 安装 Android SDK 组件
# =============================================================================

print_info "步骤 3/7: 安装 Android SDK 组件..."

export ANDROID_SDK_ROOT
export ANDROID_HOME=$ANDROID_SDK_ROOT

# 安装平台工具
print_info "安装 platform-tools..."
echo "y" | sdkmanager --sdk_root="$ANDROID_SDK_ROOT" "platform-tools" 2>&1 | tail -5

# 安装 Build Tools
print_info "安装 build-tools..."
echo "y" | sdkmanager --sdk_root="$ANDROID_SDK_ROOT" "build-tools;34.0.0" 2>&1 | tail -5

# 安装 Android 平台
print_info "安装 Android platform..."
echo "y" | sdkmanager --sdk_root="$ANDROID_SDK_ROOT" "platforms;android-${ANDROID_VERSION}" 2>&1 | tail -5

# 安装模拟器
print_info "安装 Android Emulator..."
echo "y" | sdkmanager --sdk_root="$ANDROID_SDK_ROOT" "emulator" 2>&1 | tail -5

# 安装系统镜像
print_info "安装系统镜像: $SYSTEM_IMAGE"
echo "y" | sdkmanager --sdk_root="$ANDROID_SDK_ROOT" "$SYSTEM_IMAGE" 2>&1 | tail -5

print_success "Android SDK 组件安装完成"

# =============================================================================
# 步骤 4: 创建 Android Virtual Device (AVD)
# =============================================================================

print_info "步骤 4/7: 创建 Android Virtual Device (AVD)..."

# 创建 AVD 目录
mkdir -p ~/.android/avd/$AVD_NAME.avd

# 创建 AVD 配置文件
cat > ~/.android/avd/$AVD_NAME.avd/config.ini << EOF
AvdId=$AVD_NAME
PlayStore.enabled=false
abi.type=arm64-v8a
avd.ini.displayname=CastPlay Test
avd.ini.encoding=UTF-8
disk.cachePartition=true
disk.cachePartition.size=800MB
fastboot.forceColdBoot=no
hw.accelerometer=yes
hw.audioInput=yes
hw.battery=yes
hw.camera.back=emulated
hw.camera.front=emulated
hw.cpu.arch=arm64
hw.cpu.ncore=4
hw.dPad=no
hw.gps=yes
hw.gpu.enabled=yes
hw.gpu.mode=auto
hw.initialOrientation=Portrait
hw.keyboard=yes
hw.lcd.density=420
hw.lcd.height=2400
hw.lcd.width=1080
hw.mainKeys=no
hw.ramSize=2048
hw.sdCard=yes
hw.sensors.orientation=yes
hw.sensors.proximity=yes
hw.trackBall=no
image.sysdir.1=system-images/android-${ANDROID_VERSION}/google_apis/arm64-v8a/
runtime.network.latency=none
runtime.network.speed=full
sdcard.size=512MB
showDeviceFrame=no
vm.heapSize=256
EOF

# 创建 AVD ini 文件
cat > ~/.android/avd/$AVD_NAME.ini << EOF
avd.ini.encoding=UTF-8
path=$HOME/.android/avd/$AVD_NAME.avd
path.rel=avd/$AVD_NAME.avd
target=android-${ANDROID_VERSION}
EOF

print_success "AVD '$AVD_NAME' 创建成功"

# =============================================================================
# 步骤 5: 构建 APK（如果需要）
# =============================================================================

print_info "步骤 5/7: 检查 APK 文件..."

if [ ! -f "$APK_PATH" ]; then
    print_warning "APK 文件不存在，正在构建..."

    cd "$PROJECT_ROOT/android"

    # 检查 Gradle wrapper
    if [ -f "./gradlew" ]; then
        ./gradlew assembleDebug
    else
        # 使用系统 Gradle
        gradle assembleDebug
    fi

    if [ ! -f "$APK_PATH" ]; then
        print_error "APK 构建失败"
        exit 1
    fi
fi

print_success "APK 文件已就绪: $APK_PATH"

# =============================================================================
# 步骤 6: 启动 Android 模拟器
# =============================================================================

print_info "步骤 6/7: 启动 Android 模拟器..."

EMULATOR_PATH="$ANDROID_SDK_ROOT/emulator/emulator"

if [ ! -f "$EMULATOR_PATH" ]; then
    print_error "模拟器未找到: $EMULATOR_PATH"
    exit 1
fi

# 检查是否已有模拟器在运行
RUNNING_EMULATORS=$(pgrep -f "emulator.*$AVD_NAME" 2>/dev/null || true)
if [ -n "$RUNNING_EMULATORS" ]; then
    print_warning "模拟器已在运行中"
else
    # 后台启动模拟器
    print_info "启动模拟器 (后台模式)..."
    "$EMULATOR_PATH" \
        -avd "$AVD_NAME" \
        -no-snapshot \
        -no-audio \
        -no-boot-anim \
        -gpu swiftshader_indirect &
    EMULATOR_PID=$!
    print_info "模拟器 PID: $EMULATOR_PID"
fi

# 等待模拟器启动
print_info "等待模拟器启动..."
adb wait-for-device

# 等待启动完成
for i in {1..60}; do
    BOOT_COMPLETED=$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')
    if [ "$BOOT_COMPLETED" = "1" ]; then
        print_success "模拟器启动完成!"
        break
    fi
    echo -n "."
    sleep 2
done
echo ""

# 显示设备信息
print_info "设备信息:"
adb devices -l

# =============================================================================
# 步骤 7: 安装并启动应用
# =============================================================================

print_info "步骤 7/7: 安装并启动应用..."

# 安装 APK
print_info "安装 APK..."
adb install -r "$APK_PATH"

if [ $? -eq 0 ]; then
    print_success "APK 安装成功!"
else
    print_error "APK 安装失败"
    exit 1
fi

# 启动应用
print_info "启动 CastPlay 应用..."
adb shell monkey -p com.castplay.player.debug -c android.intent.category.LAUNCHER 1

print_success "CastPlay 应用已启动!"

# =============================================================================
# 完成
# =============================================================================

echo ""
echo "=========================================="
print_success "Android 模拟器设置完成!"
echo "=========================================="
echo ""
echo "模拟器信息:"
echo "  - AVD 名称: $AVD_NAME"
echo "  - Android 版本: $ANDROID_VERSION"
echo "  - 设备 ID: $(adb get-serialno)"
echo ""
echo "常用命令:"
echo "  - 查看日志: adb logcat"
echo "  - 截图: adb shell screencap -p /sdcard/screen.png && adb pull /sdcard/screen.png"
echo "  - 关闭模拟器: adb emu kill"
echo "  - 重新启动应用: adb shell monkey -p com.castplay.player.debug -c android.intent.category.LAUNCHER 1"
echo ""
