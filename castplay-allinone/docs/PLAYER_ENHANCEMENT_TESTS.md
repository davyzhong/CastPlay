# 播放端功能增强 - 单元测试补充

**执行日期：** 2026-03-06
**测试范围：** Phase 1-5 所有新增功能

---

## 📊 测试概览

### 后端测试用例

#### 1. 数据库模型测试

```python
"""
测试新增的数据库模型
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.device_enhancement import (
    DeviceNotificationLog,
    PlaylistDownloadTask,
    PlaylistCleanupSchedule
)
from app.database import Base


class TestDeviceEnhancementModels:
    """测试新增数据模型"""

    @pytest.fixture
    def test_db(self):
        """测试数据库 fixture"""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def test_create_notification_log(self, test_db):
        """测试创建通知日志"""
        log = DeviceNotificationLog(
            device_id="test-device-001",
            notification_type="download_success",
            message="Download completed successfully",
            playlist_id=123
        )

        test_db.add(log)
        test_db.commit()

        assert log.id is not None
        assert log.created_at is not None

    def test_create_download_task(self, test_db):
        """测试创建下载任务"""
        task = PlaylistDownloadTask(
            device_id="test-device-002",
            playlist_id=456,
            status="pending",
            retry_count=0
        )

        test_db.add(task)
        test_db.commit()

        assert task.id is not None
        assert task.status == "pending"

    def test_create_cleanup_schedule(self, test_db):
        """测试创建清理计划"""
        from datetime import datetime, timedelta

        schedule = PlaylistCleanupSchedule(
            playlist_id=789,
            scheduled_time=datetime.utcnow() + timedelta(hours=24),
            executed=False
        )

        test_db.add(schedule)
        test_db.commit()

        assert schedule.id is not None
        assert schedule.executed is False


class TestDeviceNotificationAPI:
    """测试设备通知 API"""

    def test_receive_download_success(self, client, test_db, mocker):
        """测试接收下载成功通知"""
        mock_commit = mocker.patch.object(type(test_db), "commit")

        response = client.post("/api/player/devices/notifications", json={
            "device_id": "test-device-001",
            "type": "download_success",
            "playlist_id": 123
        })

        assert response.status_code == 200
        data = response.json()
        assert data["acknowledged"] is True

        # 验证数据库调用
        mock_commit.assert_called_once()

    def test_receive_download_failed_with_alert(self, client, test_db, mocker, caplog):
        """测试接收下载失败通知（应触发告警）"""
        mock_commit = mocker.patch.object(type(test_db), "commit")

        response = client.post("/api/player/devices/notifications", json={
            "device_id": "test-device-002",
            "type": "download_failed",
            "playlist_id": 456,
            "error_message": "MD5 mismatch after 3 retries"
        })

        assert response.status_code == 200

        # 验证日志包含告警
        assert "Device alert received" in caplog.text
        assert "download_failed" in caplog.text

    def test_receive_insufficient_storage(self, client, test_db, mocker):
        """测试接收存储空间不足通知"""
        response = client.post("/api/player/devices/notifications", json={
            "device_id": "test-device-003",
            "type": "insufficient_storage",
            "playlist_id": 789,
            "error_message": "Required: 500MB, Available: 100MB"
        })

        assert response.status_code == 200


class TestAvailablePlaylistsAPI:
    """测试可用播放列表 API"""

    def test_get_available_playlists_empty(self, client, test_db, mocker):
        """测试获取空播放列表"""
        mock_query = mocker.MagicMock()
        mock_query.filter.return_value.all.return_value = []
        test_db.query = mocker.MagicMock(return_value=mock_query)

        response = client.get("/api/player/playlists/available")

        assert response.status_code == 200
        data = response.json()
        assert len(data["playlists"]) == 0

    def test_get_available_playlists_with_data(self, client, test_db, mocker):
        """测试获取播放列表（有数据）"""
        # Mock 播放列表
        mock_playlist = mocker.MagicMock()
        mock_playlist.id = 1
        mock_playlist.name = "企业宣传片"
        mock_playlist.is_system = True

        # Mock 播放列表项
        mock_item = mocker.MagicMock()
        mock_item.media_file.file_size = 1024 * 1024 * 100  # 100MB

        test_db.query().filter().all.side_effect = [
            [mock_playlist],  # 播放列表查询
            [mock_item]       # 播放列表项查询
        ]

        response = client.get("/api/player/playlists/available")

        assert response.status_code == 200
        data = response.json()
        assert len(data["playlists"]) > 0
        assert data["playlists"][0]["name"] == "企业宣传片"
        assert data["playlists"][0]["media_count"] == 1


class TestHeartbeatWithPush:
    """测试心跳推送机制"""

    def test_heartbeat_with_completed_task(self, client, test_db, mocker):
        """测试心跳时有已完成的下载任务"""
        # Mock 已完成的下载任务
        mock_task = mocker.MagicMock()
        mock_task.device_id = "test-device-005"
        mock_task.status = "completed"
        mock_task.playlist_id = 123

        test_db.query().filter().first.return_value = mock_task

        # Mock 播放列表
        mock_playlist = mocker.MagicMock()
        mock_playlist.id = 123
        mock_playlist.name = "新产品介绍"
        mock_playlist.updated_at = None

        test_db.query().filter().first.return_value = mock_playlist
        test_db.query().filter().all.return_value = []

        response = client.post("/api/player/heartbeat", json={
            "device_id": "test-device-005",
            "current_playlist_id": 1,
            "status": "playing"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["playlist_update"] is not None
        assert data["playlist_update"]["has_update"] is True

    def test_heartbeat_without_update(self, client, test_db, mocker):
        """测试心跳时无更新"""
        test_db.query().filter().first.return_value = None

        response = client.post("/api/player/heartbeat", json={
            "device_id": "test-device-006",
            "current_playlist_id": 1,
            "status": "playing"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["playlist_update"] is None
```

