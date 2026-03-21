# CastPlay Android端部署与测试指南

## 1. 环境准备

### 1.1 开发环境要求
- **操作系统**: Windows 10+, macOS 10.14+, 或 Linux
- **JDK**: 17 或更高版本
- **Android SDK**: API Level 34
- **Android Studio**: Flamingo | 2022.2.1 或更高版本
- **Gradle**: 8.2 或更高版本
- **Node.js**: 18+ (用于前端构建)
- **Git**: 用于代码版本控制

### 1.2 安装步骤

#### 1.2.1 安装JDK 17+
```bash
# macOS (使用Homebrew)
brew install openjdk@17

# Ubuntu/Debian
sudo apt update
sudo apt install openjdk-17-jdk

# 验证安装
java -version
```

#### 1.2.2 安装Android SDK
1. 下载并安装 Android Studio
2. 启动 Android Studio，完成初始设置
3. 通过 SDK Manager 安装以下组件：
   - Android SDK Platform 34
   - Android SDK Build-Tools (最新版本)
   - Android SDK Platform-Tools
   - Android SDK Tools

#### 1.2.3 配置环境变量
```bash
# macOS/Linux
export ANDROID_HOME=/path/to/android/sdk
export PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools

# Windows
set ANDROID_HOME=C:\Users\[username]\AppData\Local\Android\Sdk
set PATH=%PATH%;%ANDROID_HOME%\tools;%ANDROID_HOME%\platform-tools
```

#### 1.2.4 安装Node.js (用于前端构建)
```bash
# 使用官方安装包或包管理器
brew install node  # macOS
sudo apt install nodejs npm  # Ubuntu/Debian
```

## 2. 项目克隆与初始化

### 2.1 克隆项目
```bash
git clone <repository-url>
cd castplay-allinone
```

### 2.2 安装后端依赖
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2.3 安装前端依赖
```bash
cd frontend
npm install
cd ..
```

## 3. 后端服务启动

### 3.1 初始化数据库
```bash
python scripts/init_db.py
```

### 3.2 启动后端服务
```bash
# 开发模式
python -m uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload

# 或使用Gunicorn (生产模式)
pip install gunicorn
gunicorn app.main:app --workers 4 --bind 0.0.0.0:5000 --timeout 120
```

### 3.3 验证后端服务
访问 `http://localhost:5000/docs` 确认API文档页面正常打开。

## 4. Android端构建

### 4.1 构建前端资源
```bash
cd frontend
npm run build
cd ..
```

### 4.2 使用构建脚本
```bash
# 基础构建（使用默认服务器地址 http://10.0.2.2:8000）
./build-android.sh

# 指定服务器地址构建
./build-android.sh http://192.168.1.100:5000
```

### 4.3 手动构建步骤
如果构建脚本出现问题，可以手动执行以下步骤：

#### 4.3.1 复制前端资源到Android项目
```bash
# 确保前端已构建
cd frontend
npm run build

# 复制到Android assets目录
cd ..
rm -rf android/app/src/main/assets/www/*
mkdir -p android/app/src/main/assets/www
cp -r frontend/dist/* android/app/src/main/assets/www/
cp frontend/dist/player.html android/app/src/main/assets/www/index.html
```

#### 4.3.2 构建APK
```bash
cd android
./gradlew clean
./gradlew assembleDebug -PserverUrl="http://192.168.1.100:5000"
```

## 5. 设备准备与安装

### 5.1 Android设备准备
1. 启用开发者选项
   - 设置 → 关于手机 → 连续点击"版本号"7次
2. 启用USB调试
   - 设置 → 开发者选项 → USB调试
3. 确保设备与电脑正确连接

### 5.2 验证设备连接
```bash
adb devices
```
应显示连接的设备列表。

### 5.3 安装APK
```bash
# 安装到连接的设备
adb install -r android/app/build/outputs/apk/debug/app-debug.apk

# 如果有多个设备，指定设备
adb -s DEVICE_ID install -r android/app/build/outputs/apk/debug/app-debug.apk
```

## 6. 首次运行配置

### 6.1 应用权限
首次启动应用时，系统可能会请求以下权限：
- 存储权限（用于媒体缓存）
- 网络权限（用于连接服务器）
- 设备管理权限（用于Kiosk模式）

### 6.2 设备管理员设置（可选）
为了启用Kiosk模式：
1. 打开"设置" → "安全" → "设备管理员应用"
2. 启用"CastPlay Device Admin"

### 6.3 服务器连接
应用启动后会尝试连接配置的服务器地址。如果连接失败，会显示重试提示。

## 7. 功能测试

### 7.1 基础功能测试
1. **应用启动**: 验证应用正常启动，显示播放器界面
2. **网络连接**: 验证与服务器的连接状态
3. **设备注册**: 检查设备是否成功注册到服务器
4. **播放功能**: 验证媒体播放功能

### 7.2 高级功能测试
1. **MAC地址注册**: 验证基于MAC地址的设备注册
2. **注册码生成**: 验证设备注册码的生成和使用
3. **媒体缓存**: 测试媒体文件的下载和缓存功能
4. **WebSocket连接**: 验证实时通信功能
5. **Kiosk模式**: 验证设备锁定功能

### 7.3 自动化测试
运行Android端集成测试：

```bash
# 后端测试
cd tests
pytest integration/test_android_features.py -v

# 或运行所有测试
pytest -m "android" -v
```

## 8. 运维与监控

### 8.1 日志监控
```bash
# 查看应用日志
adb logcat | grep -i castplay

# 查看特定标签的日志
adb logcat -s MainActivity
adb logcat -s CacheManager
```

### 8.2 性能监控
- **内存使用**: `adb shell dumpsys meminfo com.castplay.player`
- **CPU使用**: `adb shell top -p $(pidof com.castplay.player)`
- **电池使用**: 通过系统设置查看应用耗电情况

### 8.3 错误诊断
常见问题及解决方案：

#### 8.3.1 无法连接服务器
- 检查服务器是否运行
- 检查网络连接
- 验证服务器地址配置

#### 8.3.2 媒体无法播放
- 检查媒体文件是否正确下载
- 验证文件权限
- 检查媒体格式兼容性

#### 8.3.3 应用崩溃
- 查看日志中的错误信息
- 检查内存使用情况
- 验证设备兼容性

## 9. 部署最佳实践

### 9.1 生产环境部署
1. **服务器配置**: 使用反向代理(Nginx/Apache)和SSL证书
2. **APK签名**: 使用正式的签名证书构建release版本
3. **性能优化**: 启用代码混淆和资源压缩
4. **安全配置**: 配置网络安全策略

### 9.2 设备批量部署
1. **配置管理**: 使用MDM(Mobile Device Management)解决方案
2. **应用分发**: 通过企业应用商店或OTA方式分发
3. **监控系统**: 部署集中监控和管理平台

### 9.3 更新策略
1. **APK更新**: 通过服务器推送更新通知
2. **配置更新**: 支持远程配置更新
3. **回滚机制**: 准备回滚方案以防更新失败

## 10. 故障排除

### 10.1 常见问题
- **权限问题**: 确保应用获得必要权限
- **网络问题**: 检查防火墙和代理设置
- **存储问题**: 确保设备有足够的存储空间
- **兼容性问题**: 验证设备API Level兼容性

### 10.2 调试技巧
- 使用Android Studio的调试工具
- 启用WebView调试模式
- 使用ADB进行实时调试
- 查看系统日志分析问题

### 10.3 联系支持
如遇到无法解决的问题，请联系技术支持并提供以下信息：
- 设备型号和Android版本
- 应用版本
- 详细的问题描述
- 相关日志信息