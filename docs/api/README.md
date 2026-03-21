# CastPlay API 文档

本文档详细介绍 CastPlay 系统的所有 REST API 端点。

## 基础信息

| 属性 | 值 |
|------|-----|
| Base URL | `http://{host}:8000` |
| 认证方式 | Bearer Token (JWT) |
| 认证头 | `Authorization: Bearer <token>` |
| 内容类型 | `application/json` |
| API 文档 | `http://{host}:8000/docs` (Swagger UI) |

## 认证 API

### 登录

获取访问令牌。

```
POST /api/auth/login
```

**请求体：**

```json
{
  "username": "admin",
  "password": "your_password"
}
```

**响应 (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 604800
}
```

**错误响应 (401 Unauthorized):**

```json
{
  "detail": "用户名或密码错误"
}
```

---

### 注册用户

创建新用户账号。

```
POST /api/auth/register
```

**请求体：**

```json
{
  "username": "newuser",
  "password": "secure_password"
}
```

**响应 (201 Created):**

```json
{
  "id": 2,
  "username": "newuser",
  "created_at": "2026-03-22T10:00:00Z"
}
```

---

### 获取当前用户

获取已登录用户信息。

```
GET /api/auth/me
```

**响应 (200 OK):**

```json
{
  "id": 1,
  "username": "admin",
  "created_at": "2026-03-01T00:00:00Z"
}
```

---

## 设备 API

### 注册设备

播放器设备注册或更新。

```
POST /api/devices/register
```

**请求体：**

```json
{
  "device_id": "uuid-string",
  "device_name": "CastPlay-大厅01",
  "timezone": "Asia/Shanghai",
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "ip_address": "192.168.1.100"
}
```

**字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `device_id` | string | 否 | UUID 格式，不提供则自动生成 |
| `device_name` | string | 否 | 设备名称，默认 CastPlay-XXXXXXXX |
| `timezone` | string | 否 | 时区，默认 Asia/Shanghai |
| `mac_address` | string | 否 | MAC 地址 |
| `ip_address` | string | 否 | IP 地址 |

**响应 (201 Created / 200 OK):**

```json
{
  "id": 1,
  "device_id": "uuid-string",
  "device_name": "CastPlay-大厅01",
  "registration_code": "ABC123",
  "status": "online",
  "last_seen": "2026-03-22T10:00:00Z"
}
```

---

### 获取设备列表

```
GET /api/devices
```

**查询参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `skip` | int | 0 | 跳过数量 |
| `limit` | int | 20 | 返回数量 |

**响应 (200 OK):**

```json
{
  "devices": [
    {
      "id": 1,
      "device_id": "uuid-string",
      "device_name": "CastPlay-大厅01",
      "status": "online",
      "registration_code": "ABC123",
      "last_seen": "2026-03-22T10:00:00Z"
    }
  ],
  "total": 10,
  "online": 5,
  "offline": 5
}
```

---

### 获取设备详情

```
GET /api/devices/{device_id}
```

**响应 (200 OK):**

```json
{
  "id": 1,
  "device_id": "uuid-string",
  "device_name": "CastPlay-大厅01",
  "registration_code": "ABC123",
  "status": "online",
  "timezone": "Asia/Shanghai",
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "ip_address": "192.168.1.100",
  "assigned_playlists": [
    {
      "id": 1,
      "name": "企业宣传",
      "is_active": true
    }
  ],
  "last_seen": "2026-03-22T10:00:00Z",
  "created_at": "2026-03-01T00:00:00Z"
}
```

---

### 更新设备

```
PUT /api/devices/{device_id}
```

**请求体：**

```json
{
  "device_name": "新名称",
  "timezone": "Asia/Shanghai"
}
```

---

### 删除设备

```
DELETE /api/devices/{device_id}
```

**响应 (204 No Content)**

---

### 获取设备播放列表

```
GET /api/devices/{device_id}/playlists
```

**响应 (200 OK):**

```json
{
  "device_id": 1,
  "playlists": [
    {
      "id": 1,
      "name": "企业宣传",
      "is_active": true,
      "assigned_at": "2026-03-15T00:00:00Z"
    }
  ]
}
```

---

### 分配播放列表到设备

```
POST /api/devices/{device_id}/playlists
```

**请求体：**

```json
{
  "playlist_id": 1,
  "is_active": true
}
```

---

## 媒体 API

### 上传媒体文件

```
POST /api/media/upload
```

**表单参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file` | file | 是 | 上传的文件 |
| `file_type` | string | 是 | image / video / ppt |
| `slide_duration` | int | 否 | PPT 幻灯片时长（秒），默认 5 |

