# CastPlay WebSocket 协议文档

本文档详细介绍 CastPlay 系统的 WebSocket 通信协议。

## 连接信息

| 属性 | 值 |
|------|-----|
| URL | `ws://{host}:8000/ws/{device_id}` |
| 心跳间隔 | 30 秒 |
| 心跳超时 | 10 秒 |
| 协议版本 | v2 |

## 连接流程

### 1. 建立连接

播放器设备通过 WebSocket 连接到服务器：

```
ws://localhost:8000/ws/your-device-uuid
```

### 2. 心跳保活

连接建立后，客户端需定期发送心跳消息：

```json
{
  "type": "heartbeat",
  "device_id": "your-device-uuid",
  "timestamp": "2026-03-22T10:00:00Z"
}
```

服务器响应：

```json
{
  "type": "heartbeat",
  "timestamp": "2026-03-22T10:00:00Z"
}
```

**注意**：如果超过 60 秒未收到心跳，服务器将自动断开连接。

---

## 消息格式

所有 WebSocket 消息使用 JSON 格式：

### 服务端 -> 客户端

```json
{
  "type": "message_type",
  "device_id": "device-uuid",
  "timestamp": "2026-03-22T10:00:00Z",
  "data": { ... }
}
```

### 客户端 -> 服务端

```json
{
  "type": "message_type",
  "device_id": "device-uuid",
  "timestamp": "2026-03-22T10:00:00Z",
  "data": { ... }
}
```

---

## 服务端消息类型

### 播放列表相关

#### playlist_assigned - 播放列表已分配

通知设备分配了新的播放列表。

```json
{
  "type": "playlist_assigned",
  "device_id": "device-uuid",
  "timestamp": "2026-03-22T10:00:00Z",
  "data": {
    "playlist_id": 1,
    "playlist_name": "企业宣传",
    "version": "v1.0.0",
    "action": "assign",
    "item_count": 10,
    "total_size": 52428800,
    "priority": "normal"
  }
}
```

#### playlist_updated - 播放列表内容更新

通知设备播放列表内容已变更。

```json
{
  "type": "playlist_updated",
  "device_id": "device-uuid",
  "timestamp": "2026-03-22T10:00:00Z",
  "data": {
    "playlist_id": 1,
    "playlist_name": "企业宣传",
    "version": "v1.1.0",
    "action": "update",
    "item_count": 12,
    "total_size": 62914560,
    "priority": "normal",
    "changes": {
      "added": [{"media_id": 5, "name": "新产品.mp4"}],
      "removed": [{"media_id": 3}],
      "reordered": true
    }
  }
}
```

#### playlist_removed - 播放列表已移除

通知设备播放列表已从设备移除。

```json
{
  "type": "playlist_removed",
  "device_id": "device-uuid",
  "timestamp": "2026-03-22T10:00:00Z",
  "data": {
    "playlist_id": 1,
    "action": "remove"
  }
}
```

#### playlist_activated - 播放列表已激活

通知设备播放列表激活状态变更。

```json
{
  "type": "playlist_activated",
  "device_id": "device-uuid",
  "timestamp": "2026-03-22T10:00:00Z",
  "data": {
    "playlist_id": 1,
    "is_active": true
  }
}
```

#### playlist_deactivated - 播放列表已停用

```json
{
  "type": "playlist_deactivated",
  "device_id": "device-uuid",
  "timestamp": "2026-03-22T10:00:00Z",
  "data": {
    "playlist_id": 1,
    "is_active": false
  }
}
```

---

### 设备配置相关

#### device_config_updated - 设备配置更新

通知设备配置变更（如播放速度）。

```json
{
  "type": "device_config_updated",
  "device_id": "device-uuid",
  "timestamp": "2026-03-22T10:00:00Z",
  "data": {
    "playback_speed": 1.5,
    "volume": 80,
    "loop": true
  }
}
```

#### device_disabled - 设备已禁用

通知设备已被禁用。

```json
{
  "type": "device_disabled",
  "device_id": "device-uuid",
  "timestamp": "2026-03-22T10:00:00Z",
  "data": {
    "is_disabled": true,
    "message": "设备已被禁用，只能播放默认内容"
  }
}
```

---

### 调度相关

#### schedule_updated - 定时配置更新

通知设备定时配置已变更。

```json
{
  "type": "schedule_updated",
  "device_id": "device-uuid",
  "timestamp": "2026-03-22T10:00:00Z",
  "data": {
    "schedules": [
      {
        "id": 1,
        "playlist_id": 1,
        "start_time": "09:00:00",
        "end_time": "12:00:00",
        "days_of_week": 31,
        "enabled": true
      }
    ]
  }
}
```

#### schedule_update - 调度触发

通知设备根据定时规则切换播放列表。

```json
{
  "type": "schedule_update",
  "device_id": "device-uuid",
  "timestamp": "2026-03-22T12:00:00Z",
  "data": {
    "playlist_id": 2,
    "schedule_id": 1,
    "schedule_name": "午间时段",
    "action": "switch"
  }
}
```

---

### 控制指令

#### control - 播放控制指令

通用控制指令。

