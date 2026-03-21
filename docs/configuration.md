# CastPlay 配置参考文档

本文档详细介绍 CastPlay 系统的所有配置选项。

## 环境变量配置

CastPlay 使用 `.env` 文件进行配置。创建项目根目录下的 `.env` 文件：

```bash
cp .env.example .env
```

### 应用配置

| 变量名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `APP_NAME` | string | "CastPlay All-in-One" | 应用名称 |
| `APP_VERSION` | string | "2.0.0" | 应用版本 |
| `DEBUG` | bool | false | 调试模式 |
| `ENVIRONMENT` | string | "development" | 运行环境：`development` / `staging` / `production` |

**示例：**

```bash
APP_NAME=CastPlay
APP_VERSION=2.0.0
DEBUG=false
ENVIRONMENT=production
```

---

### 服务器配置

| 变量名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `HOST` | string | "0.0.0.0" | 服务器监听地址 |
| `PORT` | int | 8000 | 服务器监听端口 |

**示例：**

```bash
HOST=0.0.0.0
PORT=8000
```

---

### 数据库配置

| 变量名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `DATABASE_PATH` | string | "data/castplay.db" | SQLite 数据库文件路径 |

**示例：**

```bash
DATABASE_PATH=data/castplay.db
```

**注意**：路径相对于项目根目录。

---

### 文件存储配置

| 变量名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `DATA_DIR` | path | "data" | 数据目录 |
| `UPLOADS_DIR` | path | "data/uploads" | 上传文件存储目录 |
| `CONVERTED_DIR` | path | "data/converted" | 转换后文件存储目录 |
| `THUMBNAILS_DIR` | path | "data/thumbnails" | 缩略图存储目录 |
| `BACKUPS_DIR` | path | "backups" | 数据库备份目录 |

**示例：**

```bash
DATA_DIR=data
UPLOADS_DIR=data/uploads
CONVERTED_DIR=data/converted
THUMBNAILS_DIR=data/thumbnails
BACKUPS_DIR=backups
```

---

### 文件上传限制

| 变量名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `MAX_FILE_SIZE` | int | 524288000 (500MB) | 最大文件大小（字节） |
| `ALLOWED_IMAGE_TYPES` | list | ["jpg","jpeg","png","gif","bmp"] | 允许的图片格式 |
| `ALLOWED_VIDEO_TYPES` | list | ["mp4","avi","mov","mkv","flv"] | 允许的视频格式 |
| `ALLOWED_PPT_TYPES` | list | ["ppt","pptx"] | 允许的 PPT 格式 |

**示例：**

```bash
MAX_FILE_SIZE=524288000
ALLOWED_IMAGE_TYPES=["jpg","jpeg","png","gif","bmp"]
ALLOWED_VIDEO_TYPES=["mp4","avi","mov","mkv","flv"]
ALLOWED_PPT_TYPES=["ppt","pptx"]
```

---

### 认证配置

| 变量名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `SECRET_KEY` | string | (自动生成) | JWT 签名密钥 |
| `ALGORITHM` | string | "HS256" | JWT 算法 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | int | 604800 (7天) | Token 过期时间（分钟） |
| `DEFAULT_ADMIN_USERNAME` | string | "admin" | 默认管理员用户名 |
| `DEFAULT_ADMIN_PASSWORD` | string | (自动生成) | 默认管理员密码 |

**SECRET_KEY 重要说明：**

- **生产环境**：必须设置强随机密钥（至少 32 字符）
- **开发环境**：自动生成并保存到 `data/.dev_secret_key`

**示例：**

```bash
SECRET_KEY=your-super-secret-key-at-least-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=604800
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=your_secure_password
```

---

### WebSocket 配置

| 变量名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `WS_PING_INTERVAL` | int | 30 | 心跳间隔（秒） |
| `WS_PING_TIMEOUT` | int | 10 | 心跳超时（秒） |

**示例：**

```bash
WS_PING_INTERVAL=30
WS_PING_TIMEOUT=10
```

---

### 后台任务配置

| 变量名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `NUM_WORKERS` | int | 3 | 后台任务线程数 |
| `TASK_TIMEOUT` | int | 600 | 任务超时时间（秒） |

**示例：**

```bash
NUM_WORKERS=3
TASK_TIMEOUT=600
```

---

### CORS 配置