**支持的文件格式：**

| 类型 | 格式 |
|------|------|
| image | jpg, jpeg, png, gif, bmp |
| video | mp4, avi, mov, mkv, flv |
| ppt | ppt, pptx |

**响应 (201 Created):**

```json
{
  "id": 1,
  "filename": "video123.mp4",
  "original_name": "宣传片.mp4",
  "file_type": "video",
  "file_size": 10485760,
  "md5": "d41d8cd98f00b204e9800998ecf8427e",
  "url": "/uploads/video123.mp4",
  "thumbnail_url": "/thumbnails/video123.jpg",
  "status": "ready",
  "created_at": "2026-03-22T10:00:00Z"
}
```

---

### 获取媒体列表

```
GET /api/media
```

**查询参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `skip` | int | 0 | 跳过数量 |
| `limit` | int | 20 | 返回数量 |
| `file_type` | string | 全部 | 筛选类型 |
| `status` | string | 全部 | 筛选状态 |

**响应 (200 OK):**

```json
{
  "files": [
    {
      "id": 1,
      "filename": "video123.mp4",
      "original_name": "宣传片.mp4",
      "file_type": "video",
      "file_size": 10485760,
      "status": "ready",
      "created_at": "2026-03-22T10:00:00Z"
    }
  ],
  "total": 50
}
```

---

### 获取媒体详情

```
GET /api/media/{media_id}
```

---

### 删除媒体

```
DELETE /api/media/{media_id}
```

**响应 (204 No Content)**

---

### 获取上传 URL

获取预签名的上传 URL（用于大文件分片上传）。

```
GET /api/media/upload-url
```

**查询参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `filename` | string | 文件名 |
| `file_type` | string | 文件类型 |
| `size` | int | 文件大小（字节） |

**响应 (200 OK):**

```json
{
  "upload_url": "/uploads/temp/abc123.mp4",
  "media_id": "temp_abc123"
}
```

---

## 播放列表 API

### 创建播放列表

```
POST /api/playlists
```

**请求体：**

```json
{
  "name": "企业宣传",
  "description": "公司介绍视频和图片"
}
```

**响应 (201 Created):**

```json
{
  "id": 1,
  "name": "企业宣传",
  "description": "公司介绍视频和图片",
  "item_count": 0,
  "device_count": 0,
  "created_at": "2026-03-22T10:00:00Z"
}
```

---

### 获取播放列表

```
GET /api/playlists
```

**响应 (200 OK):**

```json
{
  "playlists": [
    {
      "id": 1,
      "name": "企业宣传",
      "description": "公司介绍",
      "item_count": 5,
      "device_count": 3
    }
  ],
  "total": 10
}
```

---

### 获取播放列表详情

```
GET /api/playlists/{playlist_id}
```

**响应 (200 OK):**

```json
{
  "id": 1,
  "name": "企业宣传",
  "description": "公司介绍",
  "items": [
    {
      "id": 1,
      "media_id": 1,
      "media_name": "宣传片.mp4",
      "media_type": "video",
      "duration": 60,
      "order": 1,
      "url": "/uploads/video123.mp4"
    }
  ],
  "devices": [
    {
      "id": 1,
      "device_name": "大厅屏幕",
      "is_active": true
    }
  ]
}
```

---

### 更新播放列表

```
PUT /api/playlists/{playlist_id}
```

---

### 删除播放列表

```
DELETE /api/playlists/{playlist_id}
```

---

### 添加媒体到播放列表

```
POST /api/playlists/{playlist_id}/items
```

**请求体：**

```json
{
  "media_id": 1,
  "duration": 30,
  "order": 1
}
```

---

### 批量添加媒体

```
POST /api/playlists/{playlist_id}/items/batch
```

**请求体：**

```json
{
  "items": [
    { "media_id": 1, "duration": 30 },
    { "media_id": 2, "duration": 20 },
    { "media_id": 3 }
  ]
}
```

---

### 重新排序播放列表项

```
PUT /api/playlists/{playlist_id}/items/reorder
```

**请求体：**

```json
{
  "item_ids": [3, 1, 2]
}
```

---

### 删除播放列表项

```
DELETE /api/playlists/{playlist_id}/items/{item_id}
```

