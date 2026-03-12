# 播放端详细设计方案 V3

> 文档版本: 3.0
> 创建日期: 2026-03-07
> 状态: 设计阶段

---

## 一、项目背景与需求

### 1.1 项目概述

CastPlay 是一个数字标牌（Digital Signage）管理系统，用于统一管理和分发播放内容到分布在各地的播放终端。

### 1.2 核心需求

| 需求项 | 说明 |
|--------|------|
| 播放端类型 | Android 电视盒子 + Web 浏览器 |
| 播放端数量 | 20-50 个 |
| 地理分布 | 不同国家和地区，需支持多时区 |
| 网络环境 | 不稳定，需离线播放 |
| 心跳频率 | 小时级别 |
| 服务器访问 | 公网访问 |
| Android 分发 | 自分发 APK，手动安装 |
| 监控告警 | 离线超48小时告警，邮件+钉钉 |

---

## 二、当前完成情况

### 2.1 已完成功能 ✅

| 模块 | 功能 | 状态 | 文件位置 |
|------|------|------|----------|
| **服务器端** | 设备管理 API | ✅ 完整 | `app/api/devices.py` |
| | 播放列表 API | ✅ 完整 | `app/api/playlists.py` |
| | 媒体文件 API | ✅ 完整 | `app/api/media.py` |
| | 播放端专用 API | ✅ 完整 | `app/api/player.py` |
| | WebSocket 推送 | ✅ 完整 | `app/websocket/handler.py` |
| | 心跳监控 | ✅ 完整 | `app/api/player.py` |
| **Web 播放器** | 设备注册 | ✅ 完整 | `frontend/src/player/useDeviceRegistration.ts` |
| | 播放列表同步 | ✅ 完整 | `frontend/src/player/usePlaylistSync.ts` |
| | 离线模式 | ✅ 完整 | `frontend/src/player/useOfflineMode.ts` |
| | 定时播放 | ✅ 完整 | `frontend/src/player/usePlaybackScheduler.ts` |
| | 心跳上报 | ✅ 完整 | `frontend/src/player/hooks/useHeartbeat.ts` |
| **Android SDK** | WebView 宿主 | ✅ 基础 | `android/.../MainActivity.kt` |
| | JavaScript Bridge | ✅ 基础 | `android/.../JsBridge.kt` |
| | 媒体缓存 | ✅ 基础 | `android/.../CacheManager.kt` |
| | 开机自启 | ✅ 完整 | `android/.../BootReceiver.kt` |

### 2.2 需要完善的功能 ⚠️

| 问题 | 当前状态 | 影响 | 优先级 |
|------|----------|------|--------|
| 心跳间隔不一致 | PlayerCore.tsx 用 30秒，useHeartbeat 用 2小时 | 需统一为小时级 | P0 |
| 服务器在线阈值 | 当前 5 分钟，需调整为 3 小时 | 离线判断不准 | P0 |
| Android 下载无断点续传 | CacheManager 仅基础下载 | 网络不稳定时失败 | P0 |
| 缺少 MD5 校验 | 下载后无完整性验证 | 文件可能损坏 | P0 |
| 缺少错误上报 | 仅 console.log | 无法远程诊断 | P0 |
| 缺少存储空间管理 | 无自动清理策略 | 可能磁盘满 | P1 |
| 缺少下载重试 | 无指数退避策略 | 下载失败无法恢复 | P1 |
| 缺少告警通知 | 无邮件/钉钉告警 | 无法及时发现问题 | P0 |
| 时区处理不完整 | 调度器固定上海时区 | 定时不准 | P1 |

---

## 三、整体架构设计

### 3.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                          服务器端 (公网)                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌───────────────┐  │
│  │  REST API  │  │ WebSocket  │  │  调度器    │  │ 媒体存储/转换 │  │
│  │  (FastAPI) │  │  (推送)    │  │ (定时告警) │  │   (本地存储)  │  │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └───────┬───────┘  │
│        │               │               │                 │          │
│        └───────────────┴───────────────┴─────────────────┘          │
│                                │                                     │
│                    ┌───────────┴───────────┐                        │
│                    ▼                       ▼                        │
│             ┌────────────┐         ┌────────────┐                   │
│             │ 邮件服务   │         │ 钉钉机器人 │                   │
│             └────────────┘         └────────────┘                   │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 │ HTTPS (公网访问)
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐        ┌───────────────┐        ┌───────────────┐
│ Android TV    │        │ Android TV    │        │ Web Browser   │
│ (中国 上海)   │        │ (美国 纽约)   │        │ (任意位置)    │
│               │        │               │        │               │
│ ┌───────────┐ │        │ ┌───────────┐ │        │ ┌───────────┐ │
│ │  本地存储 │ │        │ │  本地存储 │ │        │ │ Cache API │ │
│ │  (离线)   │ │        │ │  (离线)   │ │        │ │  (离线)   │ │
│ └───────────┘ │        └───────────┘ │        │ └───────────┘ │
│               │        │               │        │               │
│ 心跳: 2小时   │        │ 心跳: 2小时   │        │ 心跳: 2小时   │
│ 时区: +8      │        │ 时区: -5      │        │ 时区: 自动    │
└───────────────┘        └───────────────┘        └───────────────┘
```

### 3.2 数据流

```
1. 初始化流程 (启动时)
   ┌──────────┐     POST /api/player/init     ┌──────────┐
   │ 播放端   │ ───────────────────────────▶ │ 服务器   │
   │          │ ◀─────────────────────────── │          │
   └──────────┘    返回设备信息+播放列表+配置 └──────────┘

