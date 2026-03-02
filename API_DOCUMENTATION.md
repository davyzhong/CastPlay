# CastPlay API 文档

## 📋 目录

- [概述](#概述)
- [认证](#认证)
- [设备管理 API](#设备管理-api)
- [媒体文件 API](#媒体文件-api)
- [播放列表 API](#播放列表-api)
- [播放端 API](#播放端-api)
- [WebSocket 事件](#websocket-事件)
- [错误码](#错误码)

---

## 概述

### 基础信息

- **Base URL**: `http://localhost:5000/api`
- **协议**: HTTP/1.1
- **数据格式**: JSON
- **字符编码**: UTF-8

### 通用响应格式

**成功响应**：

```json
{
  "message": "操作成功",
  "data": { ... }
}
```

**错误响应**：

```json
{
  "error": "错误描述"
}
```

### 状态码

| 状态码 | 说明           |
| ------ | -------------- |
| 200    | 成功           |
| 201    | 创建成功       |
| 400    | 请求参数错误   |
| 404    | 资源不存在     |
| 500    | 服务器内部错误 |

---

## 认证

### JWT Token（预留功能）

**Headers**:

```
Authorization: Bearer <token>
```

> 注：当前版本未启用认证，后续版本将支持 JWT 认证

---

## 设备管理 API

### 1. 设备注册

注册新设备或更新设备信息

**请求**

```http
POST /api/devices/register
Content-Type: application/json
```

**请求体**

```json
{
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "device_name": "会议室大屏",
  "timezone": "Asia/Shanghai"
}
```

**参数说明**

| 参数        | 类型   | 必填 | 说明                                  |
| ----------- | ------ | ---- | ------------------------------------- |
| device_id   | string | 是   | 设备唯一标识（UUID）                  |
| device_name | string | 否   | 设备名称，默认为 `Device-{前8位UUID}` |
| timezone    | string | 否   | 时区，默认为 `Asia/Shanghai`          |

**响应**

```json
{
  "message": "Device registered successfully",
  "device": {
    "id": 1,
    "device_id": "550e8400-e29b-41d4-a716-446655440000",
    "device_name": "会议室大屏",
    "timezone": "Asia/Shanghai",
    "last_online": "2026-01-29T10:30:00",
    "status": "online",
    "created_at": "2026-01-29T10:30:00",
    "updated_at": "2026-01-29T10:30:00"
  }
}
```

---

### 2. 设备心跳

更新设备在线状态

**请求**

```http
PUT /api/devices/{device_id}/heartbeat
```

**路径参数**

| 参数      | 类型    | 说明          |
| --------- | ------- | ------------- |
| device_id | integer | 设备数据库 ID |

**响应**

```json
{
  "message": "Heartbeat received",
  "device": {
    "id": 1,
    "device_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "online",
    "last_online": "2026-01-29T10:35:00"
  }
}
```

---

### 3. 设备列表

获取设备列表（分页）

**请求**

```http
GET /api/devices?page=1&per_page=20&status=online
```

**查询参数**

| 参数     | 类型    | 必填 | 说明                     |
| -------- | ------- | ---- | ------------------------ |
| page     | integer | 否   | 页码，默认 1             |
| per_page | integer | 否   | 每页数量，默认 20        |
| status   | string  | 否   | 过滤状态：online/offline |

**响应**

```json
{
  "devices": [
    {
      "id": 1,
      "device_id": "550e8400-e29b-41d4-a716-446655440000",
      "device_name": "会议室大屏",
      "status": "online",
      "last_online": "2026-01-29T10:35:00",
      "created_at": "2026-01-29T10:30:00"
    }
  ],
  "total": 50,
  "page": 1,
  "per_page": 20,
  "pages": 3
}
```

---

### 4. 设备详情

获取单个设备的详细信息

**请求**

```http
GET /api/devices/{device_id}
```

**响应**

```json
{
  "id": 1,
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "device_name": "会议室大屏",
  "timezone": "Asia/Shanghai",
  "status": "online",
  "last_online": "2026-01-29T10:35:00",
  "schedule": {
    "power_on_time": "08:00",
    "power_off_time": "18:00",
    "is_enabled": true,
    "weekdays": ["1", "2", "3", "4", "5"]
  },
  "playlists": [
    {
      "id": 1,
      "name": "宣传片播放列表",
      "is_active": true
    }
  ]
}
```

---

### 5. 更新设备

更新设备基本信息

**请求**

```http
PUT /api/devices/{device_id}
Content-Type: application/json
```

**请求体**

```json
{
  "device_name": "新会议室大屏",
  "timezone": "Asia/Hong_Kong",
  "status": "online"
}
```

**响应**

```json
{
  "message": "Device updated successfully",
  "device": { ... }
}
```

---

### 6. 删除设备

删除设备及其所有关联数据

**请求**

```http
DELETE /api/devices/{device_id}
```

**响应**

```json
{
  "message": "Device deleted successfully"
}
```

---

### 7. 设置定时配置

设置或更新设备的开关机定时

**请求**

```http
POST /api/devices/{device_id}/schedule
Content-Type: application/json
```

**请求体**

```json
{
  "power_on_time": "08:00",
  "power_off_time": "18:00",
  "is_enabled": true,
  "weekdays": [1, 2, 3, 4, 5]
}
```

**参数说明**

| 参数           | 类型    | 必填 | 说明                       |
| -------------- | ------- | ---- | -------------------------- |
| power_on_time  | string  | 否   | 开机时间（HH:MM 格式）     |
| power_off_time | string  | 否   | 关机时间（HH:MM 格式）     |
| is_enabled     | boolean | 否   | 是否启用，默认 true        |
| weekdays       | array   | 否   | 工作日数组，1=周一, 7=周日 |

**响应**

```json
{
  "message": "Schedule set successfully",
  "schedule": {
    "id": 1,
    "device_id": 1,
    "power_on_time": "08:00",
    "power_off_time": "18:00",
    "is_enabled": true,
    "weekdays": ["1", "2", "3", "4", "5"]
  }
}
```

> 注：设置定时配置后会自动通过 WebSocket 推送通知到设备

---

### 8. 查询定时配置

获取设备的定时配置

**请求**

```http
GET /api/devices/{device_id}/schedule
```

**响应**

```json
{
  "id": 1,
  "device_id": 1,
  "power_on_time": "08:00",
  "power_off_time": "18:00",
  "is_enabled": true,
  "weekdays": ["1", "2", "3", "4", "5"]
}
```

**错误响应**（未配置）

```json
{
  "message": "No schedule configured"
}
```

---

## 媒体文件 API

### 1. 上传媒体文件

上传图片、视频或 PPT 文件

**请求**

```http
POST /api/media/upload
Content-Type: multipart/form-data
```

**表单字段**

| 字段      | 类型   | 必填 | 说明                      |
| --------- | ------ | ---- | ------------------------- |
| file      | file   | 是   | 文件对象                  |
| file_type | string | 是   | 文件类型：image/video/ppt |

**支持的文件格式**

- **image**: jpg, jpeg, png, gif, bmp
- **video**: mp4, avi, mov, mkv, flv
- **ppt**: ppt, pptx

**响应**

```json
{
  "message": "File uploaded successfully",
  "media": {
    "id": 1,
    "file_name": "presentation.pptx",
    "file_type": "ppt",
    "file_size": 5242880,
    "status": "processing",
    "upload_time": "2026-01-29T10:40:00"
  }
}
```

> 注：上传 PPT 文件后会自动触发转换任务，状态为 `processing`。转换完成后状态变为 `ready`

---

### 2. 媒体文件列表

获取媒体文件列表（分页）

**请求**

```http
GET /api/media?page=1&per_page=20&file_type=video&status=ready
```

**查询参数**

| 参数      | 类型    | 必填 | 说明                              |
| --------- | ------- | ---- | --------------------------------- |
| page      | integer | 否   | 页码，默认 1                      |
| per_page  | integer | 否   | 每页数量，默认 20                 |
| file_type | string  | 否   | 过滤类型：image/video/ppt         |
| status    | string  | 否   | 过滤状态：ready/processing/failed |

**响应**

```json
{
  "media": [
    {
      "id": 1,
      "file_name": "presentation.pptx",
      "file_type": "ppt",
      "file_size": 5242880,
      "status": "ready",
      "converted_path": "/storage/converted/video_xxx.mp4",
      "thumbnail_path": "/storage/thumbnails/thumb_xxx.jpg",
      "upload_time": "2026-01-29T10:40:00"
    }
  ],
  "total": 100,
  "page": 1,
  "per_page": 20,
  "pages": 5
}
```

---

### 3. 媒体文件详情

获取单个媒体文件的详细信息

**请求**

```http
GET /api/media/{media_id}
```

**响应**

```json
{
  "id": 1,
  "file_name": "presentation.pptx",
  "file_type": "ppt",
  "file_path": "/storage/uploads/20260129_104000_presentation.pptx",
  "file_size": 5242880,
  "converted_path": "/storage/converted/video_xxx.mp4",
  "thumbnail_path": "/storage/thumbnails/thumb_xxx.jpg",
  "md5_hash": "d41d8cd98f00b204e9800998ecf8427e",
  "status": "ready",
  "upload_time": "2026-01-29T10:40:00"
}
```

---

### 4. 删除媒体文件

删除媒体文件及其所有关联数据

**请求**

```http
DELETE /api/media/{media_id}
```

**响应**

```json
{
  "message": "Media deleted successfully"
}
```

> 注：会同时删除原始文件、转换后的文件和缩略图

---

### 5. 下载媒体文件

下载媒体文件（用于管理后台预览）

**请求**

```http
GET /api/media/{media_id}/download
```

**响应**

- 文件流（Content-Type: application/octet-stream）
- 如果是 PPT 且已转换，返回转换后的视频

---

### 6. 获取缩略图

获取媒体文件的缩略图

**请求**

```http
GET /api/media/{media_id}/thumbnail
```

**响应**

- 图片流（Content-Type: image/jpeg）

---

## 播放列表 API

### 1. 创建播放列表

创建新的播放列表

**请求**

```http
POST /api/playlists
Content-Type: application/json
```

**请求体**

```json
{
  "name": "企业宣传片",
  "description": "公司介绍和产品宣传"
}
```

**响应**

```json
{
  "message": "Playlist created successfully",
  "playlist": {
    "id": 1,
    "name": "企业宣传片",
    "description": "公司介绍和产品宣传",
    "created_at": "2026-01-29T11:00:00",
    "updated_at": "2026-01-29T11:00:00"
  }
}
```

---

### 2. 播放列表列表

获取播放列表列表（分页）

**请求**

```http
GET /api/playlists?page=1&per_page=20
```

**响应**

```json
{
  "playlists": [
    {
      "id": 1,
      "name": "企业宣传片",
      "description": "公司介绍和产品宣传",
      "created_at": "2026-01-29T11:00:00"
    }
  ],
  "total": 10,
  "page": 1,
  "per_page": 20,
  "pages": 1
}
```

---

### 3. 播放列表详情

获取播放列表详细信息（含媒体项和关联设备）

**请求**

```http
GET /api/playlists/{playlist_id}
```

**响应**

```json
{
  "id": 1,
  "name": "企业宣传片",
  "description": "公司介绍和产品宣传",
  "items": [
    {
      "id": 1,
      "media_id": 5,
      "media_name": "公司介绍.mp4",
      "media_type": "video",
      "display_order": 1,
      "display_duration": 10
    },
    {
      "id": 2,
      "media_id": 8,
      "media_name": "产品展示.pptx",
      "media_type": "ppt",
      "display_order": 2,
      "display_duration": 30
    }
  ],
  "devices": [
    {
      "device_id": 1,
      "device_name": "会议室大屏",
      "is_active": true
    }
  ],
  "created_at": "2026-01-29T11:00:00"
}
```

---

### 4. 更新播放列表

更新播放列表基本信息

**请求**

```http
PUT /api/playlists/{playlist_id}
Content-Type: application/json
```

**请求体**

```json
{
  "name": "新企业宣传片",
  "description": "更新后的描述"
}
```

**响应**

```json
{
  "message": "Playlist updated successfully",
  "playlist": { ... }
}
```

---

### 5. 删除播放列表

删除播放列表

**请求**

```http
DELETE /api/playlists/{playlist_id}
```

**响应**

```json
{
  "message": "Playlist deleted successfully"
}
```

---

### 6. 添加媒体到播放列表

向播放列表添加媒体项

**请求**

```http
POST /api/playlists/{playlist_id}/items
Content-Type: application/json
```

**请求体**

```json
{
  "media_id": 5,
  "display_duration": 10
}
```

**参数说明**

| 参数             | 类型    | 必填 | 说明                   |
| ---------------- | ------- | ---- | ---------------------- |
| media_id         | integer | 是   | 媒体文件 ID            |
| display_duration | integer | 否   | 显示时长（秒），默认 5 |

**响应**

```json
{
  "message": "Media added to playlist successfully",
  "item": {
    "id": 1,
    "playlist_id": 1,
    "media_id": 5,
    "display_order": 3,
    "display_duration": 10
  }
}
```

> 注：`display_order` 自动设置为当前最大值 + 1

---

### 7. 从播放列表移除媒体

从播放列表移除指定媒体项

**请求**

```http
DELETE /api/playlists/{playlist_id}/items/{item_id}
```

**响应**

```json
{
  "message": "Media removed from playlist successfully"
}
```

---

### 8. 重新排序播放列表项

调整播放列表中媒体的顺序

**请求**

```http
PUT /api/playlists/{playlist_id}/items/reorder
Content-Type: application/json
```

**请求体**

```json
{
  "items": [
    { "id": 2, "order": 0 },
    { "id": 1, "order": 1 },
    { "id": 3, "order": 2 }
  ]
}
```

**响应**

```json
{
  "message": "Playlist items reordered successfully"
}
```

---

### 9. 分配播放列表到设备

将播放列表分配给指定设备

**请求**

```http
POST /api/playlists/{playlist_id}/devices/{device_id}
```

**响应**

```json
{
  "message": "Playlist assigned to device successfully",
  "assignment": {
    "id": 1,
    "device_id": 1,
    "playlist_id": 1,
    "is_active": true
  }
}
```

> 注：分配后会自动通过 WebSocket 推送更新通知到设备

---

### 10. 取消分配播放列表

取消设备的播放列表分配

**请求**

```http
DELETE /api/playlists/{playlist_id}/devices/{device_id}
```

**响应**

```json
{
  "message": "Playlist unassigned from device successfully"
}
```

---

### 11. 激活/停用播放列表

激活或停用设备上的播放列表

**请求**

```http
PUT /api/playlists/{playlist_id}/devices/{device_id}/activate
Content-Type: application/json
```

**请求体**

```json
{
  "is_active": true
}
```

**响应**

```json
{
  "message": "Playlist activated successfully"
}
```

---

## 播放端 API

### 1. 播放端初始化

Android 设备启动时调用，获取完整配置

**请求**

```http
POST /api/player/init
Content-Type: application/json
```

**请求体**

```json
{
  "device_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**响应**

```json
{
  "device": {
    "id": 1,
    "device_id": "550e8400-e29b-41d4-a716-446655440000",
    "device_name": "会议室大屏",
    "timezone": "Asia/Shanghai"
  },
  "playlists": [
    {
      "id": 1,
      "name": "企业宣传片",
      "version": "2026-01-29T11:00:00",
      "items": [
        {
          "id": 1,
          "media_id": 5,
          "file_name": "intro.mp4",
          "file_type": "video",
          "file_url": "/api/player/media/5/download",
          "display_order": 1,
          "display_duration": 10,
          "file_size": 10485760,
          "md5_hash": "d41d8cd98f00b204e9800998ecf8427e"
        }
      ]
    }
  ],
  "schedule": {
    "power_on_time": "08:00:00",
    "power_off_time": "18:00:00",
    "weekdays": [1, 2, 3, 4, 5],
    "timezone": "Asia/Shanghai"
  },
  "websocket_url": "ws://localhost:5000"
}
```

---

### 2. 检查播放列表版本

检查本地播放列表是否需要更新

**请求**

```http
POST /api/player/playlist/{playlist_id}/check
Content-Type: application/json
```

**请求体**

```json
{
  "version": "2026-01-29T10:00:00"
}
```

**响应**

```json
{
  "needs_update": true,
  "server_version": "2026-01-29T11:00:00",
  "local_version": "2026-01-29T10:00:00"
}
```

---

### 3. 下载媒体文件

下载媒体文件到本地（原始文件或转换后文件）

**请求**

```http
GET /api/player/media/{media_id}/download
```

**响应**

- 文件流（支持断点续传）

---

### 4. 下载转换后的文件

下载 PPT 转换后的视频文件

**请求**

```http
GET /api/player/media/{media_id}/converted
```

**响应**

- 视频文件流

---

### 5. 上报播放状态

定期上报设备播放状态

**请求**

```http
POST /api/player/status
Content-Type: application/json
```

**请求体**

```json
{
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "playing"
}
```

**响应**

```json
{
  "message": "Status reported successfully"
}
```

---

## WebSocket 事件

### 连接 WebSocket

**URL**: `ws://localhost:5000/socket.io/`

**协议**: Socket.IO

### 客户端事件

#### 1. 设备注册

连接后立即发送设备注册消息

**发送**

```json
{
  "device_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**接收**（registered）

```json
{
  "event": "registered",
  "message": "Device registered successfully",
  "device_id": 1
}
```

---

#### 2. 心跳

定期发送心跳维持连接

**发送**

```json
{
  "device_id": 1
}
```

**接收**（heartbeat_ack）

```json
{
  "event": "heartbeat_ack",
  "timestamp": "2026-01-29T11:30:00"
}
```

---

### 服务端事件

#### 1. 播放列表更新通知

**接收**（playlist_update）

```json
{
  "event": "playlist_update",
  "playlist_id": 1,
  "action": "update",
  "timestamp": "2026-01-29T11:00:00"
}
```

**处理**：重新同步播放列表数据

---

#### 2. 定时配置更新通知

**接收**（schedule_update）

```json
{
  "event": "schedule_update",
  "schedule": {
    "power_on_time": "09:00",
    "power_off_time": "17:00",
    "weekdays": [1, 2, 3, 4, 5],
    "timezone": "Asia/Shanghai"
  },
  "action": "update",
  "timestamp": "2026-01-29T11:00:00"
}
```

**处理**：更新本地定时配置

---

#### 3. 强制同步通知

**接收**（force_sync）

```json
{
  "event": "force_sync",
  "action": "sync",
  "timestamp": "2026-01-29T11:00:00"
}
```

**处理**：立即执行完整同步

---

#### 4. 重启命令

**接收**（reboot）

```json
{
  "event": "reboot",
  "action": "reboot",
  "timestamp": "2026-01-29T11:00:00"
}
```

**处理**：重启 Android 应用

---

## 错误码

### HTTP 状态码

| 状态码 | 说明           | 示例                       |
| ------ | -------------- | -------------------------- |
| 200    | 成功           | -                          |
| 201    | 创建成功       | 上传文件、创建播放列表     |
| 400    | 请求参数错误   | 缺少必填参数、参数格式错误 |
| 404    | 资源不存在     | 设备/媒体/播放列表不存在   |
| 500    | 服务器内部错误 | 数据库错误、文件系统错误   |

### 业务错误码

| 错误信息                    | 原因           | 解决方案                  |
| --------------------------- | -------------- | ------------------------- |
| `device_id is required`     | 缺少设备 ID    | 请求中添加 device_id 参数 |
| `Device not registered`     | 设备未注册     | 先调用注册接口            |
| `No file provided`          | 未上传文件     | 检查表单字段名称          |
| `File type not allowed`     | 文件类型不支持 | 检查文件扩展名            |
| `Media file not found`      | 媒体文件不存在 | 检查 media_id             |
| `No schedule configured`    | 未配置定时     | 先设置定时配置            |
| `Playlist already assigned` | 播放列表已分配 | 无需重复分配              |

---

## 附录

### A. 时区列表

常用时区：

- `Asia/Shanghai` - 中国标准时间（UTC+8）
- `Asia/Hong_Kong` - 香港时间（UTC+8）
- `Asia/Tokyo` - 日本标准时间（UTC+9）
- `America/New_York` - 美国东部时间（UTC-5/-4）
- `Europe/London` - 英国时间（UTC+0/+1）

完整列表：https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

### B. 文件大小限制

- **最大文件大小**：500 MB
- **建议大小**：
  - 图片：< 5 MB
  - 视频：< 200 MB
  - PPT：< 50 MB

### C. PPT 转换说明

**转换流程**：

1. PPT → PDF（LibreOffice）
2. PDF → 图片序列（pdftoppm）
3. 图片序列 → 视频（ffmpeg）

**默认参数**：

- 每张幻灯片时长：5 秒
- 视频分辨率：1920x1080
- 视频编码：H.264
- 帧率：30fps

**转换时间**：

- 10 页 PPT 约需 30-60 秒
- 依赖服务器性能

---

**文档版本**：v1.0
**最后更新**：2026-01-29
**维护者**：CastPlay 开发团队