---

## 调度 API

### 创建调度规则

```
POST /api/schedules
```

**请求体：**

```json
{
  "device_id": 1,
  "playlist_id": 1,
  "start_time": "09:00:00",
  "end_time": "18:00:00",
  "days_of_week": 127,
  "enabled": true,
  "priority": 0
}
```

**days_of_week 位掩码：**

| 值 | 含义 |
|----|------|
| 1 | 周一 |
| 2 | 周二 |
| 4 | 周三 |
| 8 | 周四 |
| 16 | 周五 |
| 32 | 周六 |
| 64 | 周日 |
| 127 | 每天 |

---

### 获取设备调度列表

```
GET /api/schedules?device_id=1
```

---

### 获取当前激活的调度

```
GET /api/schedules/active?device_id=1
```

**响应 (200 OK):**

```json
{
  "active_playlist_id": 2,
  "schedule_id": 1,
  "schedule_name": "午间时段"
}
```

如果没有匹配的调度：

```json
{
  "active_playlist_id": null,
  "schedule_id": null,
  "schedule_name": null
}
```

---

### 获取调度详情

```
GET /api/schedules/{schedule_id}
```

---

### 更新调度规则

```
PUT /api/schedules/{schedule_id}
```

---

### 删除调度规则

```
DELETE /api/schedules/{schedule_id}
```

---

## 播放端 API

供播放器设备调用的专用 API，通常不需要认证。

### 心跳

```
POST /api/player/{device_id}/heartbeat
```

**请求体：**

```json
{
  "status": "playing",
  "current_playlist_id": 1,
  "current_media_id": 3,
  "position": 45.5,
  "volume": 80,
  "download_progress": {
    "playlist_id": 1,
    "progress": 75.5,
    "downloaded": 15728640,
    "total": 20971520
  }
}
```

---

### 获取播放配置

```
GET /api/player/{device_id}/config
```

**响应 (200 OK):**

```json
{
  "device_id": 1,
  "server_url": "http://192.168.1.100:8000",
  "ws_url": "ws://192.168.1.100:8000/ws",
  "active_playlists": [
    {
      "id": 1,
      "name": "企业宣传",
      "is_default": true,
      "items": [
        {
          "id": 1,
          "media_id": 1,
          "media_type": "video",
          "url": "/uploads/video123.mp4",
          "duration": 60
        }
      ]
    }
  ],
  "schedule": {
    "schedules": [
      {
        "id": 1,
        "playlist_id": 1,
        "start_time": "09:00:00",
        "end_time": "18:00:00",
        "days_of_week": 127
      }
    ]
  },
  "config": {
    "playback_speed": 1.0,
    "volume": 80,
    "loop": true
  }
}
```

---

### 获取媒体下载链接

```
GET /api/player/{device_id}/media/{media_id}/url
```

**响应 (200 OK):**

```json
{
  "url": "/uploads/video123.mp4",
  "expires_at": "2026-03-22T11:00:00Z"
}
```

---

### 获取播放列表媒体列表

```
GET /api/player/{device_id}/playlists/{playlist_id}/items
```

---

## 控制 API

需要管理员认证。

### 暂停播放

```
POST /api/control/{device_id}/pause
```

---

### 恢复播放

```
POST /api/control/{device_id}/resume
```

---

### 调节音量

```
POST /api/control/{device_id}/volume
```

**请求体：**

```json
{
  "volume": 80
}
```

---

### 切换播放列表

```
POST /api/control/{device_id}/switch
```

**请求体：**

```json
{
  "playlist_id": 2
}
```

---

### 重新加载

```
POST /api/control/{device_id}/reload
```

---

## 错误响应

所有 API 错误遵循以下格式：

```json
{
  "detail": "错误描述"
}
```

### 常见错误码

| 状态码 | 说明 |
|--------|------|
| 400 | 请求参数错误 |
| 401 | 认证失败 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 413 | 文件大小超限 |
| 429 | 请求频率超限 |
| 500 | 服务器内部错误 |

---

## 速率限制

| 端点 | 限制 |
|------|------|
| 登录 | 5 次/分钟 |
| API 请求 | 100 次/分钟 |
| 心跳 | 10 次/分钟 |

---

## 相关文档

- [WebSocket 协议文档](./websocket.md)
- [配置参考文档](../configuration.md)
- [WebSocket 实时推送](../architecture/websocket-design.md)