2. 内容同步流程 (有网络时)
   ┌──────────┐     下载媒体文件 (带MD5)     ┌──────────┐
   │ 播放端   │ ───────────────────────────▶ │ 服务器   │
   │          │ ◀─────────────────────────── │          │
   └──────────┘         返回文件内容          └──────────┘
        │
        ▼ 验证 MD5，存储到本地

3. 心跳流程 (每2小时)
   ┌──────────┐     POST /api/player/heartbeat   ┌──────────┐
   │ 播放端   │ ───────────────────────────────▶ │ 服务器   │
   │          │    {device_id, status, ...}     │          │
   │          │ ◀─────────────────────────────── │          │
   └──────────┘    {ack, server_time, updates}  └──────────┘

4. 告警流程 (服务器端定时任务，每小时检查)
   ┌──────────┐     检查 last_online           ┌──────────┐
   │ 调度器   │ ──────────────────────────────▶ │ 数据库   │
   │          │ ◀────────────────────────────── │          │
   └──────────┘    返回离线超48h设备列表      └──────────┘
        │
        ├──▶ 发送邮件通知
        └──▶ 发送钉钉通知
```

---

## 四、服务器端增强设计

### 4.1 配置模型新增

```python
# app/models/device.py (新增)

class AlertConfig(Base, TimestampMixin):
    """告警配置表"""
    __tablename__ = "alert_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 离线告警配置
    offline_threshold_hours = Column(Integer, default=48, doc="离线阈值(小时)")
    check_interval_hours = Column(Integer, default=1, doc="检查间隔(小时)")

    # 邮件配置
    email_enabled = Column(Boolean, default=False, doc="是否启用邮件告警")
    smtp_host = Column(String(100), nullable=True, doc="SMTP服务器")
    smtp_port = Column(Integer, default=587, doc="SMTP端口")
    smtp_user = Column(String(100), nullable=True, doc="SMTP用户名")
    smtp_password = Column(String(200), nullable=True, doc="SMTP密码(加密)")
    email_from = Column(String(100), nullable=True, doc="发件人地址")
    email_to = Column(Text, nullable=True, doc="收件人列表(JSON数组)")

    # 钉钉配置
    dingtalk_enabled = Column(Boolean, default=False, doc="是否启用钉钉告警")
    dingtalk_webhook = Column(String(500), nullable=True, doc="钉钉机器人Webhook")
    dingtalk_secret = Column(String(200), nullable=True, doc="钉钉签名密钥")

    # 全局开关
    is_active = Column(Boolean, default=True, doc="是否启用")
```

### 4.2 告警服务设计

```python
# app/services/alert_service.py (新增)

import smtplib
import hashlib
import hmac
import base64
import time
import urllib.parse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import httpx
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.device import Device, AlertConfig

class AlertService:
    """告警服务"""

    def __init__(self, db: Session):
        self.db = db
        self.config = self._load_config()

    def _load_config(self) -> Optional[AlertConfig]:
        """加载告警配置"""
        return self.db.query(AlertConfig).filter(
            AlertConfig.is_active == True
        ).first()

    def check_offline_devices(self) -> List[Device]:
        """检查离线超过阈值的设备"""
        if not self.config:
            return []

        threshold = datetime.utcnow() - timedelta(
            hours=self.config.offline_threshold_hours
        )

        offline_devices = self.db.query(Device).filter(
            Device.last_online < threshold,
            Device.is_disabled == False
        ).all()

        return offline_devices

    def send_alert(self, devices: List[Device]) -> dict:
        """发送告警通知"""
        if not devices:
            return {"sent": False, "reason": "no_offline_devices"}

        results = {
            "email": None,
            "dingtalk": None,
            "device_count": len(devices)
        }

        # 构建告警内容
        content = self._build_alert_content(devices)

        # 发送邮件
        if self.config and self.config.email_enabled:
            results["email"] = self._send_email(content)

        # 发送钉钉
        if self.config and self.config.dingtalk_enabled:
            results["dingtalk"] = self._send_dingtalk(content)

        return results

    def _build_alert_content(self, devices: List[Device]) -> dict:
        """构建告警内容"""
        device_list = []
        for device in devices:
            offline_duration = datetime.utcnow() - device.last_online
            hours = int(offline_duration.total_seconds() / 3600)

            device_list.append({
                "name": device.device_name,
                "device_id": device.device_id[-8:],  # 只显示后8位
                "timezone": device.timezone,
                "last_online": device.last_online.strftime("%Y-%m-%d %H:%M UTC"),
                "offline_hours": hours
            })

        return {
            "title": f"CastPlay 设备离线告警 ({len(devices)}台)",
            "devices": device_list,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        }

    def _send_email(self, content: dict) -> dict:
        """发送邮件通知"""
        try:
            config = self.config
            msg = MIMEMultipart("alternative")
            msg["Subject"] = content["title"]
            msg["From"] = config.email_from
            msg["To"] = ", ".join(config.email_to)

            # 构建邮件正文
            text_body = self._build_email_text(content)
            html_body = self._build_email_html(content)

            msg.attach(MIMEText(text_body, "plain", "utf-8"))
            msg.attach(MIMEText(html_body, "html", "utf-8"))

            # 发送
            with smtplib.SMTP(config.smtp_host, config.smtp_port) as server:
                server.starttls()
                server.login(config.smtp_user, config.smtp_password)
                server.sendmail(
                    config.email_from,
                    config.email_to,
                    msg.as_string()
                )

            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _build_email_html(self, content: dict) -> str:
        """构建 HTML 邮件正文"""
        device_rows = ""
        for d in content["devices"]:
            device_rows += f"""
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">{d['name']}</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{d['device_id']}</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{d['timezone']}</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{d['last_online']}</td>
                    <td style="padding: 8px; border: 1px solid #ddd; color: red;">{d['offline_hours']} 小时</td>
                </tr>
            """

        return f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #d32f2f;">⚠️ {content['title']}</h2>
            <p>以下设备已离线超过配置的阈值时间：</p>
            <table style="border-collapse: collapse; width: 100%;">
                <tr style="background-color: #f5f5f5;">
                    <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">设备名称</th>
                    <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">设备ID</th>
                    <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">时区</th>
                    <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">最后在线</th>
                    <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">离线时长</th>
                </tr>
                {device_rows}
            </table>
            <p style="color: #666; margin-top: 20px;">
                告警时间: {content['timestamp']}<br>
                请及时检查设备状态。
            </p>
        </body>
        </html>
        """

    def _build_email_text(self, content: dict) -> str:
        """构建纯文本邮件正文"""
        lines = [f"⚠️ {content['title']}", ""]
        lines.append("以下设备已离线超过配置的阈值时间：")
        lines.append("")

        for d in content["devices"]:
            lines.append(f"- {d['name']} (ID: {d['device_id']})")
            lines.append(f"  时区: {d['timezone']}, 最后在线: {d['last_online']}")
            lines.append(f"  离线时长: {d['offline_hours']} 小时")
            lines.append("")

        lines.append(f"告警时间: {content['timestamp']}")
        lines.append("请及时检查设备状态。")

        return "\n".join(lines)

    def _send_dingtalk(self, content: dict) -> dict:
        """发送钉钉通知"""
        try:
            webhook = self.config.dingtalk_webhook

            # 构建钉钉消息
            device_text = ""
            for d in content["devices"][:10]:  # 最多显示10个
                device_text += f"- **{d['name']}** (离线 {d['offline_hours']}h)\n"

            if len(content["devices"]) > 10:
                device_text += f"\n... 还有 {len(content['devices']) - 10} 台设备"

            message = {
                "msgtype": "markdown",
                "markdown": {
                    "title": content["title"],
                    "text": f"""## ⚠️ {content['title']}