---

### 前端测试用例

#### 2. 组件和 Hook 测试

```typescript
/**
 * 测试设备 ID 展示组件
 */
import React from "react";
import { render, screen } from "@testing-library/react";
import { DeviceIdDisplay } from "../components/DeviceIdDisplay";

describe("DeviceIdDisplay", () => {
  it("should display first 4 characters of device ID", () => {
    const deviceId = "550e8400-e29b-41d4-a716-446655440000";
    render(<DeviceIdDisplay deviceId={deviceId} />);

    expect(screen.getByText("550e")).toBeInTheDocument();
  });

  it("should apply low visibility styles", () => {
    const { container } = render(<DeviceIdDisplay deviceId="test123" />);

    const element = container.firstChild as HTMLElement;
    const styles = window.getComputedStyle(element);

    expect(styles.opacity).toBe("0.4");
    expect(styles.pointerEvents).toBe("none");
  });
});

/**
 * 测试播放列表选择 Hook
 */
import { renderHook, waitFor } from "@testing-library/react";
import { usePlaylistSelection } from "../hooks/usePlaylistSelection";

describe("usePlaylistSelection", () => {
  beforeEach(() => {
    localStorage.clear();
    global.fetch = jest.fn();
  });

  it("should load available playlists on mount", async () => {
    const mockPlaylists = [
      { id: 1, name: "企业宣传片", media_count: 5, total_size_mb: 1250 },
    ];

    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ playlists: mockPlaylists }),
    });

    const { result } = renderHook(() => usePlaylistSelection("test-device"));

    await waitFor(() => {
      expect(result.current.availablePlaylists).toHaveLength(1);
    });
  });

  it("should handle storage check failure", async () => {
    const { result } = renderHook(() => usePlaylistSelection("test-device"));

    await result.current.selectPlaylist({
      id: 1,
      name: "Test Playlist",
      media_count: 5,
      total_size_mb: 1000,
    });

    // 应该调用 fetch 检查存储
    expect(global.fetch).toHaveBeenCalled();
  });
});

/**
 * 测试下载管理器
 */
import { DownloadManager, DownloadState } from "../services/DownloadManager";

describe("DownloadManager", () => {
  let downloadManager: DownloadManager;

  beforeEach(() => {
    downloadManager = new DownloadManager("test-device");
  });

  it("should calculate priority correctly for images", () => {
    const priority = (downloadManager as any).calculatePriority("image/jpeg");
    expect(priority).toBe(1); // 最高优先级
  });

  it("should calculate priority correctly for videos", () => {
    const priority = (downloadManager as any).calculatePriority("video/mp4");
    expect(priority).toBe(2);
  });

  it("should handle retry logic", async () => {
    const mockTask = {
      id: "task-001",
      url: "http://example.com/file.mp4",
      targetPath: "/path/to/file",
      mediaType: "video/mp4",
      playlistId: 123,
      retryCount: 0,
    };

    // Mock notifyServer
    const notifySpy = jest.spyOn(downloadManager as any, "notifyServer");

    // 模拟 3 次失败
    for (let i = 0; i < 3; i++) {
      await (downloadManager as any).handleRetry(
        mockTask,
        new Error("Network error")
      );
    }

    // 第 3 次失败后应该通知服务端
    expect(notifySpy).toHaveBeenCalled();
  });

  it("should check storage space", async () => {
    // Mock navigator.storage.estimate
    Object.defineProperty(navigator, "storage", {
      value: {
        estimate: jest.fn().mockResolvedValue({
          quota: 1024 * 1024 * 1000, // 1000MB
        }),
      },
    });

    const hasSpace = await downloadManager.checkStorageSpace(500); // 需要 500MB
    expect(hasSpace).toBe(true);
  });
});

/**
 * 测试切换管理器
 */
import { SwitchManager, SwitchStatus } from "../services/SwitchManager";

describe("SwitchManager", () => {
  let switchManager: SwitchManager;

  beforeEach(() => {
    switchManager = new SwitchManager({
      deviceId: "test-device",
      onSwitchComplete: jest.fn(),
      onSwitchFailed: jest.fn(),
    });
  });

  it("should start in IDLE state", () => {
    expect(switchManager.getStatus()).toBe(SwitchStatus.IDLE);
  });

  it("should schedule switch and wait for playlist end", async () => {
    await switchManager.scheduleSwitch(123, 456);

    expect(switchManager.getStatus()).toBe(SwitchStatus.WAITING_PLAYLIST_END);
    expect(switchManager.getTargetPlaylistId()).toBe(123);
  });

  it("should cancel switch when requested", async () => {
    await switchManager.scheduleSwitch(123, 456);
    switchManager.cancel();

    expect(switchManager.getStatus()).toBe(SwitchStatus.IDLE);
    expect(switchManager.getTargetPlaylistId()).toBeNull();
  });

  it("should set playing status", () => {
    switchManager.setPlayingStatus(true);
    expect((switchManager as any).isPlaying).toBe(true);
  });
});

/**
 * 测试清理管理器
 */
import { CleanupManager } from "../services/CleanupManager";

describe("CleanupManager", () => {
  let cleanupManager: CleanupManager;

  beforeEach(() => {
    localStorage.clear();
    cleanupManager = new CleanupManager({
      deviceId: "test-device",
    });
  });

  it("should schedule cleanup", async () => {
    await cleanupManager.scheduleCleanup(123);

    const schedules = await cleanupManager.getScheduledCleanupsList();
    expect(schedules).toHaveLength(1);
    expect(schedules[0].playlistId).toBe(123);
  });

  it("should verify cleanup conditions", async () => {
    // 设置激活的播放列表
    localStorage.setItem("castplay_current_playlist_id", "456");
    localStorage.setItem(
      "castplay_playlist_activated_456",
      Date.now().toString()
    );

    const canCleanup = await (cleanupManager as any).verifyCleanupConditions(
      123
    );
    expect(canCleanup).toBe(false); // 未满 24 小时
  });

  it("should cancel cleanup when requested", async () => {
    await cleanupManager.scheduleCleanup(123);
    await cleanupManager.cancelCleanup(123);

    const schedules = await cleanupManager.getScheduledCleanupsList();
    expect(schedules).toHaveLength(0);
  });
});
```

