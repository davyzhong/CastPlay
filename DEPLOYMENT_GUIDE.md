# CastPlay 部署指南

## 📋 目录

- [系统要求](#系统要求)
- [开发环境搭建](#开发环境搭建)
- [生产环境部署](#生产环境部署)
- [Docker 部署](#docker-部署)
- [配置说明](#配置说明)
- [常见问题](#常见问题)

---

## 系统要求

### 后端服务

**最低配置**：

- CPU: 2 核
- 内存: 4GB
- 磁盘: 50GB（含文件存储）
- 操作系统: Ubuntu 20.04+ / CentOS 7+ / macOS 10.15+

**推荐配置**：

- CPU: 4 核+
- 内存: 8GB+
- 磁盘: 200GB+ SSD
- 操作系统: Ubuntu 22.04 LTS

**软件依赖**：

- Python 3.10+
- PostgreSQL 13+ / SQLite 3.x
- Redis 6.0+
- LibreOffice 7.0+
- FFmpeg 4.x+
- pdftoppm (poppler-utils)

### 前端管理后台

**开发环境**：

- Node.js 18+
- npm 9+ / yarn 1.22+

**生产环境**：

- Nginx / Apache（静态文件服务）

### Android 播放端

**开发环境**：

- Android Studio 2022+
- JDK 11+
- Android SDK 33

**设备要求**：

- Android 5.0+ (API 21+)
- 推荐 Android 8.0+ (API 26+)
- 2GB+ RAM

---

## 开发环境搭建

### 1. 后端服务搭建

#### 步骤 1：克隆代码

```bash
cd /path/to/workspace
git clone <repository-url> CastPlay
cd CastPlay/castplay-server
```

#### 步骤 2：创建虚拟环境

```bash
# 使用 venv
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 或使用 conda
conda create -n castplay python=3.10
conda activate castplay
```

#### 步骤 3：安装依赖

```bash
pip install -r requirements.txt
```

#### 步骤 4：安装系统依赖

**Ubuntu/Debian**：

```bash
sudo apt update
sudo apt install -y libreoffice ffmpeg poppler-utils redis-server
```

**macOS**：

```bash
brew install libreoffice ffmpeg poppler redis
brew services start redis
```

**CentOS/RHEL**：

```bash
sudo yum install -y libreoffice ffmpeg poppler-utils redis
sudo systemctl start redis
sudo systemctl enable redis
```

#### 步骤 5：配置环境变量

创建 `.env` 文件：

```bash
# .env
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///castplay.db
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
SOCKETIO_MESSAGE_QUEUE=redis://localhost:6379/1
```

#### 步骤 6：初始化数据库

```bash
# 初始化迁移
flask db init

# 生成迁移脚本
flask db migrate -m "Initial migration"

# 应用迁移
flask db upgrade
```

#### 步骤 7：启动服务

**Terminal 1 - Flask 服务**：

```bash
python run.py
```

**Terminal 2 - Celery Worker**：

```bash
celery -A app.tasks.celery_app:celery worker --loglevel=info
```

**验证**：

- Flask: http://localhost:5000/health
- API 文档: http://localhost:5000/api/

---

### 2. 前端管理后台搭建

#### 步骤 1：进入目录

```bash
cd CastPlay/castplay-admin
```

#### 步骤 2：安装依赖

```bash
npm install
# 或
yarn install
```

#### 步骤 3：配置环境变量

创建 `.env.development` 文件：

```bash
VITE_API_BASE_URL=http://localhost:5000/api
VITE_WS_URL=ws://localhost:5000
```

#### 步骤 4：启动开发服务器

```bash
npm run dev
# 或
yarn dev
```

**访问**：http://localhost:3000

---

### 3. Android 应用开发

#### 步骤 1：打开项目

```bash
# 使用 Android Studio 打开
android-app/
```

#### 步骤 2：配置 Gradle

编辑 `app/build.gradle`，修改 API 地址：

```gradle
buildConfigField "String", "API_BASE_URL", '"http://10.0.2.2:5000/api/"'
buildConfigField "String", "WS_URL", '"ws://10.0.2.2:5000/socket.io/"'
```

> 注：`10.0.2.2` 是 Android 模拟器访问宿主机的特殊 IP

#### 步骤 3：同步依赖

Android Studio 会自动同步 Gradle 依赖

#### 步骤 4：运行应用

1. 连接设备或启动模拟器
2. 点击 Run 按钮
3. 选择目标设备

---

## 生产环境部署

### 架构图

```
Internet
   ↓
Nginx (443/80)
   ↓
┌──────────────┬──────────────┐
│ Flask (5000) │ React (静态) │
└──────┬───────┴──────────────┘
       ↓
┌──────┴───────┐
│ Celery Worker│
└──────┬───────┘
       ↓
┌──────┴───────┬──────────────┐
│    Redis     │  PostgreSQL  │
└──────────────┴──────────────┘
```

### 1. 后端生产部署

#### 使用 Gunicorn + Supervisor

**安装 Gunicorn**：

```bash
pip install gunicorn gevent-websocket
```

**创建 Gunicorn 配置**：

```python
# gunicorn_config.py
import multiprocessing

bind = "0.0.0.0:5000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "geventwebsocket.gunicorn.workers.GeventWebSocketWorker"
timeout = 120
keepalive = 5
accesslog = "/var/log/castplay/gunicorn_access.log"
errorlog = "/var/log/castplay/gunicorn_error.log"
loglevel = "info"
```

**创建 Supervisor 配置**：

```ini
# /etc/supervisor/conf.d/castplay.conf

[program:castplay-flask]
command=/path/to/venv/bin/gunicorn -c gunicorn_config.py app:app
directory=/path/to/castplay-server
user=www-data
autostart=true
autorestart=true
stdout_logfile=/var/log/castplay/flask.log
stderr_logfile=/var/log/castplay/flask_error.log

[program:castplay-celery]
command=/path/to/venv/bin/celery -A app.tasks.celery_app:celery worker --loglevel=info
directory=/path/to/castplay-server
user=www-data
autostart=true
autorestart=true
stdout_logfile=/var/log/castplay/celery.log
stderr_logfile=/var/log/castplay/celery_error.log
```

**启动服务**：

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start castplay-flask
sudo supervisorctl start castplay-celery
```

---

#### 配置 Nginx

```nginx
# /etc/nginx/sites-available/castplay

upstream castplay_backend {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name your-domain.com;

    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL 证书配置
    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # 静态文件（前端）
    location / {
        root /path/to/castplay-admin/dist;
        try_files $uri $uri/ /index.html;
    }

    # API 请求
    location /api/ {
        proxy_pass http://castplay_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /socket.io/ {
        proxy_pass http://castplay_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 媒体文件（大文件优化）
    location /storage/ {
        alias /path/to/castplay-server/storage/;
        sendfile on;
        tcp_nopush on;
        tcp_nodelay on;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }

    # 上传大小限制
    client_max_body_size 500M;
}
```

**启用站点**：

```bash
sudo ln -s /etc/nginx/sites-available/castplay /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

#### 配置 PostgreSQL

**创建数据库**：

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE castplay;
CREATE USER castplay_user WITH PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE castplay TO castplay_user;
\q
```

**更新环境变量**：

```bash
DATABASE_URL=postgresql://castplay_user:your-password@localhost/castplay
```

**迁移数据**：

```bash
flask db upgrade
```

---

### 2. 前端生产部署

#### 构建生产版本

```bash
cd castplay-admin

# 配置生产环境变量
cat > .env.production << EOF
VITE_API_BASE_URL=https://your-domain.com/api
VITE_WS_URL=wss://your-domain.com
EOF

# 构建
npm run build
```

**输出目录**：`dist/`

#### 部署到 Nginx

```bash
sudo cp -r dist/* /var/www/castplay-admin/
sudo chown -R www-data:www-data /var/www/castplay-admin/
```

---

### 3. Android APK 打包

#### 生成签名密钥

```bash
keytool -genkey -v -keystore castplay.keystore \
  -alias castplay -keyalg RSA -keysize 2048 -validity 10000
```

#### 配置签名

编辑 `android-app/app/build.gradle`：

```gradle
android {
    signingConfigs {
        release {
            storeFile file("../castplay.keystore")
            storePassword "your-password"
            keyAlias "castplay"
            keyPassword "your-password"
        }
    }

    buildTypes {
        release {
            signingConfig signingConfigs.release
            minifyEnabled true
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'

            buildConfigField "String", "API_BASE_URL", '"https://your-domain.com/api/"'
            buildConfigField "String", "WS_URL", '"wss://your-domain.com/socket.io/"'
        }
    }
}
```

#### 打包 APK

```bash
# 在 Android Studio 中
Build → Generate Signed Bundle / APK → APK → Release
```

**输出路径**：`android-app/app/release/app-release.apk`

---

## Docker 部署

### Docker Compose 配置

创建 `docker-compose.yml`：

```yaml
version: "3.8"

services:
  # PostgreSQL 数据库
  postgres:
    image: postgres:14-alpine
    container_name: castplay-postgres
    environment:
      POSTGRES_DB: castplay
      POSTGRES_USER: castplay_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - castplay-network
    restart: unless-stopped

  # Redis
  redis:
    image: redis:7-alpine
    container_name: castplay-redis
    networks:
      - castplay-network
    restart: unless-stopped

  # Flask 应用
  flask-app:
    build:
      context: ./castplay-server
      dockerfile: Dockerfile
    container_name: castplay-flask
    environment:
      FLASK_ENV: production
      DATABASE_URL: postgresql://castplay_user:${DB_PASSWORD}@postgres/castplay
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/0
      SOCKETIO_MESSAGE_QUEUE: redis://redis:6379/1
    volumes:
      - ./castplay-server/storage:/app/storage
    ports:
      - "5000:5000"
    depends_on:
      - postgres
      - redis
    networks:
      - castplay-network
    restart: unless-stopped

  # Celery Worker
  celery-worker:
    build:
      context: ./castplay-server
      dockerfile: Dockerfile
    container_name: castplay-celery
    command: celery -A app.tasks.celery_app:celery worker --loglevel=info
    environment:
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/0
      DATABASE_URL: postgresql://castplay_user:${DB_PASSWORD}@postgres/castplay
    volumes:
      - ./castplay-server/storage:/app/storage
    depends_on:
      - redis
      - postgres
    networks:
      - castplay-network
    restart: unless-stopped

  # Nginx 反向代理
  nginx:
    image: nginx:alpine
    container_name: castplay-nginx
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./castplay-admin/dist:/usr/share/nginx/html:ro
      - ./castplay-server/storage:/var/www/storage:ro
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - flask-app
    networks:
      - castplay-network
    restart: unless-stopped

volumes:
  postgres_data:

networks:
  castplay-network:
    driver: bridge
```

### Flask Dockerfile

```dockerfile
# castplay-server/Dockerfile
FROM python:3.10-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    libreoffice \
    ffmpeg \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建存储目录
RUN mkdir -p storage/uploads storage/converted storage/thumbnails

EXPOSE 5000

CMD ["gunicorn", "-c", "gunicorn_config.py", "app:app"]
```

### 启动容器

```bash
# 创建 .env 文件
cat > .env << EOF
DB_PASSWORD=your-secure-password
EOF

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 初始化数据库
docker-compose exec flask-app flask db upgrade
```

---

## 配置说明

### 环境变量

| 变量名                   | 说明              | 默认值           | 示例                           |
| ------------------------ | ----------------- | ---------------- | ------------------------------ |
| `FLASK_ENV`              | 运行环境          | development      | production                     |
| `SECRET_KEY`             | Flask 密钥        | -                | random-secret-key              |
| `DATABASE_URL`           | 数据库连接        | sqlite           | postgresql://user:pass@host/db |
| `CELERY_BROKER_URL`      | Celery Broker     | -                | redis://localhost:6379/0       |
| `CELERY_RESULT_BACKEND`  | Celery 结果存储   | -                | redis://localhost:6379/0       |
| `SOCKETIO_MESSAGE_QUEUE` | SocketIO 消息队列 | -                | redis://localhost:6379/1       |
| `CORS_ORIGINS`           | CORS 允许源       | \*               | https://admin.example.com      |
| `LIBREOFFICE_PATH`       | LibreOffice 路径  | /usr/bin/soffice | -                              |
| `FFMPEG_PATH`            | FFmpeg 路径       | /usr/bin/ffmpeg  | -                              |

### 性能调优

#### Gunicorn Worker 数量

```python
workers = (CPU核心数 * 2) + 1
```

#### PostgreSQL 连接池

```python
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True
}
```

#### Redis 持久化

```conf
# redis.conf
save 900 1
save 300 10
save 60 10000
```

---

## 常见问题

### Q1: PPT 转换失败

**问题**：上传 PPT 后状态一直是 processing

**解决**：

1. 检查 LibreOffice 是否安装：`soffice --version`
2. 检查 FFmpeg 是否安装：`ffmpeg -version`
3. 查看 Celery Worker 日志：`supervisorctl tail -f castplay-celery`

### Q2: WebSocket 连接失败

**问题**：Android 无法连接 WebSocket

**解决**：

1. 检查 Nginx 配置是否包含 WebSocket 代理
2. 检查防火墙是否开放端口
3. 确认 URL 协议（ws:// 或 wss://）

### Q3: 文件上传失败

**问题**：上传大文件时报错

**解决**：

1. 增加 Nginx 上传限制：`client_max_body_size 500M;`
2. 增加 Flask 限制：`MAX_CONTENT_LENGTH = 500 * 1024 * 1024`
3. 检查磁盘空间

### Q4: 数据库连接池耗尽

**问题**：高并发下连接池耗尽

**解决**：

```python
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 20,
    'max_overflow': 10
}
```

### Q5: Android 无法下载文件

**问题**：设备无法下载媒体文件

**解决**：

1. 检查网络连接
2. 检查 API URL 配置
3. 检查文件路径权限
4. 查看 Android 日志：`adb logcat | grep CastPlay`

---

## 监控和维护

### 日志管理

**日志位置**：

- Flask: `/var/log/castplay/flask.log`
- Celery: `/var/log/castplay/celery.log`
- Nginx: `/var/log/nginx/access.log`

**日志轮转**（logrotate）：

```bash
# /etc/logrotate.d/castplay
/var/log/castplay/*.log {
    daily
    missingok
    rotate 14
    compress
    notifempty
    create 0640 www-data www-data
}
```

### 备份策略

**数据库备份**：

```bash
# 每日备份脚本
pg_dump castplay > /backup/castplay_$(date +%Y%m%d).sql
```

**文件备份**：

```bash
# 备份存储目录
rsync -avz /path/to/storage/ /backup/storage/
```

### 性能监控

推荐工具：

- **Prometheus + Grafana** - 系统监控
- **Sentry** - 错误追踪
- **New Relic / DataDog** - APM 性能监控

---

**文档版本**：v1.0
**最后更新**：2026-01-29
**维护者**：CastPlay 开发团队
