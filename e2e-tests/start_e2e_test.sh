#!/bin/bash
# E2E 测试启动脚本

set -e

# 配置环境
export PATH="/Users/Davy/.nvm/versions/node/v22.14.0/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
export ANDROID_HOME="/Users/Davy/PycharmProjects/CastPlay/android-sdk"
export JAVA_HOME="/Users/Davy/Library/Java/JavaVirtualMachines/jbr-17.0.14/Contents/Home"

echo "=========================================="
echo "E2E 自动化测试启动脚本"
echo "=========================================="

# 1. 检查 Appium
echo ""
echo "[1] 检查 Appium..."
if pgrep -f "appium" > /dev/null; then
    echo "  ✓ Appium 已运行"
else
    echo "  启动 Appium..."
    nohup appium --port 4723 > /tmp/appium.log 2>&1 &
    sleep 5
    if curl -s http://127.0.0.1:4723/status > /dev/null; then
        echo "  ✓ Appium 启动成功"
    else
        echo "  ✗ Appium 启动失败"
        exit 1
    fi
fi

# 2. 检查模拟器
echo ""
echo "[2] 检查模拟器..."
if $ANDROID_HOME/platform-tools/adb devices | grep -q "emulator"; then
    echo "  ✓ 模拟器已连接"
else
    echo "  启动模拟器..."
    nohup $ANDROID_HOME/emulator/emulator -avd Pixel_4_API_30 -no-snapshot-save -no-audio > /tmp/emulator.log 2>&1 &
    echo "  等待模拟器启动..."
    $ANDROID_HOME/platform-tools/adb wait-for-device
    sleep 30
    if $ANDROID_HOME/platform-tools/adb shell getprop sys.boot_completed | grep -q "1"; then
        echo "  ✓ 模拟器启动成功"
    else
        echo "  ✗ 模拟器启动超时"
        exit 1
    fi
fi

# 3. 运行测试
echo ""
echo "[3] 运行 E2E 测试..."
cd /Users/Davy/PycharmProjects/CastPlay/e2e-tests
python -m pytest tests/test_e2e_full_flow.py -v -s --tb=short 2>&1

echo ""
echo "=========================================="
echo "测试完成"
echo "=========================================="