---

## 📋 测试执行计划

### 后端测试

```bash
# 运行所有新增测试
cd /Users/Davy/PycharmProjects/CastPlay/castplay-allinone
python -m pytest tests/test_enhancements.py -v --tb=short

# 运行特定测试类
python -m pytest tests/test_enhancements.py::TestDeviceNotifications -v

# 生成覆盖率报告
python -m pytest tests/test_enhancements.py --cov=app/api/player --cov-report=html
```

### 前端测试

```bash
# 运行所有前端测试
cd /Users/Davy/PycharmProjects/CastPlay/castplay-allinone/frontend
npm test -- src/player/services/__tests__/DownloadManager.test.ts

# 运行组件测试
npm test -- src/player/components/__tests__/DeviceIdDisplay.test.tsx

# 生成覆盖率报告
npm test -- --coverage
```

---

## 📊 预期测试覆盖率

| 模块                             | 目标覆盖率 | 当前覆盖率 |
| -------------------------------- | ---------- | ---------- |
| app/models/device_enhancement.py | 90%        | 待测试     |
| app/api/player.py (新增部分)     | 85%        | 待测试     |
| DownloadManager.ts               | 80%        | 待测试     |
| SwitchManager.ts                 | 80%        | 待测试     |
| CleanupManager.ts                | 80%        | 待测试     |
| usePlaylistSelection.ts          | 75%        | 待测试     |

**总体目标：** 80%+

---

## ✅ 测试验收标准

- [ ] 所有 P0/P1 问题修复后有测试覆盖
- [ ] 核心功能（下载、切换、清理）测试通过率 100%
- [ ] 边界场景测试完整
- [ ] 错误处理测试完整
- [ ] 整体覆盖率 > 80%
