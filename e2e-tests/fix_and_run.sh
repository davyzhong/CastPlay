#!/bin/bash
# E2E 测试修复和执行脚本
# 运行方式: cd /Users/Davy/PycharmProjects/CastPlay/e2e-tests && ./fix_and_run.sh

set -e

echo "=========================================="
echo "CastPlay E2E 测试修复与执行"
echo "=========================================="

# 配置
export ANDROID_HOME="/Users/Davy/PycharmProjects/CastPlay/android-sdk"
export JAVA_HOME="/Users/Davy/Library/Java/JavaVirtualMachines/jbr-17.0.14/Contents/Home"
export PATH="$JAVA_HOME/bin:$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$PATH"

PROJECT_DIR="/Users/Davy/PycharmProjects/CastPlay"
ANDROID_APP_DIR="$PROJECT_DIR/android-app"

echo ""
echo "[步骤 1] 修复 Gradle Wrapper"
echo "----------------------------------------"

cd "$ANDROID_APP_DIR"
WRAPPER_JAR="gradle/wrapper/gradle-wrapper.jar"

if [ ! -f "$WRAPPER_JAR" ] || [ $(stat -f%z "$WRAPPER_JAR" 2>/dev/null || echo 0) -lt 10000 ]; then
    echo "Gradle wrapper 需要修复..."

    # 方法1: 使用系统 gradle 重新生成
    if command -v gradle &> /dev/null; then
        echo "使用系统 gradle 生成 wrapper..."
        gradle wrapper --gradle-version=8.2
    else
        echo "系统 gradle 不可用，尝试直接下载..."
        # 方法2: 从 Maven 中央仓库下载
        WRAPPER_URL="https://repo1.maven.org/maven2/org/gradle/gradle-wrapper/8.2/gradle-wrapper-8.2.jar"
        curl -L -o "$WRAPPER_JAR" "$WRAPPER_URL" || {
            echo "下载失败，请手动修复或使用 Android Studio 构建"
            exit 1
        }
    fi
fi

if [ -f "$WRAPPER_JAR" ]; then
    SIZE=$(stat -f%z "$WRAPPER_JAR" 2>/dev/null || stat -c%s "$WRAPPER_JAR" 2>/dev/null || echo 0)
    echo "Wrapper jar 大小: $SIZE bytes"
    if [ "$SIZE" -gt 50000 ]; then
        echo "✓ Gradle wrapper 已修复"
    else
        echo "✗ Wrapper 文件可能损坏"
    fi
else
    echo "✗ Wrapper 文件不存在"
fi

echo ""
echo "[步骤 2] 构建 APK"
echo "----------------------------------------"

APK_PATH="$ANDROID_APP_DIR/app/build/outputs/apk/debug/app-debug.apk"

if [ ! -f "$APK_PATH" ]; then
    echo "构建 Debug APK..."
    cd "$ANDROID_APP_DIR"
    ./gradlew assembleDebug --no-daemon
fi

if [ -f "$APK_PATH" ]; then
    echo "✓ APK 构建成功: $APK_PATH"
else
    echo "✗ APK 构建失败"
    echo "建议: 使用 Android Studio 打开项目并构建"
    exit 1
fi

echo ""
echo "[步骤 3] 启动服务"
echo "----------------------------------------"

# 启动 Appium
echo "启动 Appium..."
pkill -f appium 2>/dev/null || true
appium --port 4723 &
sleep 3

# 检查模拟器
echo "检查模拟器..."
DEVICE=$($ANDROID_HOME/platform-tools/adb devices | grep "emulator")
if [ -z "$DEVICE" ]; then
    echo "启动模拟器..."
    $ANDROID_HOME/emulator/emulator -avd Pixel_4_API_30 -no-snapshot-save -no-audio &
    echo "等待模拟器启动..."
    $ANDROID_HOME/platform-tools/adb wait-for-device
    sleep 30
fi

# 安装 APK
echo "安装 APK..."
$ANDROID_HOME/platform-tools/adb install -r "$APK_PATH"

# 启动后端
echo "启动后端服务..."
pkill -f "run.py" 2>/dev/null || true
cd "$PROJECT_DIR/castplay-server"
python run.py &
sleep 3

echo ""
echo "[步骤 4] 运行 E2E 测试"
echo "----------------------------------------"

cd "$PROJECT_DIR/e2e-tests"

echo "运行环境验证测试..."
python -m pytest tests/test_environment_validation.py -v --tb=short

echo ""
echo "运行 CastPlay E2E 测试..."
python -m pytest tests/test_castplay_e2e.py -v --tb=short

echo ""
echo "=========================================="
echo "测试完成"
echo "=========================================="
