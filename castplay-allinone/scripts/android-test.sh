#!/bin/bash

# CastPlay Android 测试脚本
# 用法: ./scripts/android-test.sh [--skip-build] [--skip-emulator]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
APK_PATH="$PROJECT_DIR/android/app/build/outputs/apk/debug/app-debug.apk"
PACKAGE_NAME="com.castplay.player.debug"
ACTIVITY_NAME="$PACKAGE_NAME/com.castplay.player.MainActivity"
AVD_NAME="${AVD_NAME:-CastPlay_Test}"

# Android SDK 路径
ANDROID_SDK="${ANDROID_SDK:-/opt/homebrew/share/android-commandlinetools}"
EMULATOR="$ANDROID_SDK/emulator/emulator/emulator"
ADB="$ANDROID_SDK/platform-tools/adb"

# 解析参数
SKIP_BUILD=false
SKIP_EMULATOR=false

for arg in "$@"; do
    case $arg in
        --skip-build) SKIP_BUILD=true ;;
        --skip-emulator) SKIP_EMULATOR=true ;;
        --help)
            echo "用法: $0 [选项]"
            echo "选项:"
            echo "  --skip-build     跳过 APK 构建，直接安装现有 APK"
            echo "  --skip-emulator  跳过模拟器启动，使用已连接的设备"
            echo "  --help           显示帮助信息"
            exit 0
            ;;
    esac
done

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   CastPlay Android 测试自动化脚本${NC}"
echo -e "${BLUE}========================================${NC}"

# 检查依赖
check_dependencies() {
    echo -e "\n${YELLOW}[1/5] 检查依赖...${NC}"

    if [ ! -f "$EMULATOR" ]; then
        echo -e "${RED}错误: 找不到 Android 模拟器: $EMULATOR${NC}"
        exit 1
    fi

    if [ ! -f "$ADB" ]; then
        echo -e "${RED}错误: 找不到 ADB: $ADB${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ 依赖检查通过${NC}"
}

# 构建 APK
build_apk() {
    if [ "$SKIP_BUILD" = true ]; then
        echo -e "\n${YELLOW}[2/5] 跳过构建 (使用 --skip-build)${NC}"
        if [ ! -f "$APK_PATH" ]; then
            echo -e "${RED}错误: APK 文件不存在: $APK_PATH${NC}"
            exit 1
        fi
        return
    fi

    echo -e "\n${YELLOW}[2/5] 构建 APK...${NC}"
    cd "$PROJECT_DIR"

    # 构建前端资源
    echo "  - 构建前端资源..."
    if [ -f "frontend/package.json" ]; then
        cd "$PROJECT_DIR/frontend"
        npm run build 2>&1 | tail -3
        # 复制构建产物到 Android assets
        echo "  - 复制构建产物到 Android assets..."
        rm -rf "$PROJECT_DIR/android/app/src/main/assets/www/*"
        cp -r "$PROJECT_DIR/frontend/dist/*" "$PROJECT_DIR/android/app/src/main/assets/www/"
        cd "$PROJECT_DIR"
    fi

    # 构建 APK
    echo "  - 构建 Android APK..."
    cd android
    ./gradlew assembleDebug

    if [ ! -f "$APK_PATH" ]; then
        echo -e "${RED}错误: APK 构建失败${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ APK 构建完成: $APK_PATH${NC}"
    echo -e "  文件大小: $(du -h "$APK_PATH" | cut -f1)"
}

