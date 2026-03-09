# CastPlay All-in-One v2.0 部署和使用指南

> 🚀 从零开始部署到生产使用
> **版本**: v2.0.1 | **更新时间**: 2026-03-07

---

## 📋 目录

1. [快速开始](#1-快速开始)
2. [系统要求](#2-系统要求)
3. [安装步骤](#3-安装步骤)
4. [配置说明](#4-配置说明)
5. [启动服务](#5-启动服务)
6. [管理后台使用](#6-管理后台使用)
7. [播放端部署](#7-播放端部署)
8. [运维管理](#8-运维管理)
9. [故障排查](#9-故障排查)
10. [最佳实践](#10-最佳实践)

---

## 1. 快速开始

### 5 分钟快速部署

```bash
# 1. 克隆项目
git clone https://github.com/your-org/castplay-allinone.git
cd castplay-allinone

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 初始化数据库
python scripts/init_db.py

# 5. 启动服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 6. 访问管理后台
# 浏览器打开：http://localhost:8000
# 默认账号：admin / (自动生成的密码)
```

**恭喜！您已完成部署！** 🎉

---

## 2. 系统要求

### 2.1 最低配置

| 组件     | 要求        | 说明            |
| -------- | ----------- | --------------- |
| **CPU**  | 双核 2.0GHz | 支持 <20 设备   |
| **内存** | 2GB RAM     | 基础运行        |
| **存储** | 10GB SSD    | 系统 + 媒体缓存 |
| **网络** | 100Mbps     | 内网部署        |

### 2.2 推荐配置

| 组件     | 要求         | 说明          |
| -------- | ------------ | ------------- |
| **CPU**  | 四核 2.5GHz+ | 支持 <50 设备 |
| **内存** | 4GB RAM      | 流畅运行      |
| **存储** | 50GB+ SSD    | 大量媒体文件  |
| **网络** | 1Gbps        | 千兆内网      |

### 2.3 软件依赖

**必须安装**:

- ✅ Python 3.10+ (推荐 3.12)
- ✅ pip (Python 包管理器)
- ✅ git (版本控制)

**可选安装**:

- 🔧 LibreOffice 7.0+ (PPT 转换)
- 🔧 ffmpeg 4.0+ (视频处理)
- 🔧 Node.js 18+ (前端开发)

### 2.4 支持的操作系统

| 系统        | 版本         | 状态        |
| ----------- | ------------ | ----------- |
| **Ubuntu**  | 20.04, 22.04 | ✅ 完全支持 |
| **Debian**  | 10, 11       | ✅ 完全支持 |
| **CentOS**  | 7, 8         | ✅ 支持     |
| **macOS**   | 11+          | ✅ 支持     |
| **Windows** | 10, 11       | ⚠️ 基础支持 |
| **Docker**  | Any          | ✅ 推荐     |

---

## 3. 安装步骤

### 3.1 Ubuntu/Debian 安装

#### Step 1: 安装系统依赖

```bash
# 更新软件包列表
sudo apt update && sudo apt upgrade -y

# 安装 Python 和依赖
sudo apt install -y python3.12 python3.12-venv python3-pip git

# 安装 LibreOffice（PPT 转换）
sudo apt install -y libreoffice

# 安装 ffmpeg（视频处理）
sudo apt install -y ffmpeg

# 验证安装
python3 --version  # 应显示 Python 3.12.x
git --version      # 应显示 git version 2.x
```

#### Step 2: 克隆项目

```bash
# 创建应用目录
mkdir -p /opt/castplay
cd /opt/castplay

# 克隆代码（或复制本地项目）
git clone https://github.com/your-org/castplay-allinone.git .
# 或从本地复制
# cp -r /path/to/castplay-allinone/* /opt/castplay/
```

#### Step 3: 创建虚拟环境

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 验证虚拟环境已激活
which python  # 应显示 /opt/castplay/venv/bin/python
```

#### Step 4: 安装 Python 依赖

```bash
# 升级 pip
pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt

# 验证安装
pip list | grep -i fastapi  # 应显示 fastapi
```

#### Step 5: 初始化数据库

```bash
# 运行初始化脚本
python scripts/init_db.py

# 输出示例:
# ℹ️  管理员账户：admin
# ℹ️  管理员密码：5-GU6Cibs4Qq6mPvJLAaQA
# Database initialized at data/castplay.db
```

**重要**: 请保存管理员密码！

---

### 3.2 macOS 安装

```bash
# 1. 安装 Homebrew（如果未安装）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. 安装依赖
brew install python@3.12 git libreoffice ffmpeg

# 3. 克隆项目
git clone https://github.com/your-org/castplay-allinone.git
cd castplay-allinone

# 4. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 5. 安装依赖
pip install -r requirements.txt

# 6. 初始化数据库
python scripts/init_db.py
```

---

### 3.3 Docker 部署（推荐）⭐

#### Dockerfile

```dockerfile
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    libreoffice \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# 启动命令
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### docker-compose.yml

```yaml
version: "3.8"

services:
  castplay:
    build: .
    container_name: castplay-server
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      # 持久化数据
      - ./data:/app/data
      - ./backups:/app/backups
      - ./logs:/app/logs
    environment:
      - ENVIRONMENT=production
      - SECRET_KEY=${SECRET_KEY:-change-me-to-random-string}
      - DEFAULT_ADMIN_PASSWORD=${ADMIN_PASSWORD:-admin123}
      - CORS_ORIGINS=["http://your-domain.com"]
    networks:
      - castplay-network

networks:
  castplay-network:
    driver: bridge
```

#### 启动 Docker

```bash
# 1. 构建镜像
docker-compose build

# 2. 启动服务
docker-compose up -d

# 3. 查看日志
docker-compose logs -f

# 4. 停止服务
docker-compose down

# 5. 重启服务
docker-compose restart
```

**优势**:

- ✅ 环境隔离，无依赖冲突
- ✅ 一键部署，便于迁移
- ✅ 自动重启，高可用
- ✅ 资源限制，安全可控

---

## 4. 配置说明

### 4.1 配置文件位置

```
castplay-allinone/
├── .env                  # 环境变量配置（自动生成）
├── .env.example          # 配置模板
└── app/
    └── config.py         # 配置加载逻辑
```

### 4.2 完整配置示例

```bash
# .env 文件内容

# ==================== 应用配置 ====================
APP_NAME="CastPlay All-in-One"
DEBUG=false                          # 生产环境必须为 false
ENVIRONMENT=production               # development | staging | production

# ==================== 服务器配置 ====================
HOST=0.0.0.0                         # 监听地址
PORT=8000                            # 监听端口

# ==================== 数据库配置 ====================
DATABASE_PATH=data/castplay.db       # SQLite 数据库路径

# ==================== 文件存储 ====================
DATA_DIR=data                        # 数据根目录
UPLOADS_DIR=data/uploads             # 上传文件目录
CONVERTED_DIR=data/converted         # 转换后文件目录
THUMBNAILS_DIR=data/thumbnails       # 缩略图目录
BACKUPS_DIR=backups                  # 备份目录

# ==================== 安全配置 ====================
# 生产环境必须设置强随机密钥（至少 32 字符）
SECRET_KEY=your-super-secret-key-minimum-32-chars

# 管理员密码（生产环境必须修改）
DEFAULT_ADMIN_PASSWORD=SecurePassw0rd!@#

# JWT Token 过期时间（分钟）
ACCESS_TOKEN_EXPIRE_MINUTES=10080    # 7 天

# ==================== CORS 配置 ====================
# 生产环境必须配置具体域名，不要使用 *
CORS_ORIGINS=["https://your-domain.com","https://admin.your-domain.com"]

# ==================== 速率限制 ====================
RATE_LIMIT_ENABLED=true              # 启用限流
RATE_LIMIT_LOGIN=5/minute            # 登录限流
RATE_LIMIT_API=100/minute            # API 限流

# ==================== WebSocket 配置 ====================
WS_PING_INTERVAL=30                  # 心跳间隔（秒）
WS_PING_TIMEOUT=10                   # 超时时间（秒）

# ==================== 后台任务配置 ====================
NUM_WORKERS=3                        # Worker 线程数
TASK_TIMEOUT=600                     # 任务超时（秒）

# ==================== 文件上传限制 ====================
MAX_FILE_SIZE=524288000              # 500MB
ALLOWED_IMAGE_TYPES=jpg,jpeg,png,gif,bmp
ALLOWED_VIDEO_TYPES=mp4,avi,mov,mkv,flv
ALLOWED_PPT_TYPES=ppt,pptx
```

### 4.3 生成安全密钥

```bash
# 方法 1: 使用 Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 方法 2: 使用 OpenSSL
openssl rand -hex 32

# 方法 3: 使用 /dev/urandom
head -c 32 /dev/urandom | base64
```

**输出示例**: `xK9mP2nL5qR8tW3vY6zB0cD4eF7gH1iJ`

将此值复制到 `.env` 的 `SECRET_KEY` 字段。

### 4.4 生产环境配置检查清单

在上线前，请确保完成以下配置：

- [ ] `DEBUG=false`
- [ ] `ENVIRONMENT=production`
- [ ] `SECRET_KEY` 已设置为强随机字符串（≥32 字符）
- [ ] `DEFAULT_ADMIN_PASSWORD` 已修改为强密码
- [ ] `CORS_ORIGINS` 已配置具体域名（不是 `*`）
- [ ] 数据库目录有写入权限
- [ ] 防火墙已开放 8000 端口
- [ ] 已配置 HTTPS（如果使用）
- [ ] 日志目录可写
- [ ] 备份策略已配置

---

## 5. 启动服务

### 5.1 开发环境启动

```bash
# 1. 激活虚拟环境
source venv/bin/activate

# 2. 启动开发服务器（自动重载）
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 3. 验证启动
curl http://localhost:8000/api/health
# 应返回：{"status":"ok"}
```

**访问地址**:

- 🌐 管理后台：http://localhost:8000/
- 📖 API 文档：http://localhost:8000/docs
- 📖 ReDoc: http://localhost:8000/redoc

### 5.2 生产环境启动

#### 方式一：直接启动

```bash
# 1. 激活虚拟环境
source venv/bin/activate

# 2. 启动服务（不自动重载）
python -m uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --no-access-log
```

#### 方式二：systemd 服务（推荐）⭐

创建 systemd 服务文件：

```ini
# /etc/systemd/system/castplay.service
[Unit]
Description=CastPlay All-in-One Server
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/castplay
Environment="PATH=/opt/castplay/venv/bin"
ExecStart=/opt/castplay/venv/bin/python -m uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4
Restart=always
RestartSec=10

# 日志
StandardOutput=journal
StandardError=journal
SyslogIdentifier=castplay

[Install]
WantedBy=multi-user.target
```

**启动服务**:

```bash
# 1. 重新加载 systemd
sudo systemctl daemon-reload

# 2. 启动服务
sudo systemctl start castplay

# 3. 设置开机自启
sudo systemctl enable castplay

# 4. 查看状态
sudo systemctl status castplay

# 5. 查看日志
sudo journalctl -u castplay -f

# 6. 重启服务
sudo systemctl restart castplay

# 7. 停止服务
sudo systemctl stop castplay
```

#### 方式三：Docker Compose

```bash
# 启动
docker-compose up -d

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 重启
docker-compose restart

# 停止
docker-compose down
```

### 5.3 反向代理配置

#### Nginx 配置

```nginx
# /etc/nginx/sites-available/castplay
server {
    listen 80;
    server_name your-domain.com;

    # 重定向到 HTTPS（可选）
    # return 301 https://$server_name$request_uri;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 静态文件缓存（可选）
    location /static {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

**启用配置**:

```bash
# 1. 创建软链接
sudo ln -s /etc/nginx/sites-available/castplay /etc/nginx/sites-enabled/

# 2. 测试配置
sudo nginx -t

# 3. 重启 Nginx
sudo systemctl restart nginx
```

#### HTTPS 配置（Let's Encrypt）

```bash
# 1. 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 2. 获取证书
sudo certbot --nginx -d your-domain.com

# 3. 自动续期
sudo certbot renew --dry-run
```

---

## 6. 管理后台使用

### 6.1 首次登录

1. **访问管理后台**

   ```
   http://localhost:8000/
   ```

2. **使用默认账号登录**

   - 用户名：`admin`
   - 密码：启动时显示的随机密码（见 `.env` 文件或启动日志）

3. **修改密码**（强烈建议！）
   - 点击右上角用户头像
   - 选择"设置"
   - 修改密码并保存

### 6.2 功能模块介绍

#### 仪表板（Dashboard）

**功能**:

- 📊 总览统计（设备数、媒体数、播放列表数）
- 📈 实时状态监控
- 🔔 最近活动日志

**操作**:

```
/ → 默认首页
```

#### 设备管理（Devices）

**功能**:

- ➕ 注册新设备
- ✏️ 编辑设备信息
- 🗑️ 删除设备
- 🔗 分配播放列表
- 📱 查看设备状态

**操作步骤**:

1. **注册设备**

   ```
   设备管理 → 创建设备 → 填写信息 → 提交
   ```

   - `device_id`: 唯一标识（如 `web-player-001`）
   - `name`: 设备名称（如 "前台显示屏"）
   - `device_type`: `web_browser`, `android_app`, `ios_app`

2. **分配播放列表**

   ```
   设备详情 → 分配播放列表 → 选择列表 → 确认
   ```

3. **查看设备状态**
   - 在线/离线状态
   - 最后心跳时间
   - 当前播放内容

#### 媒体库（Media Library）

**功能**:

- ⬆️ 上传媒体文件
- 📁 分类管理
- 🔍 搜索过滤
- ✏️ 编辑元数据
- 🗑️ 删除文件

**上传流程**:

1. **点击"上传媒体"**
2. **选择文件**（支持拖拽）

   - 图片：JPG, PNG, GIF, BMP
   - 视频：MP4, AVI, MOV, MKV, FLV
   - PPT: PPT, PPTX（自动转换）

3. **填写信息**

   - 标题（可选）
   - 描述（可选）
   - 播放时长（默认 30 秒）

4. **提交上传**
   - 大文件会显示进度条
   - PPT 会自动后台转换

**批量操作**:

- 多选删除
- 批量上传（最多 50 个）

#### 播放列表（Playlists）

**功能**:

- ➕ 创建播放列表
- ✏️ 编辑列表信息
- ➕ 添加媒体项
- 🔄 调整播放顺序
- 🗑️ 删除列表

**创建流程**:

1. **创建播放列表**

   ```
   播放列表 → 创建播放列表 → 填写名称和描述
   ```

2. **添加媒体**

   ```
   播放列表详情 → 添加媒体 → 从媒体库选择
   ```

   - 支持单选和多选
   - 可设置每个媒体的播放时长

3. **调整顺序**

   ```
   拖拽媒体卡片 → 释放到新位置 → 自动保存
   ```

4. **预览播放**
   ```
   点击"预览"按钮 → 模拟播放效果
   ```

**批量操作**:

- 批量添加媒体（最多 50 个）
- 一键清空列表
- 复制到其他列表

### 6.3 快捷操作

**键盘快捷键**:

- `Ctrl + K`: 全局搜索
- `Ctrl + N`: 新建（根据页面不同而不同）
- `Delete`: 删除选中项
- `Esc`: 关闭弹窗

**批量操作技巧**:

- `Shift + 点击`: 连续多选
- `Ctrl + 点击`: 不连续多选
- `Ctrl + A`: 全选当前页

---

## 7. 播放端部署

### 7.1 Web 播放端

**适用场景**:

- ✅ 智能电视
- ✅ 电脑显示器
- ✅ 投影仪
- ✅ 任何带浏览器的设备

**部署步骤**:

1. **获取播放端 URL**

   ```
   http://服务器 IP:8000/player.html?device_id=YOUR_DEVICE_ID
   ```

2. **在播放设备上打开浏览器**

   - Chrome / Firefox / Edge / Safari
   - 建议使用最新版本的浏览器

3. **输入播放端 URL**

   - 替换 `YOUR_DEVICE_ID` 为实际设备 ID
   - 按回车访问

4. **全屏播放**（推荐）
   - Windows/Linux: `F11`
   - macOS: `Ctrl + Cmd + F`
   - 或点击播放器右上角的全屏按钮

**示例**:

```
http://192.168.1.100:8000/player.html?device_id=lobby-display-01
```

**自动启动**（可选）:

创建启动脚本 `start_player.sh`:

```bash
#!/bin/bash
# 等待网络就绪
sleep 10

# 打开浏览器全屏播放
google-chrome --kiosk --autoplay-policy=no-user-gesture-required \
  "http://192.168.1.100:8000/player.html?device_id=lobby-display-01"
```

添加到开机启动:

```bash
chmod +x start_player.sh
sudo nano /etc/rc.local
# 在 exit 0 之前添加:
# /path/to/start_player.sh &
```

### 7.2 Android 播放端

**适用场景**:

- ✅ Android 电视盒
- ✅ Android 平板
- ✅ Android 广告机

**安装步骤**:

1. **下载 APK**

   ```
   从 releases 页面下载最新版本：castplay-player-android.apk
   ```

2. **安装 APK**

   ```
   设置 → 安全 → 未知来源 → 允许安装
   然后打开 APK 文件安装
   ```

3. **配置播放器**

   - 打开 CastPlay Player 应用
   - 输入服务器地址：`http://服务器 IP:8000`
   - 输入设备 ID: `YOUR_DEVICE_ID`
   - 点击"连接"

4. **设置开机自启**
   ```
   设置 → 应用 → CastPlay Player → 开机自启 → 开启
   ```

### 7.3 iOS 播放端

**适用场景**:

- ✅ iPad
- ✅ iPhone
- ✅ Apple TV

**安装步骤**:

1. **从 App Store 下载**

   ```
   搜索 "CastPlay Player" 并下载安装
   ```

2. **配置播放器**

   - 打开 CastPlay 应用
   - 输入服务器地址
   - 输入设备 ID
   - 点击"保存"

3. **引导式访问**（防止误触）
   ```
   设置 → 辅助功能 → 引导式访问 → 开启
   连按三次侧边按钮启动
   ```

### 7.4 多屏幕同步

**场景**: 多个屏幕播放相同内容

**方案一：共享播放列表**

1. 创建一个播放列表
2. 分配给多个设备
3. 所有设备自动同步播放

**方案二：手动同步**

1. 所有设备同时打开播放端
2. 管理员发送"强制同步"命令
3. 所有设备立即切换到最新内容

**同步精度**: ±1 秒

---

## 8. 运维管理

### 8.1 日常巡检清单

**每日检查**:

- [ ] 服务是否正常运行
- [ ] CPU/内存使用率是否正常
- [ ] 磁盘空间是否充足
- [ ] 日志是否有异常错误
- [ ] WebSocket 连接是否稳定

**每周检查**:

- [ ] 备份是否成功
- [ ] 数据库性能是否正常
- [ ] 清理过期日志
- [ ] 检查安全更新

**每月检查**:

- [ ] 完整系统备份
- [ ] 性能基准测试
- [ ] 审查访问日志
- [ ] 更新依赖包

### 8.2 监控指标

**关键指标**:

| 指标               | 正常值 | 告警阈值 | 检查方法       |
| ------------------ | ------ | -------- | -------------- |
| **CPU 使用率**     | <50%   | >80%     | `top`          |
| **内存使用率**     | <70%   | >90%     | `free -h`      |
| **磁盘使用率**     | <60%   | >85%     | `df -h`        |
| **响应时间**       | <200ms | >500ms   | 监控工具       |
| **WebSocket 连接** | 稳定   | 频繁断开 | 日志           |
| **数据库大小**     | <10GB  | >50GB    | `du -sh data/` |

**监控脚本**:

```bash
#!/bin/bash
# monitor.sh - 系统健康检查脚本

LOG_FILE="/var/log/castplay_monitor.log"

# CPU
cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
echo "$(date): CPU Usage: ${cpu_usage}%" >> $LOG_FILE

# 内存
mem_usage=$(free | grep Mem | awk '{printf("%.1f", $3/$2 * 100.0)}')
echo "$(date): Memory Usage: ${mem_usage}%" >> $LOG_FILE

# 磁盘
disk_usage=$(df -h / | tail -1 | awk '{print $5}' | cut -d'%' -f1)
echo "$(date): Disk Usage: ${disk_usage}%" >> $LOG_FILE

# 告警
if (( $(echo "$cpu_usage > 80" | bc -l) )); then
    echo "⚠️  WARNING: CPU usage is high: ${cpu_usage}%" >> $LOG_FILE
fi

if (( $(echo "$mem_usage > 90" | bc -l) )); then
    echo "⚠️  WARNING: Memory usage is high: ${mem_usage}%" >> $LOG_FILE
fi

if (( $(echo "$disk_usage > 85" | bc -l) )); then
    echo "⚠️  WARNING: Disk usage is high: ${disk_usage}%" >> $LOG_FILE
fi
```

**定时执行**:

```bash
# 添加到 crontab
crontab -e

# 每 5 分钟执行一次
*/5 * * * * /opt/castplay/scripts/monitor.sh
```

### 8.3 备份策略

#### 数据库备份

**自动备份脚本**:

```bash
#!/bin/bash
# backup_database.sh

BACKUP_DIR="/opt/castplay/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_FILE="/opt/castplay/data/castplay.db"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
cp $DB_FILE $BACKUP_DIR/castplay_$DATE.db

# 压缩备份
cd $BACKUP_DIR
tar -czf castplay_$DATE.tar.gz castplay_$DATE.db
rm castplay_$DATE.db

# 删除 30 天前的备份
find $BACKUP_DIR -name "castplay_*.tar.gz" -mtime +30 -delete

echo "Backup completed: castplay_$DATE.tar.gz"
```

**定时备份**:

```bash
# 每天凌晨 2 点备份
0 2 * * * /opt/castplay/scripts/backup_database.sh
```

**手动备份**:

```bash
# 立即备份
cp data/castplay.db backups/castplay_$(date +%Y%m%d).db
```

#### 媒体文件备份

**增量备份脚本**:

```bash
#!/bin/bash
# backup_media.sh

MEDIA_DIR="/opt/castplay/data/uploads"
BACKUP_DIR="/opt/castplay/backups/media"
DATE=$(date +%Y%m%d)

# 使用 rsync 增量备份
rsync -av --delete $MEDIA_DIR/ $BACKUP_DIR/$DATE/

# 压缩旧备份
cd $BACKUP_DIR
tar -czf media_$(date -d "7 days ago" +%Y%m%d).tar.gz \
  $(date -d "7 days ago" +%Y%m%d)/

echo "Media backup completed"
```

### 8.4 日志管理

**日志位置**:

```
/var/log/castplay/           # systemd 日志
/opt/castplay/logs/          # 应用日志
/opt/castplay/server.log     # 主日志文件
```

**日志轮转配置**:

```ini
# /etc/logrotate.d/castplay
/opt/castplay/logs/*.log {
    daily                    # 每日轮转
    rotate 30                # 保留 30 天
    compress                 # 压缩旧日志
    delaycompress            # 延迟一天压缩
    missingok                # 文件不存在不报错
    notifempty               # 空文件不轮转
    create 0640 www-data adm # 创建新文件的权限
    postrotate
        systemctl reload castplay > /dev/null 2>&1 || true
    endscript
}
```

**查看日志**:

```bash
# 实时查看
tail -f /opt/castplay/server.log

# 查看最近 100 行
tail -n 100 /opt/castplay/server.log

# 搜索错误
grep -i error /opt/castplay/server.log

# 查看今天的日志
cat /opt/castplay/server.log | grep "$(date +%Y-%m-%d)"
```

---

## 9. 故障排查

### 9.1 常见问题速查

#### 问题 1: 服务无法启动

**症状**:

```
Error: Address already in use
```

**原因**: 端口被占用

**解决**:

```bash
# 查看占用端口的进程
lsof -i :8000

# 杀死进程
kill -9 <PID>

# 或修改配置使用其他端口
# 编辑 .env 文件，修改 PORT=8001
```

#### 问题 2: 数据库锁定

**症状**:

```
sqlite3.OperationalError: database is locked
```

**原因**: 并发写入冲突

**解决**:

```bash
# 1. 重启服务
sudo systemctl restart castplay

# 2. 检查 WAL 模式
sqlite3 data/castplay.db "PRAGMA journal_mode;"
# 应返回：wal

# 3. 如果不是 WAL，启用它
sqlite3 data/castplay.db "PRAGMA journal_mode=WAL;"
```

#### 问题 3: WebSocket 频繁断开

**症状**:

```
WebSocket disconnected unexpectedly
```

**原因**: 防火墙或代理超时

**解决**:

```nginx
# Nginx 增加超时配置
location / {
    proxy_read_timeout 300s;
    proxy_send_timeout 300s;
}
```

#### 问题 4: PPT 转换失败

**症状**:

```
PPT conversion failed: Command 'libreoffice' not found
```

**原因**: LibreOffice 未安装

**解决**:

```bash
# Ubuntu/Debian
sudo apt install -y libreoffice

# CentOS/RHEL
sudo yum install -y libreoffice

# macOS
brew install libreoffice
```

#### 问题 5: 跨域错误（CORS）

**症状**:

```
Access to XMLHttpRequest has been blocked by CORS policy
```

**原因**: CORS 配置不正确

**解决**:

```bash
# 编辑 .env 文件
CORS_ORIGINS=["http://your-domain.com"]

# 开发环境可以临时设置为 *
CORS_ORIGINS=["*"]
```

### 9.2 诊断工具

**健康检查脚本**:

```bash
#!/bin/bash
# health_check.sh

echo "=== CastPlay Health Check ==="
echo ""

# 1. 检查服务状态
echo "1. Service Status:"
if systemctl is-active --quiet castplay; then
    echo "   ✅ Service is running"
else
    echo "   ❌ Service is not running"
fi

# 2. 检查端口
echo ""
echo "2. Port Check:"
if netstat -tuln | grep -q ":8000"; then
    echo "   ✅ Port 8000 is listening"
else
    echo "   ❌ Port 8000 is not listening"
fi

# 3. 检查数据库
echo ""
echo "3. Database Check:"
if [ -f "data/castplay.db" ]; then
    echo "   ✅ Database file exists"
else
    echo "   ❌ Database file not found"
fi

# 4. 检查磁盘空间
echo ""
echo "4. Disk Space:"
df -h / | tail -1 | awk '{print "   Used: " $5 " Available: " $4}'

# 5. API 健康检查
echo ""
echo "5. API Health:"
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/health)
if [ "$response" = "200" ]; then
    echo "   ✅ API is healthy (HTTP $response)"
else
    echo "   ❌ API returned HTTP $response"
fi

echo ""
echo "=== Health Check Complete ==="
```

**使用方法**:

```bash
chmod +x health_check.sh
./health_check.sh
```

### 9.3 性能调优

**数据库优化**:

```sql
-- 分析慢查询
sqlite3 data/castplay.db "PRAGMA slow_query_log = ON;"

-- 优化索引
sqlite3 data/castplay.db "ANALYZE;"

-- 清理碎片
sqlite3 data/castplay.db "VACUUM;"
```

**应用优化**:

```bash
# 增加 Worker 数量（多核 CPU）
# 编辑 .env
NUM_WORKERS=4

# 调整连接池大小
# 修改 app/database.py
pool_size=30
max_overflow=50
```

---

## 10. 最佳实践

### 10.1 安全加固

**必做事项**:

1. **修改默认密码**

   ```bash
   # 登录后立即修改管理员密码
   ```

2. **设置强 SECRET_KEY**

   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

3. **配置 CORS 白名单**

   ```bash
   CORS_ORIGINS=["https://your-domain.com"]
   ```

4. **启用 HTTPS**

   ```bash
   sudo certbot --nginx -d your-domain.com
   ```

5. **限制文件上传类型**

   ```bash
   # 已在配置中默认限制
   ALLOWED_IMAGE_TYPES=jpg,jpeg,png,gif,bmp
   ALLOWED_VIDEO_TYPES=mp4,avi,mov,mkv,flv
   ```

6. **定期更新依赖**
   ```bash
   pip list --outdated
   pip install --upgrade package-name
   ```

### 10.2 性能优化

**推荐配置**:

```bash
# .env 生产环境优化
NUM_WORKERS=4              # CPU 核心数
POOL_SIZE=30               # 数据库连接池
MAX_OVERFLOW=50            # 最大溢出
WS_PING_INTERVAL=30        # WebSocket 心跳
CACHE_ENABLED=true         # 启用缓存
```

**前端优化**:

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ["react", "react-dom"],
          router: ["react-router-dom"],
        },
      },
    },
  },
});
```

### 10.3 高可用方案

**主从热备**:

```
主服务器：192.168.1.100:8000
从服务器：192.168.1.101:8000

Nginx 负载均衡:
upstream castplay {
    server 192.168.1.100:8000;
    server 192.168.1.101:8000;
}
```

**数据库同步**:

```bash
# 使用 rsync 定期同步数据库
rsync -avz data/castplay.db backup-server:/opt/castplay/data/
```

### 10.4 扩展建议

**当设备数超过 50 台时**:

1. **升级到 PostgreSQL**

   ```bash
   # 修改 database.py
   SQLALCHEMY_DATABASE_URL = "postgresql://user:pass@localhost/dbname"
   ```

2. **使用 Redis 缓存**

   ```bash
   pip install redis
   ```

3. **分离 Celery 任务队列**

   ```bash
   pip install celery[redis]
   ```

4. **使用 Docker Swarm/K8s**
   ```yaml
   # docker-compose.yml 增加副本
   deploy:
     replicas: 3
   ```

---

## 📖 附录

### A. 端口清单

| 端口 | 用途          | 协议 |
| ---- | ------------- | ---- |
| 8000 | HTTP API      | TCP  |
| 8000 | WebSocket     | TCP  |
| 443  | HTTPS（可选） | TCP  |

### B. 目录结构

```
/opt/castplay/
├── app/                    # 应用代码
├── frontend/               # 前端代码
├── data/                   # 数据目录
│   ├── uploads/           # 上传文件
│   ├── converted/         # 转换文件
│   ├── thumbnails/        # 缩略图
│   └── castplay.db        # SQLite 数据库
├── backups/               # 备份目录
├── logs/                  # 日志目录
├── scripts/               # 脚本工具
├── venv/                  # 虚拟环境
└── .env                   # 配置文件
```

### C. 常用命令速查

```bash
# 启动服务
sudo systemctl start castplay

# 停止服务
sudo systemctl stop castplay

# 重启服务
sudo systemctl restart castplay

# 查看状态
sudo systemctl status castplay

# 查看日志
sudo journalctl -u castplay -f

# 备份数据库
cp data/castplay.db backups/

# 进入虚拟环境
source venv/bin/activate

# 更新依赖
pip install -r requirements.txt --upgrade

# 运行测试
pytest tests/ -v
```

### D. 获取帮助

**遇到问题？**

1. **查看文档**

   - [项目架构说明书](./PROJECT_ARCHITECTURE.md)
   - [API 文档](http://localhost:8000/docs)

2. **查看日志**

   ```bash
   sudo journalctl -u castplay -n 100
   ```

3. **运行健康检查**

   ```bash
   ./scripts/health_check.sh
   ```

4. **提交 Issue**
   - GitHub Issues 页面

---

**文档版本**: v2.0.1
**最后更新**: 2026-03-07
**维护者**: CastPlay Team