| 变量名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `CORS_ORIGINS` | list | ["*","null"] | CORS 允许的来源 |
| `CORS_ALLOW_CREDENTIALS` | bool | true | 是否允许携带凭证 |

**CORS_ORIGINS 说明：**

- **开发环境**：默认为 `["*","null"]`，允许所有来源
- **生产环境**：必须配置具体的域名列表

**示例（生产环境）：**

```bash
CORS_ORIGINS=["http://localhost:3000","http://192.168.1.100:3000"]
CORS_ALLOW_CREDENTIALS=true
```

---

### 设备注册配置

| 变量名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `REGISTRATION_CODE` | string | null | 设备注册验证码（构建时嵌入） |

**示例：**

```bash
REGISTRATION_CODE=ABC123XYZ
```

---

### 速率限制配置

| 变量名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `RATE_LIMIT_ENABLED` | bool | true | 是否启用速率限制 |
| `RATE_LIMIT_LOGIN` | string | "5/minute" | 登录请求限制 |
| `RATE_LIMIT_API` | string | "100/minute" | API 请求限制 |

**示例：**

```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_LOGIN=5/minute
RATE_LIMIT_API=100/minute
```

---

## 完整配置示例

### 开发环境 (.env)

```bash
# 应用配置
APP_NAME=CastPlay Dev
DEBUG=true
ENVIRONMENT=development

# 服务器配置
HOST=0.0.0.0
PORT=8000

# 数据库配置
DATABASE_PATH=data/castplay.db

# 文件存储配置
DATA_DIR=data
UPLOADS_DIR=data/uploads
CONVERTED_DIR=data/converted
THUMBNAILS_DIR=data/thumbnails
BACKUPS_DIR=backups

# 文件上传限制
MAX_FILE_SIZE=524288000

# JWT 配置
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# CORS 配置
CORS_ORIGINS=["*","null"]

# 速率限制
RATE_LIMIT_ENABLED=false
```

### 生产环境 (.env)

```bash
# 应用配置
APP_NAME=CastPlay
DEBUG=false
ENVIRONMENT=production

# 服务器配置
HOST=0.0.0.0
PORT=8000

# 数据库配置
DATABASE_PATH=/var/lib/castplay/castplay.db

# 文件存储配置
DATA_DIR=/var/lib/castplay
UPLOADS_DIR=/var/lib/castplay/uploads
CONVERTED_DIR=/var/lib/castplay/converted
THUMBNAILS_DIR=/var/lib/castplay/thumbnails
BACKUPS_DIR=/var/lib/castplay/backups

# 文件上传限制
MAX_FILE_SIZE=524288000

# JWT 配置（必须设置）
SECRET_KEY=your-super-secret-key-at-least-32-characters-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=604800
DEFAULT_ADMIN_PASSWORD=your_secure_admin_password

# CORS 配置（必须配置具体域名）
CORS_ORIGINS=["https://admin.example.com","https://castplay.example.com"]
CORS_ALLOW_CREDENTIALS=true

# 设备注册配置
REGISTRATION_CODE=YOUR_BUILD_TIME_REGISTRATION_CODE

# 速率限制
RATE_LIMIT_ENABLED=true
RATE_LIMIT_LOGIN=5/minute
RATE_LIMIT_API=100/minute
```

---

## 配置文件优先级

配置按以下优先级（从高到低）：

1. **环境变量** - 操作系统环境变量
2. **.env 文件** - 项目根目录下的 .env 文件
3. **默认值** - 代码中定义的默认值

---

## 配置验证

启动时，系统会验证生产环境配置：

```python
warnings = settings.validate_production_config()
if warnings:
    for warning in warnings:
        logger.warning(warning)
```

**验证项目：**

- `SECRET_KEY` 必须设置且长度 >= 32
- `CORS_ORIGINS` 不建议使用 `["*"]`

---

## 运行时修改配置

部分配置支持运行时修改：

| 配置项 | 修改方式 | 生效时间 |
|--------|----------|----------|
| CORS 配置 | 修改 .env 后重启 | 重启后生效 |
| 速率限制 | 修改 .env 后重启 | 重启后生效 |
| 文件上传限制 | 修改 .env 后重启 | 重启后生效 |

---

## 相关文档

- [API 参考文档](./api/README.md)
- [WebSocket 协议文档](./api/websocket.md)
- [部署指南](./deployment/guide.md)