# 启动模拟器
start_emulator() {
    if [ "$SKIP_EMULATOR" = true ]; then
        echo -e "\n${YELLOW}[3/5] 跳过模拟器启动 (使用 --skip-emulator)${NC}"
        return
    fi

    echo -e "\n${YELLOW}[3/5] 启动 Android 模拟器...${NC}"

    # 检查是否已有设备连接
    DEVICES=$("$ADB" devices 2>/dev/null | grep -v "List of devices" | grep "device$" | wc -l)
    if [ "$DEVICES" -gt 0 ]; then
        echo -e "${GREEN}✓ 已有 $DEVICES 个设备连接${NC}"
        "$ADB" devices
        return
    fi

    # 检查 AVD 是否存在
    AVD_EXISTS=$(ls -d ~/.android/avd/$AVD_NAME.avd 2>/dev/null | wc -l)
    if [ "$AVD_EXISTS" -eq 0 ]; then
        echo -e "${RED}错误: 找不到 AVD: $AVD_NAME${NC}"
        echo "可用的 AVD 列表:"
        ls -1 ~/.android/avd/*.avd 2>/dev/null | xargs -n1 basename | sed 's/.avd$//'
        exit 1
    fi

    echo "  - 启动 $AVD_NAME..."
    "$EMULATOR" -avd "$AVD_NAME" -no-snapshot-load &
    EMULATOR_PID=$!
    echo "  - 模拟器 PID: $EMULATOR_PID"

    # 等待设备就绪
    echo "  - 等待设备就绪..."
    "$ADB" wait-for-device

    # 等待系统启动完成
    echo "  - 等待系统启动..."
    for i in {1..30}; do
        BOOT_COMPLETE=$("$ADB" shell getprop sys.boot_completed 2>/dev/null)
        if [ "$BOOT_COMPLETE" = "1" ]; then
            break
        fi
        sleep 1
        printf "."
    done
    echo ""

    echo -e "${GREEN}✓ 模拟器已就绪${NC}"
    "$ADB" devices
}

# 安装 APK
install_apk() {
    echo -e "\n${YELLOW}[4/5] 安装 APK...${NC}"

    # 卸载旧版本（可选，避免签名问题）
    "$ADB" uninstall "$PACKAGE_NAME" 2>/dev/null || true

    # 安装新版本
    "$ADB" install -r "$APK_PATH"

    echo -e "${GREEN}✓ APK 安装完成${NC}"
}

# 启动应用并检查日志
launch_app() {
    echo -e "\n${YELLOW}[5/5] 启动应用...${NC}"

    # 启动应用
    "$ADB" shell am start -n "$ACTIVITY_NAME"

    sleep 2

    # 检查应用是否运行
    CURRENT_ACTIVITY=$("$ADB" shell dumpsys activity activities 2>/dev/null | grep "mResumedActivity" | grep -o "com.castplay.player[^ ]*")
    if [ -n "$CURRENT_ACTIVITY" ]; then
        echo -e "${GREEN}✓ 应用已启动: $CURRENT_ACTIVITY${NC}"
    else
        echo -e "${RED}警告: 无法确认应用是否启动${NC}"
    fi

    # 显示最近的日志
    echo -e "\n${BLUE}--- 最近的应用日志 ---${NC}"
    "$ADB" logcat -d -t 20 | grep -iE "castplay|mainactivity|player" | tail -10

    # 截图
    SCREENSHOT_PATH="$PROJECT_DIR/screen_test_$(date +%Y%m%d_%H%M%S).png"
    "$ADB" exec-out screencap -p > "$SCREENSHOT_PATH"
    echo -e "${GREEN}✓ 截图已保存: $SCREENSHOT_PATH${NC}"
}

# 显示总结
show_summary() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${GREEN}   测试环境已就绪!${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo "常用命令:"
    echo "  查看日志:    $ADB logcat -s MainActivity:* chromium:*"
    echo "  重新启动:    $ADB shell am force-stop $PACKAGE_NAME && $ADB shell am start -n $ACTIVITY_NAME"
    echo "  截图:        $ADB exec-out screencap -p > screen.png"
    echo "  安装新APK:   $ADB install -r $APK_PATH"
    echo ""
}

# 执行主流程
main() {
    check_dependencies
    build_apk
    start_emulator
    install_apk
    launch_app
    show_summary
}

main "$@"
