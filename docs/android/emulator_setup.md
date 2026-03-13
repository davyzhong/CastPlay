# Android 模拟器设置指南

## 概述

本文档描述了如何在 macOS (Apple Silicon) 上设置 Android 模拟器，用于测试 CastPlay 应用。

## 前置要求

### 1. 系统要求
- macOS 12.0+ (Monterey 或更高版本)
- Apple Silicon (M1/M2/M3) 或 Intel Mac
- 至少 8GB 可用内存
- 至少 20GB 可用磁盘空间

### 2. 必须安装的软件

#### Homebrew
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### Java 17+
```bash
brew install openjdk@17
sudo ln -sfn /opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk /Library/Java/JavaVirtualMachines/openjdk-17.jdk
```

#### Android Command Line Tools
```bash
brew install android-commandlinetools
```

## 自动化设置

### 完整设置（首次运行）

运行完整设置脚本：

```bash
cd /path/to/CastPlay/castplay-allinone
chmod +x scripts/setup_android_emulator.sh
./scripts/setup_android_emulator.sh
```

### 日常使用

启动模拟器并安装应用：

```bash
./scripts/start_emulator.sh# 重新构建并安装
./scripts/start_emulator.sh --rebuild
```

## 手动设置步骤

如果需要手动设置，请按以下步骤操作：

### 步骤 1: 创建 Android SDK 目录

```bash
# 设置 SDK 路径（根据你的项目位置调整）
export ANDROID_SDK_ROOT=/path/to/CastPlay/android-sdk
mkdir -p "$ANDROID_SDK_ROOT"
```

### 步骤 2: 接受许可证

```bash
mkdir -p "$ANDROID_SDK_ROOT/licenses"
echo -e "\n24333f8a63b6825ea9c5514f83c2829b004d1fee" > "$ANDROID_SDK_ROOT/licenses/android-sdk-license"
```

### 步骤 3: 安装必要组件

```bash
# 设置包管理器路径
SDKMANAGER="/opt/homebrew/bin/sdkmanager"

# 安装构建工具
echo "y" | $SDKMANAGER --sdk_root="$ANDROID_SDK_ROOT" "build-tools;34.0.0"

# 安装平台
echo "y" | $SDKMANAGER --sdk_root="$ANDROID_SDK_ROOT" "platforms;android-34"

# 安装平台工具
echo "y" | $SDKMANAGER --sdk_root="$ANDROID_SDK_ROOT" "platform-tools"

# 安装模拟器
echo "y" | $SDKMANAGER --sdk_root="$ANDROID_SDK_ROOT" "emulator"

# 安装系统镜像 (Android 30, ARM64)
echo "y" | $SDKMANAGER --sdk_root="$ANDROID_SDK_ROOT" "system-images;android-30;google_apis;arm64-v8a"
```

### 步骤 4: 创建 AVD (Android Virtual Device)

```bash
# 创建 AVD 目录
mkdir -p ~/.android/avd/CastPlay_Test.avd

# 创建配置文件
cat > ~/.android/avd/CastPlay_Test.avd/config.ini << 'EOF'
AvdId=CastPlay_Test
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
image.sysdir.1=system-images/android-30/google_apis/arm64-v8a/
runtime.network.latency=none
runtime.network.speed=full
sdcard.size=512MB
showDeviceFrame=no
vm.heapSize=256
EOF

# 创建 AVD 元数据文件
cat > ~/.android/avd/CastPlay_Test.ini << 'EOF'
avd.ini.encoding=UTF-8
path=/Users/你的用户名/.android/avd/CastPlay_Test.avd
path.rel=avd/CastPlay_Test.avd
target=android-30
EOF
```

**注意**: 将 `path` 中的用户名替换为你的实际用户名。

### 步骤 5: 启动模拟器

```bash
export ANDROID_SDK_ROOT=/path/to/CastPlay/android-sdk

# 启动模拟器（后台运行）
"$ANDROID_SDK_ROOT/emulator/emulator" \
    -avd CastPlay_Test \
    -no-snapshot \
    -no-audio \
    -no-boot-anim \
    -gpu swiftshader_indirect &

# 等待设备启动
adb wait-for-device

# 等待系统启动完成
while [ "$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" != "1" ]; do
    sleep 2
done

echo "模拟器已就绪"
```