**离线设备列表：**
{device_text}

> 告警时间: {content['timestamp']}
> 请及时检查设备状态。
"""
                }
            }

            # 签名
            if self.config.dingtalk_secret:
                timestamp = str(round(time.time() * 1000))
                string_to_sign = f"{timestamp}\n{self.config.dingtalk_secret}"
                hmac_code = hmac.new(
                    self.config.dingtalk_secret.encode(),
                    string_to_sign.encode(),
                    digestmod=hashlib.sha256
                ).digest()
                sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
                webhook = f"{webhook}&timestamp={timestamp}&sign={sign}"

            # 发送
            response = httpx.post(webhook, json=message, timeout=10)
            result = response.json()

            return {
                "success": result.get("errcode") == 0,
                "response": result
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
```

### 4.3 调度器配置更新

```python
# app/scheduler.py (修改)

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.services.alert_service import AlertService

def setup_alert_job(scheduler: BackgroundScheduler, db_session_factory):
    """设置告警定时任务"""

    def check_and_alert():
        db = db_session_factory()
        try:
            alert_service = AlertService(db)
            offline_devices = alert_service.check_offline_devices()
            if offline_devices:
                result = alert_service.send_alert(offline_devices)
                logger.info(f"Alert sent: {result}")
        except Exception as e:
            logger.error(f"Alert job failed: {e}")
        finally:
            db.close()

    # 每小时检查一次
    scheduler.add_job(
        check_and_alert,
        trigger=IntervalTrigger(hours=1),
        id="device_offline_alert",
        name="设备离线告警检查",
        replace_existing=True
    )
```

### 4.4 在线阈值常量更新

```python
# app/api/player.py (修改)

# 修改在线阈值从 5 分钟改为 3 小时
DEVICE_ONLINE_THRESHOLD_HOURS = 3  # 设备在线阈值（小时）
```

### 4.5 告警配置 API

```python
# app/api/alerts.py (新增)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.device import AlertConfig
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/api/alerts", tags=["告警配置"])

class AlertConfigCreate(BaseModel):
    offline_threshold_hours: int = 48
    check_interval_hours: int = 1

    email_enabled: bool = False
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: Optional[str] = None
    email_to: List[str] = []

    dingtalk_enabled: bool = False
    dingtalk_webhook: Optional[str] = None
    dingtalk_secret: Optional[str] = None

@router.post("/config")
def create_or_update_config(config: AlertConfigCreate, db: Session = Depends(get_db)):
    """创建或更新告警配置"""
    existing = db.query(AlertConfig).first()

    if existing:
        for key, value in config.dict().items():
            if key == "email_to":
                setattr(existing, key, value)  # JSON 字段
            else:
                setattr(existing, key, value)
    else:
        new_config = AlertConfig(**config.dict())
        db.add(new_config)

    db.commit()
    return {"message": "Alert config saved"}

@router.get("/config")
def get_config(db: Session = Depends(get_db)):
    """获取告警配置"""
    config = db.query(AlertConfig).first()
    if not config:
        return {"configured": False}

    return {
        "configured": True,
        "offline_threshold_hours": config.offline_threshold_hours,
        "email_enabled": config.email_enabled,
        "dingtalk_enabled": config.dingtalk_enabled
    }

@router.post("/test")
def test_alert(db: Session = Depends(get_db)):
    """测试告警发送"""
    from app.services.alert_service import AlertService

    alert_service = AlertService(db)
    # 创建测试设备对象
    test_device = type('Device', (), {
        'device_name': '测试设备',
        'device_id': 'test-00000000',
        'timezone': 'Asia/Shanghai',
        'last_online': datetime.utcnow() - timedelta(hours=50)
    })()

    result = alert_service.send_alert([test_device])
    return result
```

---

## 五、播放端增强设计

### 5.1 Web 播放器更新

#### 5.1.1 统一心跳配置

```typescript
// frontend/src/player/config/constants.ts (新增)

export const PLAYER_CONFIG = {
    // 心跳配置
    HEARTBEAT_INTERVAL_MS: 2 * 60 * 60 * 1000,  // 2 小时
    HEARTBEAT_TIMEOUT_MS: 10 * 1000,            // 10 秒超时

    // 下载配置
    DOWNLOAD_TIMEOUT_MS: 30 * 60 * 1000,        // 30 分钟超时
    DOWNLOAD_RETRY_COUNT: 3,                    // 重试次数
    DOWNLOAD_RETRY_DELAY_MS: 5 * 60 * 1000,     // 重试间隔 5 分钟

    // 存储配置
    MIN_FREE_SPACE_MB: 500,                     // 最小保留空间
    MAX_CACHE_SIZE_MB: 5000,                    // 最大缓存大小

    // 错误上报
    ERROR_REPORT_ENABLED: true,
} as const;
```

#### 5.1.2 移除 PlayerCore 中的重复心跳

```typescript
// frontend/src/player/PlayerCore.tsx (修改)

// 删除以下代码（约 154-181 行）:
// heartbeatRef.current = setInterval(sendHeartbeat, 30000);

// 使用统一的 useHeartbeat hook
import { useHeartbeat } from './hooks/useHeartbeat';

export const PlayerCore: React.FC<PlayerCoreProps> = (props) => {
    // ... 其他代码 ...

    // 使用统一的心跳 hook
    useHeartbeat(
        deviceInfo?.device_id || null,
        currentPlaylist?.id || null,
        currentItem?.media_id || null,
        isPlaying ? 'playing' : 'idle'
    );

    // ... 其他代码 ...
};
```

#### 5.1.3 错误上报服务

```typescript
// frontend/src/player/services/ErrorReporter.ts (新增)

import { PLAYER_CONFIG } from '../config/constants';

interface ErrorReport {
    device_id: string;
    error_type: 'download_failed' | 'playback_error' | 'storage_error' | 'network_error';
    error_message: string;
    media_id?: number;
    playlist_id?: number;
    timestamp: string;
}

class ErrorReporter {
    private deviceId: string | null = null;
    private queue: ErrorReport[] = [];
    private isOnline: boolean = navigator.onLine;

    setDeviceId(deviceId: string) {
        this.deviceId = deviceId;
    }

    setOnlineStatus(isOnline: boolean) {
        this.isOnline = isOnline;
        if (isOnline && this.queue.length > 0) {
            this.flushQueue();
        }
    }

    async report(
        errorType: ErrorReport['error_type'],
        message: string,
        context?: { media_id?: number; playlist_id?: number }
    ) {
        if (!this.deviceId) return;

        const report: ErrorReport = {
            device_id: this.deviceId,
            error_type: errorType,
            error_message: message,
            media_id: context?.media_id,
            playlist_id: context?.playlist_id,
            timestamp: new Date().toISOString()
        };

        if (!this.isOnline) {
            this.queue.push(report);
            return;
        }

        await this.sendReport(report);
    }

    private async sendReport(report: ErrorReport) {
        try {
            await fetch('/api/player/devices/notifications', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    device_id: report.device_id,
                    type: report.error_type,
                    error_message: report.error_message,
                    playlist_id: report.playlist_id
                })
            });
        } catch (error) {
            console.error('Failed to send error report:', error);
            this.queue.push(report);
        }
    }

    private async flushQueue() {
        while (this.queue.length > 0) {
            const report = this.queue.shift();
            if (report) {
                await this.sendReport(report);
            }
        }
    }
}

export const errorReporter = new ErrorReporter();
```

### 5.2 Android SDK 增强

#### 5.2.1 增强的缓存管理器

```kotlin
// android/.../CacheManager.kt (重构)

package com.castplay.player

import android.app.DownloadManager
import android.content.Context
import android.net.Uri
import android.os.Environment
import android.util.Log
import kotlinx.coroutines.*
import org.json.JSONObject
import java.io.File
import java.security.MessageDigest
import java.util.concurrent.ConcurrentHashMap

/**
 * 增强的媒体缓存管理器
 * 支持：断点续传、MD5校验、自动重试、存储管理
 */
class CacheManager private constructor(private val context: Context) {

    companion object {
        private const val TAG = "CacheManager"
        private const val MEDIA_DIR = "CastPlay/media"

        // 配置常量
        private const val MAX_RETRY_COUNT = 3
        private const val RETRY_DELAY_MS = 5 * 60 * 1000L  // 5 分钟
        private const val MIN_FREE_SPACE_MB = 500L
        private const val MAX_CACHE_SIZE_MB = 5000L

        @Volatile
        private var instance: CacheManager? = null

        fun getInstance(context: Context): CacheManager {
            return instance ?: synchronized(this) {
                instance ?: CacheManager(context.applicationContext).also { instance = it }
            }
        }
    }

    private val downloadManager: DownloadManager by lazy {
        context.getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager
    }

    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())

    // 下载任务映射
    private val downloadTasks = ConcurrentHashMap<String, DownloadTask>()
    private val downloadProgress = ConcurrentHashMap<String, Int>()

    private val mediaCacheDir: File by lazy {
        File(context.getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS), MEDIA_DIR).apply {
            if (!exists()) mkdirs()
        }
    }

    private val prefs by lazy {
        context.getSharedPreferences("media_cache", Context.MODE_PRIVATE)
    }

    data class DownloadTask(
        val mediaId: String,
        val url: String,
        val md5Hash: String?,
        var retryCount: Int = 0,
        var downloadId: Long? = null,
        var status: Status = Status.PENDING
    ) {
        enum class Status {
            PENDING, DOWNLOADING, COMPLETED, FAILED, RETRYING
        }
    }

    /**
     * 下载媒体文件（带重试和校验）
     */
    fun downloadMedia(
        url: String,
        mediaId: String,
        md5Hash: String? = null,
        onProgress: ((Int) -> Unit)? = null,
        onComplete: ((Boolean, String?) -> Unit)? = null
    ) {
        // 检查是否已缓存
        if (isMediaCached(mediaId)) {
            val path = getCachedMediaPath(mediaId)
            if (verifyMd5(path, md5Hash)) {
                Log.d(TAG, "Media already cached and verified: $mediaId")
                onComplete?.invoke(true, path)
                return
            } else {
                // MD5 不匹配，删除重新下载
                deleteCachedMedia(mediaId)
                Log.w(TAG, "MD5 mismatch, re-downloading: $mediaId")
            }
        }

        // 检查存储空间
        if (!checkStorageSpace()) {
            Log.e(TAG, "Insufficient storage space")
            onComplete?.invoke(false, "Insufficient storage space")
            return
        }

        // 创建下载任务
        val task = DownloadTask(mediaId, url, md5Hash)
        downloadTasks[mediaId] = task

        startDownload(task, onProgress, onComplete)
    }

    private fun startDownload(
        task: DownloadTask,
        onProgress: ((Int) -> Unit)?,
        onComplete: ((Boolean, String?) -> Unit)?
    ) {
        scope.launch {
            try {
                val targetFile = File(mediaCacheDir, task.mediaId)

                val request = DownloadManager.Request(Uri.parse(task.url))
                    .setTitle("CastPlay Media ${task.mediaId}")
                    .setDescription("Downloading media file")
                    .setNotificationVisibility(DownloadManager.Request.VISIBILITY_HIDDEN)
                    .setDestinationUri(Uri.fromFile(targetFile))
                    .setAllowedOverMetered(true)
                    .setAllowedRoaming(true)
                    // 支持断点续传
                    .setAllowedOverMetered(true)

                val downloadId = downloadManager.enqueue(request)
                task.downloadId = downloadId
                task.status = DownloadTask.Status.DOWNLOADING

                // 监控下载进度
                monitorDownload(task, onProgress, onComplete)

            } catch (e: Exception) {
                Log.e(TAG, "Download failed: ${task.mediaId}", e)
                handleDownloadFailure(task, e.message, onComplete)
            }
        }
    }

    private suspend fun monitorDownload(
        task: DownloadTask,
        onProgress: ((Int) -> Unit)?,
        onComplete: ((Boolean, String?) -> Unit)?
    ) {
        val downloadId = task.downloadId ?: return

        while (task.status == DownloadTask.Status.DOWNLOADING) {
            val query = DownloadManager.Query().setFilterById(downloadId)
            val cursor = downloadManager.query(query)

            cursor?.use {
                if (it.moveToFirst()) {
                    val bytesDownloaded = it.getLong(
                        it.getColumnIndex(DownloadManager.COLUMN_BYTES_DOWNLOADED_SO_FAR)
                    )
                    val totalBytes = it.getLong(
                        it.getColumnIndex(DownloadManager.COLUMN_TOTAL_SIZE_BYTES)
                    )
                    val status = it.getInt(
                        it.getColumnIndex(DownloadManager.COLUMN_STATUS)
                    )

                    val progress = if (totalBytes > 0) {
                        ((bytesDownloaded * 100) / totalBytes).toInt()
                    } else 0

                    downloadProgress[task.mediaId] = progress
                    onProgress?.invoke(progress)

                    when (status) {
                        DownloadManager.STATUS_SUCCESSFUL -> {
                            task.status = DownloadTask.Status.COMPLETED
                            downloadProgress[task.mediaId] = 100

                            // 验证 MD5
                            val path = getCachedMediaPath(task.mediaId)
                            if (task.md5Hash != null && !verifyMd5(path, task.md5Hash)) {
                                Log.e(TAG, "MD5 verification failed: ${task.mediaId}")
                                deleteCachedMedia(task.mediaId)
                                handleDownloadFailure(task, "MD5 verification failed", onComplete)
                            } else {
                                // 保存缓存信息
                                saveCacheInfo(task.mediaId, path, task.md5Hash)
                                Log.d(TAG, "Download completed: ${task.mediaId}")
                                onComplete?.invoke(true, path)
                            }
                            return
                        }
                        DownloadManager.STATUS_FAILED -> {
                            val reason = it.getInt(
                                it.getColumnIndex(DownloadManager.COLUMN_REASON)
                            )
                            Log.e(TAG, "Download failed: ${task.mediaId}, reason: $reason")
                            handleDownloadFailure(task, "Download failed: $reason", onComplete)
                            return
                        }
                    }
                }
            }

            delay(1000)
        }
    }

    private fun handleDownloadFailure(
        task: DownloadTask,
        errorMessage: String?,
        onComplete: ((Boolean, String?) -> Unit)?
    ) {
        task.retryCount++

        if (task.retryCount <= MAX_RETRY_COUNT) {
            task.status = DownloadTask.Status.RETRYING
            Log.d(TAG, "Retrying download (${task.retryCount}/$MAX_RETRY_COUNT): ${task.mediaId}")

            // 指数退避
            scope.launch {
                delay(RETRY_DELAY_MS * task.retryCount)
                startDownload(task, null, onComplete)
            }
        } else {
            task.status = DownloadTask.Status.FAILED
            Log.e(TAG, "Download failed after $MAX_RETRY_COUNT retries: ${task.mediaId}")

            // 上报错误
            ErrorReporter.getInstance(context).reportDownloadFailed(
                task.mediaId,
                errorMessage ?: "Max retries exceeded"
            )

            onComplete?.invoke(false, errorMessage)
            downloadTasks.remove(task.mediaId)
        }
    }

    /**
     * 验证文件 MD5
     */
    private fun verifyMd5(filePath: String?, expectedMd5: String?): Boolean {
        if (filePath == null || expectedMd5 == null) return true

        val file = File(filePath)
        if (!file.exists()) return false

        return try {
            val md5 = calculateMd5(file)
            md5.equals(expectedMd5, ignoreCase = true)
        } catch (e: Exception) {
            Log.e(TAG, "MD5 calculation failed", e)
            false
        }
    }

    private fun calculateMd5(file: File): String {
        val md = MessageDigest.getInstance("MD5")
        file.inputStream().use { fis ->
            val buffer = ByteArray(8192)
            var bytesRead: Int
            while (fis.read(buffer).also { bytesRead = it } != -1) {
                md.update(buffer, 0, bytesRead)
            }
        }
        return md.digest().joinToString("") { "%02x".format(it) }
    }

    /**
     * 检查存储空间
     */
    private fun checkStorageSpace(): Boolean {
        val stat = android.os.StatFs(mediaCacheDir.path)
        val freeBytes = stat.availableBlocksLong * stat.blockSizeLong
        val freeMB = freeBytes / (1024 * 1024)

        if (freeMB < MIN_FREE_SPACE_MB) {
            // 尝试清理旧缓存
            cleanupOldCache()
            return checkStorageSpaceAfterCleanup()
        }

        return true
    }

    private fun checkStorageSpaceAfterCleanup(): Boolean {
        val stat = android.os.StatFs(mediaCacheDir.path)
        val freeBytes = stat.availableBlocksLong * stat.blockSizeLong
        return (freeBytes / (1024 * 1024)) >= MIN_FREE_SPACE_MB
    }

    /**
     * 清理旧缓存
     */
    fun cleanupOldCache() {
        Log.d(TAG, "Starting cache cleanup")

        val files = mediaCacheDir.listFiles()?.sortedByDescending { it.lastModified() }
        val currentCacheSize = getCacheSize()
        val maxBytes = MAX_CACHE_SIZE_MB * 1024 * 1024

        if (currentCacheSize > maxBytes) {
            var deletedSize = 0L
            files?.drop(5)?.forEach { file -> // 保留最新的5个文件
                val size = file.length()
                if (file.delete()) {
                    deletedSize += size
                    // 清理 SharedPreferences
                    val mediaId = file.name
                    prefs.edit()
                        .remove("cached_$mediaId")
                        .remove("path_$mediaId")
                        .remove("md5_$mediaId")
                        .apply()
                }

                if (currentCacheSize - deletedSize < maxBytes * 0.8) {
                    return
                }
            }
        }
    }

    // ... 其他现有方法保持不变 ...

    fun isMediaCached(mediaId: String): Boolean {
        return prefs.getBoolean("cached_$mediaId", false)
    }

    fun getCachedMediaPath(mediaId: String): String {
        if (!isMediaCached(mediaId)) return ""

        val storedPath = prefs.getString("path_$mediaId", null)
        if (storedPath != null) {
            val file = File(Uri.parse(storedPath).path ?: return "")
            if (file.exists()) return file.absolutePath
        }

        val defaultFile = File(mediaCacheDir, mediaId)
        return if (defaultFile.exists()) defaultFile.absolutePath else ""
    }

    fun getDownloadProgress(mediaId: String): Int {
        return downloadProgress[mediaId] ?: 0
    }

    fun getCacheSize(): Long {
        return mediaCacheDir.listFiles()?.sumOf { it.length() } ?: 0
    }

    private fun saveCacheInfo(mediaId: String, path: String, md5Hash: String?) {
        prefs.edit()
            .putBoolean("cached_$mediaId", true)
            .putString("path_$mediaId", "file://$path")
            .apply()

        if (md5Hash != null) {
            prefs.edit().putString("md5_$mediaId", md5Hash).apply()
        }
    }

    private fun deleteCachedMedia(mediaId: String) {
        val file = File(mediaCacheDir, mediaId)
        if (file.exists()) file.delete()

        prefs.edit()
            .remove("cached_$mediaId")
            .remove("path_$mediaId")
            .remove("md5_$mediaId")
            .apply()
    }
}
```

#### 5.2.2 错误上报服务

```kotlin
// android/.../ErrorReporter.kt (新增)

package com.castplay.player

import android.content.Context
import android.util.Log
import kotlinx.coroutines.*
import org.json.JSONObject
import java.net.URL
import java.util.concurrent.ConcurrentLinkedQueue

/**
 * 错误上报服务
 */
class ErrorReporter private constructor(private val context: Context) {

    companion object {
        private const val TAG = "ErrorReporter"
        private const val REPORT_URL = "/api/player/devices/notifications"

        @Volatile
        private var instance: ErrorReporter? = null

        fun getInstance(context: Context): ErrorReporter {
            return instance ?: synchronized(this) {
                instance ?: ErrorReporter(context.applicationContext).also { instance = it }
            }
        }
    }

    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private val queue = ConcurrentLinkedQueue<ErrorReport>()
    private val prefs = context.getSharedPreferences("device", Context.MODE_PRIVATE)

    data class ErrorReport(
        val type: String,
        val message: String,
        val playlistId: String? = null,
        val mediaId: String? = null
    )

    fun reportDownloadFailed(mediaId: String, errorMessage: String) {
        report("download_failed", errorMessage, mediaId = mediaId)
    }

    fun reportStorageError(message: String) {
        report("insufficient_storage", message)
    }

    fun reportPlaybackError(message: String, mediaId: String? = null) {
        report("playback_error", message, mediaId = mediaId)
    }

    fun reportSwitchFailed(playlistId: String, errorMessage: String) {
        report("switch_failed", errorMessage, playlistId = playlistId)
    }

    private fun report(
        type: String,
        message: String,
        playlistId: String? = null,
        mediaId: String? = null
    ) {
        val report = ErrorReport(type, message, playlistId, mediaId)

        scope.launch {
            try {
                sendReport(report)
            } catch (e: Exception) {
                Log.w(TAG, "Failed to send report, queuing: $type")
                queue.offer(report)
            }
        }
    }

    fun flushQueue() {
        scope.launch {
            while (queue.isNotEmpty()) {
                val report = queue.poll() ?: break
                try {
                    sendReport(report)
                } catch (e: Exception) {
                    // 放回队列
                    queue.offer(report)
                    break
                }
            }
        }
    }

    private suspend fun sendReport(report: ErrorReport) {
        val deviceId = prefs.getString("device_id", null) ?: return
        val serverUrl = prefs.getString("server_url", "") ?: return

        val json = JSONObject().apply {
            put("device_id", deviceId)
            put("type", report.type)
            put("error_message", report.message)
            report.playlistId?.let { put("playlist_id", it) }
            report.mediaId?.let { put("media_id", it) }
        }

        val url = URL("$serverUrl$REPORT_URL")
        val connection = url.openConnection() as java.net.HttpURLConnection
        connection.requestMethod = "POST"
        connection.setRequestProperty("Content-Type", "application/json")
        connection.doOutput = true
        connection.connectTimeout = 10000
        connection.readTimeout = 10000

        connection.outputStream.use { os ->
            os.write(json.toString().toByteArray(Charsets.UTF_8))
        }

        val responseCode = connection.responseCode
        if (responseCode == 200) {
            Log.d(TAG, "Error report sent: ${report.type}")
        } else {
            throw Exception("HTTP $responseCode")
        }
    }
}
```

#### 5.2.3 开机启动配置

```xml
<!-- android/.../AndroidManifest.xml (确保包含以下配置) -->

<manifest ...>
    <!-- 权限 -->
    <uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" />
    <uses-permission android:name="android.permission.WAKE_LOCK" />
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />

    <application ...>
        <!-- 主 Activity - Kiosk 模式 -->
        <activity
            android:name=".MainActivity"
            android:launchMode="singleTask"
            android:screenOrientation="landscape"
            android:theme="@style/Theme.CastPlay"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
                <category android:name="android.intent.category.HOME" />
                <category android:name="android.intent.category.DEFAULT" />
            </intent-filter>
        </activity>

        <!-- 开机启动接收器 -->
        <receiver
            android:name=".BootReceiver"
            android:enabled="true"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.BOOT_COMPLETED" />
                <action android:name="android.intent.action.QUICKBOOT_POWERON" />
            </intent-filter>
        </receiver>

        <!-- 设备管理员 (可选，用于更严格的 Kiosk 模式) -->
        <receiver
            android:name=".MyDeviceAdminReceiver"
            android:description="@string/device_admin_description"
            android:label="@string/device_admin_label"
            android:permission="android.permission.BIND_DEVICE_ADMIN"
            android:exported="true">
            <meta-data
                android:name="android.app.device_admin"
                android:resource="@xml/device_admin_policies" />
            <intent-filter>
                <action android:name="android.app.action.DEVICE_ADMIN_ENABLED" />
            </intent-filter>
        </receiver>
    </application>
</manifest>
```

```kotlin
// android/.../BootReceiver.kt (完善)

package com.castplay.player

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log

class BootReceiver : BroadcastReceiver() {

    companion object {
        private const val TAG = "BootReceiver"
    }

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Intent.ACTION_BOOT_COMPLETED ||
            intent.action == "android.intent.action.QUICKBOOT_POWERON") {

            Log.i(TAG, "Boot completed, starting CastPlay...")

            // 启动主 Activity
            val launchIntent = Intent(context, MainActivity::class.java).apply {
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP)
            }
            context.startActivity(launchIntent)
        }
    }
}
```

---

## 六、时区处理完善

### 6.1 服务器端时区处理

```python
# app/utils/timezone.py (新增)

from datetime import datetime, timezone
from typing import Optional
import pytz

def convert_to_device_time(
    utc_time: datetime,
    device_timezone: str
) -> datetime:
    """将 UTC 时间转换为设备本地时间"""
    try:
        tz = pytz.timezone(device_timezone)
        return utc_time.replace(tzinfo=timezone.utc).astimezone(tz)
    except Exception:
        return utc_time

def convert_to_utc(
    local_time: datetime,
    device_timezone: str
) -> datetime:
    """将设备本地时间转换为 UTC"""
    try:
        tz = pytz.timezone(device_timezone)
        localized = tz.localize(local_time)
        return localized.astimezone(timezone.utc).replace(tzinfo=None)
    except Exception:
        return local_time

def get_current_time_in_timezone(device_timezone: str) -> datetime:
    """获取指定时区的当前时间"""
    try:
        tz = pytz.timezone(device_timezone)
        return datetime.now(tz)
    except Exception:
        return datetime.now(pytz.UTC)

def is_time_in_range(
    current_time: datetime,
    start_time_str: str,  # "HH:MM"
    end_time_str: str     # "HH:MM"
) -> bool:
    """检查当前时间是否在指定范围内"""
    try:
        current_minutes = current_time.hour * 60 + current_time.minute

        start_parts = start_time_str.split(":")
        start_minutes = int(start_parts[0]) * 60 + int(start_parts[1])

        end_parts = end_time_str.split(":")
        end_minutes = int(end_parts[0]) * 60 + int(end_parts[1])

        return start_minutes <= current_minutes <= end_minutes
    except Exception:
        return True
```

### 6.2 播放列表初始化时返回时区处理后的时间

```python
# app/api/player.py (修改 player_init)

from app.utils.timezone import convert_to_device_time

def player_init(...):
    # ... 现有代码 ...

    if schedule:
        # 转换时间到设备时区
        now_local = convert_to_device_time(datetime.utcnow(), device.timezone)

        schedule_data = {
            "power_on_time": schedule.power_on_time,
            "power_off_time": schedule.power_off_time,
            "is_enabled": schedule.is_enabled,
            "weekdays": schedule.get_weekdays_list(),
            "timezone": device.timezone,
            "current_local_time": now_local.strftime("%H:%M"),
            "current_local_date": now_local.strftime("%Y-%m-%d")
        }

    # ... 现有代码 ...
```

---

## 七、实现优先级和计划

### 7.1 P0 - 必须实现（保证基本可用）

| # | 功能 | 说明 | 预估工作量 | 文件 |
|---|------|------|-----------|------|
| 1 | 统一心跳间隔 | PlayerCore 移除30秒心跳，使用 useHeartbeat | 0.5天 | `PlayerCore.tsx` |
| 2 | 服务器在线阈值调整 | 改为3小时 | 0.5天 | `app/api/player.py` |
| 3 | Android MD5 校验 | 下载后完整性验证 | 0.5天 | `CacheManager.kt` |
| 4 | 告警服务 | 邮件+钉钉通知 | 1.5天 | `app/services/alert_service.py` |
| 5 | 告警配置 API | 前端配置界面 | 0.5天 | `app/api/alerts.py` |
| 6 | 错误上报集成 | 播放端集成上报 | 0.5天 | 多文件 |

**P0 总计: 4天**

### 7.2 P1 - 应该实现（提升稳定性）

| # | 功能 | 说明 | 预估工作量 | 文件 |
|---|------|------|-----------|------|
| 7 | Android 断点续传 | 网络不稳定场景 | 1天 | `CacheManager.kt` |
| 8 | 下载重试机制 | 指数退避策略 | 0.5天 | `CacheManager.kt` |
| 9 | 存储空间管理 | 自动清理策略 | 1天 | `CacheManager.kt` |
| 10 | 时区完善 | 服务器端转换 | 1天 | `app/utils/timezone.py` |

**P1 总计: 3.5天**

### 7.3 P2 - 可以实现（提升体验）

| # | 功能 | 说明 | 预估工作量 | 文件 |
|---|------|------|-----------|------|
| 11 | Web Service Worker | 完善离线体验 | 2天 | `frontend/src/player/services/` |
| 12 | 远程控制指令 | WebSocket 实时控制 | 1天 | 多文件 |
| 13 | 前端告警配置页 | 可视化配置 | 1天 | `frontend/src/pages/` |

**P2 总计: 4天**

---

## 八、测试计划

### 8.1 单元测试

| 模块 | 测试点 |
|------|--------|
| 告警服务 | 离线检测逻辑、邮件发送、钉钉发送 |
| 时区工具 | 时间转换、边界情况 |
| Android 缓存 | MD5 校验、重试逻辑、存储检测 |

### 8.2 集成测试

| 场景 | 验证点 |
|------|--------|
| 设备离线告警 | 模拟离线48小时后收到告警 |
| 播放端错误上报 | 模拟下载失败后服务器收到通知 |
| 心跳间隔验证 | 确认2小时发送一次 |

### 8.3 E2E 测试

| 场景 | 步骤 |
|------|------|
| 完整播放流程 | 设备注册 → 下载内容 → 离线播放 → 心跳上报 |
| 告警流程 | 配置告警 → 模拟离线 → 验证收到通知 |

---

## 九、部署注意事项

### 9.1 服务器端

1. **邮件配置**：需要配置 SMTP 服务器信息
2. **钉钉机器人**：需要创建钉钉群机器人并获取 Webhook
3. **时区数据库**：确保安装 pytz 包

### 9.2 Android 播放端

1. **APK 签名**：使用正式签名证书
2. **权限声明**：确保所有必要权限已声明
3. **设备管理员**：如需严格 Kiosk 模式，需激活设备管理员

### 9.3 Web 播放端

1. **HTTPS**：Service Worker 需要 HTTPS 环境
2. **跨域配置**：确保 CORS 配置正确

---

## 十、风险与缓解措施

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 网络长时间中断 | 无法同步内容 | 本地缓存 + 重连机制 |
| 存储空间耗尽 | 无法下载新内容 | 自动清理旧内容 |
| 邮件/钉钉服务不可用 | 告警无法发送 | 记录日志 + 备用通知渠道 |
| 时区配置错误 | 定时不准确 | 使用标准时区数据库 |

---

## 附录：配置示例

### A.1 告警配置示例

```json
{
    "offline_threshold_hours": 48,
    "check_interval_hours": 1,
    "email_enabled": true,
    "smtp_host": "smtp.example.com",
    "smtp_port": 587,
    "smtp_user": "alerts@example.com",
    "smtp_password": "encrypted_password",
    "email_from": "alerts@example.com",
    "email_to": ["admin1@example.com", "admin2@example.com"],
    "dingtalk_enabled": true,
    "dingtalk_webhook": "https://oapi.dingtalk.com/robot/send?access_token=xxx",
    "dingtalk_secret": "SECxxx"
}
```

### A.2 播放端配置示例

```json
{
    "device_id": "550e8400-e29b-41d4-a716-446655440000",
    "server_url": "https://castplay.example.com",
    "heartbeat_interval_hours": 2,
    "timezone": "America/New_York",
    "cache_max_size_mb": 5000,
    "min_free_space_mb": 500
}
```

---

> 文档结束