```json
{
  "type": "control",
  "device_id": "device-uuid",
  "timestamp": "2026-03-22T10:00:00Z",
  "data": {
    "action": "pause"
  }
}
```

**支持的 action 值：**

| action | 说明 | 附加参数 |
|--------|------|----------|
| `pause` | 暂停播放 | - |
| `resume` | 恢复播放 | - |
| `reboot` | 重启设备 | - |
| `volume` | 调节音量 | `volume`: 0-100 |
| `reload` | 重新加载 | - |
| `seek` | 跳转位置 | `position`: 秒数 |
| `next` | 下一个媒体 | - |
| `prev` | 上一个媒体 | - |
| `switch_playlist` | 切换播放列表 | `playlist_id` |

#### force_sync - 强制同步

通知设备强制同步。

```json
{
  "type": "force_sync",
  "device_id": "device-uuid",
  "timestamp": "2026-03-22T10:00:00Z",
  "data": {
    "action": "sync"
  }
}
```

---

## 客户端消息类型

### heartbeat - 心跳

```json
{
  "type": "heartbeat",
  "device_id": "device-uuid",
  "timestamp": "2026-03-22T10:00:00Z"
}
```

---

### download_progress - 下载进度上报

```json
{
  "type": "download_progress",
  "device_id": "device-uuid",
  "timestamp": "2026-03-22T10:00:00Z",
  "data": {
    "playlist_id": 1,
    "media_id": 5,
    "media_name": "宣传片.mp4",
    "progress": 45.5,
    "status": "downloading",
    "downloaded_bytes": 10485760,
    "total_bytes": 20971520,
    "error": null
  }
}
```

**status 值：**

| status | 说明 |
|--------|------|
| `pending` | 等待下载 |
| `downloading` | 下载中 |
| `completed` | 下载完成 |
| `failed` | 下载失败 |

---

### download_complete - 下载完成

```json
{
  "type": "download_complete",
  "device_id": "device-uuid",
  "timestamp": "2026-03-22T10:00:00Z",
  "data": {
    "playlist_id": 1,
    "media_id": 5,
    "media_name": "宣传片.mp4",
    "status": "completed"
  }
}
```

---

### download_failed - 下载失败

```json
{
  "type": "download_failed",
  "device_id": "device-uuid",
  "timestamp": "2026-03-22T10:00:00Z",
  "data": {
    "playlist_id": 1,
    "media_id": 5,
    "media_name": "宣传片.mp4",
    "status": "failed",
    "error": "网络连接失败"
  }
}
```

---

### playlist_switched - 播放列表已切换

```json
{
  "type": "playlist_switched",
  "device_id": "device-uuid",
  "timestamp": "2026-03-22T10:00:00Z",
  "data": {
    "from_playlist_id": 1,
    "to_playlist_id": 2,
    "reason": "schedule"
  }
}
```

**reason 值：**

| reason | 说明 |
|--------|------|
| `manual` | 手动切换 |
| `schedule` | 定时切换 |
| `auto` | 自动循环 |

---

### player_status - 播放状态上报

```json
{
  "type": "player_status",
  "device_id": "device-uuid",
  "timestamp": "2026-03-22T10:00:00Z",
  "data": {
    "status": "playing",
    "current_playlist_id": 1,
    "current_media_id": 5,
    "position": 45.5,
    "duration": 120.0,
    "volume": 80,
    "loop": true
  }
}
```

**status 值：**

| status | 说明 |
|--------|------|
| `idle` | 空闲 |
| `loading` | 加载中 |
| `playing` | 播放中 |
| `paused` | 已暂停 |
| `error` | 错误状态 |

---

## 消息流程示例

### 播放列表切换流程

```
1. 服务端发送 playlist_updated
   {
     "type": "playlist_updated",
     "data": {
       "playlist_id": 2,
       "action": "update"
     }
   }

2. 客户端发送 download_progress (多次)
   {
     "type": "download_progress",
     "data": { "progress": 25, "status": "downloading" }
   }

3. 客户端发送 download_complete
   {
     "type": "download_complete",
     "data": { "status": "completed" }
   }

4. 客户端发送 playlist_switched
   {
     "type": "playlist_switched",
     "data": {
       "from_playlist_id": 1,
       "to_playlist_id": 2,
       "reason": "manual"
     }
   }
```

### 定时切换流程

```
1. 服务端发送 schedule_update
   {
     "type": "schedule_update",
     "data": {
       "playlist_id": 2,
       "schedule_id": 1,
       "action": "switch"
     }
   }

2. 客户端下载新播放列表内容

3. 客户端发送 playlist_switched
   {
     "type": "playlist_switched",
     "data": {
       "from_playlist_id": 1,
       "to_playlist_id": 2,
       "reason": "schedule"
     }
   }
```

---

## 错误处理

### 连接断开

如果 WebSocket 连接断开，播放器应：

1. 等待 5 秒后尝试重连
2. 使用指数退避策略（5s, 10s, 20s, 40s, 最大 60s）
3. 重连成功后发送心跳并请求完整配置

### 消息处理错误

如果收到无法解析的消息，应：

1. 记录错误日志
2. 忽略该消息
3. 继续处理后续消息

---

## 相关文档

- [API 参考文档](./README.md)
- [配置参考文档](../configuration.md)