### 步骤 6: 安装 APK

```bash
# 构建 APK（如果需要）
cd /path/to/CastPlay/castplay-allinone/android
./gradlew assembleDebug

# 安装 APK
APK_PATH="app/build/outputs/apk/debug/app-debug.apk"
adb install -r "$APK_PATH"
```

### 步骤 7: 启动应用

```bash
# 启动 CastPlay 应用
adb shell monkey -p com.castplay.player.debug -c android.intent.category.LAUNCHER 1
```

## 常用命令

### ADB 命令

| 命令 | 描述 |
|------|------|
| `adb devices` | 列出已连接设备 |
| `adb logcat` | 查看实时日志 |
| `adb logcat -c` | 清除日志缓冲区 |
| `adb shell` | 进入设备 shell |
| `adb install -r app.apk` | 安装/更新 APK |
| `adb uninstall <package>` | 卸载应用 |
| `adb pull <remote> <local>` | 从设备拉取文件 |
| `adb push <local> <remote>` | 推送文件到设备 |

### 模拟器命令

| 命令 | 描述 |
|------|------|
| `adb emu kill` | 关闭模拟器 |
| `adb emu avd name` | 显示当前 AVD 名称 |
| `adb shell screencap -p /sdcard/screen.png` | 截图 |
| `adb pull /sdcard/screen.png` | 拉取截图 |

### 调试命令

```bash
# 查看 CastPlay 应用日志
adb logcat -s CastPlay:* | grep -E "(CastPlay|ExoPlayer|WebSocket)"

# 查看所有错误
adb logcat *:E

# 实时查看崩溃日志
adb logcat -s AndroidRuntime:E
```

## 故障排除

### 问题 1: 模拟器启动失败

**症状**: 模拟器窗口不出现或立即崩溃

**解决方案**:
1. 检查系统镜像是否正确安装
2. 尝试使用不同的 GPU 模式:
   ```bash
   emulator -avd CastPlay_Test -gpu host  # 使用主机 GPU
   emulator -avd CastPlay_Test -gpu swiftshader_indirect  # 软件渲染
   ```

### 问题 2: APK 安装失败

**症状**: `INSTALL_FAILED_UPDATE_INCOMPATIBLE`

**解决方案**:
```bash
# 先卸载旧版本
adb uninstall com.castplay.player.debug
# 重新安装
adb install app-debug.apk
```

### 问题 3: 模拟器网络问题

**症状**: 应用无法连接到后端服务

**解决方案**:
1. 使用 `10.0.2.2` 作为主机地址（模拟器特有）
2. 或使用本地 IP 地址:
   ```bash
   # 查看本机 IP
   ifconfig | grep "inet " | grep -v 127.0.0.1
   ```

### 问题 4: 模拟器太慢

**解决方案**:
1. 增加 RAM: 修改 `hw.ramSize=4096`
2. 启用硬件加速: 确保 HAXM 或 Hypervisor.Framework 已安装
3. 使用 x86 系统镜像（需要额外安装）

## 配置参考

### AVD 配置选项

| 选项 | 描述 | 示例值 |
|------|------|--------|
| `hw.ramSize` | RAM 大小(MB) | 2048 |
| `hw.lcd.width` | 屏幕宽度 | 1080 |
| `hw.lcd.height` | 屏幕高度 | 2400 |
| `hw.lcd.density` | 屏幕密度 (DPI) | 420 |
| `hw.cpu.ncore` | CPU 核心数 | 4 |
| `sdcard.size` | SD 卡大小 | 512MB |

### 环境变量

| 变量 | 描述 | 示例 |
|------|------|------|
| `ANDROID_SDK_ROOT` | Android SDK 路径 | `/path/to/android-sdk` |
| `ANDROID_HOME` | 同上（兼容） | 同上 |
| `ANDROID_AVD_HOME` | AVD 存储路径 | `~/.android/avd` |

## 相关文件

- `scripts/setup_android_emulator.sh` - 完整设置脚本
- `scripts/start_emulator.sh` - 快速启动脚本
- `android/app/build.gradle.kts` - Android 构建配置
- `android/local.properties` - 本地 SDK 路径配置
