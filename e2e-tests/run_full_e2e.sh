#!/bin/bash
# E2E 自动化测试完整流程脚本

set -e

# 配置路径
export ANDROID_HOME="/Users/Davy/PycharmProjects/CastPlay/android-sdk"
export JAVA_HOME="/Users/Davy/Library/Java/JavaVirtualMachines/jbr-17.0.14/Contents/Home"
export PATH="$JAVA_HOME/bin:$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$PATH"

PROJECT_DIR="/Users/Davy/PycharmProjects/CastPlay"
ANDROID_APP_DIR="$PROJECT_DIR/android-app"
SERVER_DIR="$PROJECT_DIR/castplay-server"
E2E_DIR="$PROJECT_DIR/e2e-tests"
LOG_FILE="$E2E_DIR/e2e_run.log"

# 清空日志
echo "E2E 测试开始: $(date)" > "$LOG_FILE"

log() {
    echo "[$(date '+%H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

cleanup() {
    log "清理进程..."
    pkill -f "appium" 2>/dev/null || true
    pkill -f "emulator" 2>/dev/null || true
    pkill -f "flask" 2>/dev/null || true
    pkill -f "run.py" 2>/dev/null || true
}

# 捕获退出信号
trap cleanup EXIT

log "=============================================="
log "步骤 1: 检查环境"
log "=============================================="

# 检查 Java
log "Java: $($JAVA_HOME/bin/java -version 2>&1 | head -1)"

# 检查 ADB
log "ADB: $($ANDROID_HOME/platform-tools/adb --version | head -1)"

# 检查 Appium
if command -v appium &> /dev/null; then
    log "Appium: $(appium --version)"
else
    log "ERROR: Appium 未安装"
    exit 1
fi

log "=============================================="
log "步骤 2: 启动 Appium 服务器"
log "=============================================="

pkill -f appium 2>/dev/null || true
sleep 2
appium --port 4723 >> "$LOG_FILE" 2>&1 &
APPIUM_PID=$!
log "Appium PID: $APPIUM_PID"
sleep 5

# 验证 Appium
if curl -s http://127.0.0.1:4723/status | grep -q "ready"; then
    log "Appium 服务器已就绪"
else
    log "WARNING: Appium 可能未就绪，继续..."
fi

log "=============================================="
log "步骤 3: 启动 Android 模拟器"
log "=============================================="

# 检查模拟器是否已运行
DEVICE=$($ANDROID_HOME/platform-tools/adb devices | grep "emulator" | head -1)
if [ -z "$DEVICE" ]; then
    log "启动模拟器 Pixel_4_API_30..."
    $ANDROID_HOME/emulator/emulator -avd Pixel_4_API_30 -no-snapshot-save -no-audio &
    EMULATOR_PID=$!
    log "模拟器 PID: $EMULATOR_PID"

    # 等待模拟器启动
    log "等待模拟器启动..."
    $ANDROID_HOME/platform-tools/adb wait-for-device

    for i in {1..60}; do
        BOOT=$($ANDROID_HOME/platform-tools/adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')
        if [ "$BOOT" = "1" ]; then
            log "模拟器启动完成"
            break
        fi
        sleep 2
    done
else
    log "模拟器已运行: $DEVICE"
fi

log "=============================================="
log "步骤 4: 构建 Android APK"
log "=============================================="

cd "$ANDROID_APP_DIR"

# 检查 APK 是否存在
APK_PATH="$ANDROID_APP_DIR/app/build/outputs/apk/debug/app-debug.apk"
if [ ! -f "$APK_PATH" ]; then
    log "构建 Debug APK..."
    ./gradlew assembleDebug 2>&1 | tail -20 >> "$LOG_FILE"

    if [ -f "$APK_PATH" ]; then
        log "APK 构建成功: $APK_PATH"
    else
        log "ERROR: APK 构建失败"
        # 尝试列出可能的 APK
        find "$ANDROID_APP_DIR" -name "*.apk" 2>/dev/null >> "$LOG_FILE"
        exit 1
    fi
else
    log "APK 已存在: $APK_PATH"
fi

log "=============================================="
log "步骤 5: 安装 APK 到模拟器"
log "=============================================="

# 检查应用是否已安装
INSTALLED=$($ANDROID_HOME/platform-tools/adb shell pm list packages | grep "castplay" || true)
if [ -z "$INSTALLED" ]; then
    log "安装 APK..."
    $ANDROID_HOME/platform-tools/adb install -r "$APK_PATH" 2>&1 | tee -a "$LOG_FILE"
else
    log "应用已安装: $INSTALLED"
    # 重新安装
    log "重新安装 APK..."
    $ANDROID_HOME/platform-tools/adb install -r "$APK_PATH" 2>&1 | tee -a "$LOG_FILE"
fi

log "=============================================="
log "步骤 6: 启动后端服务器"
log "=============================================="

cd "$SERVER_DIR"
pkill -f "run.py" 2>/dev/null || true
sleep 2

log "启动 Flask 服务器..."
python run.py >> "$LOG_FILE" 2>&1 &
FLASK_PID=$!
log "Flask PID: $FLASK_PID"
sleep 5

# 验证后端
if curl -s http://127.0.0.1:5000/api/devices | grep -q "\["; then
    log "后端服务器已就绪"
else
    log "WARNING: 后端可能未完全就绪"
fi

log "=============================================="
log "步骤 7: 运行 E2E 测试"
log "=============================================="

cd "$E2E_DIR"
log "运行测试..."

# 运行环境验证测试
python -m pytest tests/test_environment_validation.py -v -s 2>&1 | tee -a "$LOG_FILE"

# 运行 CastPlay E2E 测试
python -m pytest tests/test_castplay_e2e.py -v -s 2>&1 | tee -a "$LOG_FILE"

log "=============================================="
log "测试完成"
log "=============================================="

echo ""
echo "详细日志: $LOG_FILE"
