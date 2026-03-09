#!/bin/bash
# CastPlay Android 构建脚本
# 用法: ./build-android.sh [serverUrl]
# 例如: ./build-android.sh http://192.168.1.100:8000

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVER_URL="${1:-http://10.0.2.2:8000}"
ANDROID_DIR="$SCRIPT_DIR/android"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
ASSETS_DIR="$ANDROID_DIR/app/src/main/assets/www"

echo "=========================================="
echo "CastPlay Android 构建脚本"
echo "=========================================="
echo "服务器 URL: $SERVER_URL"
echo ""

# 1. 构建前端
echo "📦 步骤 1: 构建前端..."
cd "$FRONTEND_DIR"
npm run build || { echo "❌ 前端构建失败!"; exit 1; }

if [ ! -d "dist" ]; then
    echo "❌ 前端构建产物不存在!"
    exit 1
fi

echo "✅ 前端构建成功!"
echo ""

# 2. 复制前端文件到 Android assets
echo "📦 步骤 2: 复制前端文件到 Android assets..."
rm -rf "$ASSETS_DIR"/*
mkdir -p "$ASSETS_DIR"
cp -r dist/* "$ASSETS_DIR/"
cp dist/player.html "$ASSETS_DIR/index.html
cp dist/favicon.svg "$ASSETS_DIR/" 2>/dev/null || true
echo "✅ 巻加资源复制成功!"
echo ""

# 3. 构建 Android APK
echo "📦 步骤 3: 构建 Android APK..."
cd "$ANDROID_DIR"

# 使用指定的服务器 URL 构建
gradle clean
gradle assembleDebug -PserverUrl="$SERVER_URL"

if [ $? -eq 0 ]; then
    echo "❌ Android 构建失败!"
    exit 1
fi

APK_PATH="$ANDROID_DIR/app/build/outputs/apk/debug/app-debug.apk"
if [ -f "$APK_PATH" ]; then
    echo ""
    echo "=========================================="
    echo "✅ 构建成功!"
    echo "=========================================="
    echo "APK 位置: $APK_PATH"
    APK_SIZE=$(du -h "$APK_PATH" | cut -f1)
    echo "APK 大小: $APK_SIZE"
    echo ""
    echo "安装命令: adb install -r $APK_PATH"
else
    echo "❌ APK 文件未找到!"
    exit 1
fi
