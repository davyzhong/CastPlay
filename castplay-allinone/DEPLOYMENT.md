# CastPlay All-in-One 部署指南

## 目录
- [系统要求](#系统要求)
- [快速开始](#快速开始)
- [Docker 部署](#docker-部署)
- [手动部署](#手动部署)
- [生产环境配置](#生产环境配置)
- [备份与恢复](#备份与恢复)
- [故障排除](#故障排除)

---

## 系统要求

### 最低配置
- CPU: 2 核
- 内存: 2GB
- 磁盘: 20GB
- 操作系统: Linux/macOS/Windows

### 推荐配置
- CPU: 4 核
- 内存: 4GB
- 磁盘: 50GB SSD
- 操作系统: Linux (Ubuntu 20.04+)

### 软件依赖
- Python 3.12+
- Docker 20.10+ (Docker 部署)
- LibreOffice (PPT 转换)
- FFmpeg (视频处理)

---

## 快速开始

### 使用 Docker Compose（推荐）

```bash
# 1. 克隆仓库
git clone <repository-url>
cd castplay-allinone

# 2. 启动服务
docker-compose up -d

# 3. 初始化数据库
docker-compose exec castplay python scripts/init_db.py

# 4. 访问应用
# API 文档: http://localhost:8000/docs
# 前端应用: http://localhost:8000
```

默认管理员账号：
- 用户名: `admin`
- 密码: `admin123`

---

## Docker 部署

### 构建镜像

```bash
docker build -t castplay:latest .
```

### 运行容器

```bash
docker run -d \
  --name castplay \
  -p 8000:8000 \
  -v castplay-data:/app/data \
  -e SECRET_KEY=your-secret-key-here \
  castplay:latest
```

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `SECRET_KEY` | `your-secret-key-change-in-production` | JWT 签名密钥 |
| `DATABASE_PATH` | `data/castplay.db` | 数据库文件路径 |
| `DEBUG` | `false` | 调试模式 |
| `NUM_WORKERS` | `3` | 后台任务工作线程数 |
| `MAX_FILE_SIZE` | `524288000` | 最大上传文件大小 (字节) |

---

## 手动部署

### 1. 安装依赖

#### Ubuntu/Debian
```bash
# 安装系统依赖
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip
sudo apt-get install -y libreoffice ffmpeg imagemagick poppler-utils pdftoppm

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate
```

#### macOS
```bash
# 使用 Homebrew
brew install python3 libreoffice ffmpeg poppler

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate
```

#### Windows
```powershell
# 使用 Chocolatey
choco install python libreoffice ffmpeg poppler

# 创建虚拟环境
python -m venv venv
venv\Scripts\activate
```

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 3. 初始化数据库

```bash
python scripts/init_db.py
```

### 4. 启动服务

```bash
# 开发模式
python scripts/run.py

# 或使用 uvicorn（生产模式）
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 生产环境配置

### 1. 配置文件

创建 `.env` 文件：

```env
# 数据库
DATABASE_PATH=/var/lib/castplay/castplay.db

# 安全
SECRET_KEY=your-very-secret-key-change-this
ACCESS_TOKEN_EXPIRE_MINUTES=60

# 应用配置
DEBUG=false
NUM_WORKERS=4
MAX_FILE_SIZE=524288000  # 500MB

# 服务器
HOST=0.0.0.0
PORT=8000
```

### 2. 使用 systemd 管理

创建服务文件 `/etc/systemd/system/castplay.service`：

```ini
[Unit]
Description=CastPlay Digital Signage Server
After=network.target

[Service]
Type=simple
User=castplay
WorkingDirectory=/opt/castplay
Environment="PATH=/opt/castplay/venv/bin"
ExecStart=/opt/castplay/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable castplay
sudo systemctl start castplay
sudo systemctl status castplay
```

### 3. Nginx 反向代理

```nginx
upstream castplay {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name castplay.example.com;

    # API
    location /api/ {
        proxy_pass http://castplay;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 静态文件
    location /static/ {
        alias /opt/castplay/data/uploads/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://castplay;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # 前端
    location / {
        root /opt/castplay/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
}
```

### 4. SSL 配置

使用 Let's Encrypt 获取免费证书：

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d castplay.example.com
```

---

## 备份与恢复

### 数据库备份

```bash
# 手动备份
python scripts/backup_db.py

# 或直接复制数据库文件
cp data/castplay.db data/backups/castplay_$(date +%Y%m%d_%H%M%S).db
```

### 定时备份 (crontab)

```bash
# 编辑 crontab
crontab -e

# 添加每天凌晨 2 点备份
0 2 * * * /opt/castplay/scripts/backup_db.py >> /var/log/castplay_backup.log 2>&1
```

### 数据库恢复

```bash
# 停止服务
systemctl stop castplay

# 恢复数据库
cp data/backups/castplay_backup.db data/castplay.db

# 重启服务
systemctl start castplay
```

### 完整备份（包含上传文件）

```bash
# 创建备份目录
BACKUP_DIR="/backup/castplay_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# 备份数据库
cp data/castplay.db "$BACKUP_DIR/"

# 备份上传文件
cp -r data/uploads "$BACKUP_DIR/"
cp -r data/converted "$BACKUP_DIR/"
cp -r data/thumbnails "$BACKUP_DIR/"

# 压缩
tar -czf "$BACKUP_DIR.tar.gz" -C /backup "$(basename $BACKUP_DIR)"
rm -rf "$BACKUP_DIR"
```

---

## 故障排除

### 服务无法启动

```bash
# 查看日志
docker-compose logs castplay

# 或手动运行查看错误
python scripts/run.py
```

### 数据库被锁定

```bash
# 删除 WAL 文件
rm data/castplay.db-shm data/castplay.db-wal

# 重启服务
docker-compose restart castplay
```

### PPT 转换失败

```bash
# 检查 LibreOffice 是否安装
libreoffice --version

# 检查 pdftoppm 是否安装
pdftoppm --version

# 测试转换
libreoffice --headless --convert-to pdf test.pptx
```

### 端口被占用

```bash
# 查找占用端口的进程
lsof -i :8000

# 或
netstat -tlnp | grep :8000

# 修改端口
export PORT=8001
python scripts/run.py
```

### 内存不足

```bash
# 减少工作线程数
export NUM_WORKERS=2
python scripts/run.py

# 或增加 swap 空间
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## 监控

### 健康检查

```bash
# 检查 API 健康状态
curl http://localhost:8000/health

# 预期响应
# {"status": "ok", "version": "2.0.0"}
```

### 日志查看

```bash
# Docker 日志
docker-compose logs -f castplay

# systemd 日志
journalctl -u castplay -f
```

### 性能监控

```bash
# 检查数据库大小
ls -lh data/castplay.db

# 检查磁盘使用
df -h

# 检查内存使用
free -h
```

---

## 更新

### Docker 更新

```bash
# 拉取最新代码
git pull

# 重新构建镜像
docker-compose build

# 重启服务
docker-compose up -d
```

### 手动更新

```bash
# 备份数据库
python scripts/backup_db.py

# 拉取最新代码
git pull

# 更新依赖
pip install -r requirements.txt --upgrade

# 重启服务
systemctl restart castplay
```

---

## 支持

如有问题，请查看：
- API 文档: http://your-server/docs
- GitHub Issues: <repository-url>/issues
