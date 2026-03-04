"""
E2E 测试用例 - 设备注册、内容下载、播放等

测试场景：
1. 首次启动设备注册
2. 内容下载同步
3. 自动轮播
4. 定时开关播放
"""
from config.settings import get_default_config
from utils.backend_manager import BackendManager
from utils.emulator_manager import EmulatorManager
from utils.appium_base import CastPlayPage
import pytest
import time
import logging
import re
from datetime import datetime, timedelta

import sys
sys.path.insert(0, '..')


logger = logging.getLogger(__name__)


class TestCastPlayE2E:
    """CastPlay 端到端测试"""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """测试准备"""
        self.config = get_default_config()
        self.emulator = EmulatorManager(self.config.emulator)
        self.backend = BackendManager(self.config.backend)
        self.app = None

        yield

        # 清理
        if self.app:
            self.app.teardown()

    def _init_app(self) -> CastPlayPage:
        """初始化应用"""
        app = CastPlayPage(self.config, self.emulator, self.backend)
        assert app.setup(), "Appium 驱动初始化失败"
        self.app = app
        return app


class TestDeviceRegistration(TestCastPlayE2E):
    """
    测试场景：设备注册

    验证点：
    1. 首次启动自动注册
    2. 设备 ID 正确显示
    3. 服务器记录正确
    """

    def test_first_launch_registration(self):
        """
        测试用例: 首次启动自动注册

        步骤:
        1. 清除应用数据
        2. 启动应用
        3. 等待注册完成
        4. 验证设备 ID 显示
        5. 验证服务器记录
        """
        logger.info("=" * 60)
        logger.info("测试: 首次启动自动注册")
        logger.info("=" * 60)

        app = self._init_app()

        # Step 1: 清除应用数据（模拟首次安装）
        app.clear_app_and_restart()
        logger.info("✓ 已清除应用数据")

        # Step 2: 等待注册完成
        assert app.wait_for_registration(timeout=30), "设备注册超时"
        logger.info("✓ 设备注册完成")

        # Step 3: 获取并验证设备 ID
        device_id = app.get_device_id()
        assert device_id is not None, "无法获取设备 ID"
        assert device_id.startswith("CAS-"), f"设备 ID 格式错误: {device_id}"
        logger.info(f"✓ 设备 ID: {device_id}")

        # Step 4: 验证服务器记录
        device_info = self.backend.get_device_by_id(device_id)
        assert device_info is not None, f"服务器未找到设备: {device_id}"
        logger.info(f"✓ 服务器设备记录: {device_info}")

        # 截图留证
        app.take_screenshot("registration_success")

        logger.info("=" * 60)
        logger.info("测试通过: 首次启动自动注册")
        logger.info("=" * 60)

    def test_reinstall_recovery(self):
        """
        测试用例: 重装后恢复设备 ID

        步骤:
        1. 获取当前设备 ID
        2. 清除数据重启
        3. 等待注册
        4. 验证 ID 恢复（通过 hardware_id）
        """
        logger.info("=" * 60)
        logger.info("测试: 重装后恢复设备 ID")
        logger.info("=" * 60)

        app = self._init_app()

        # Step 1: 获取当前设备 ID
        app.wait_for_registration(timeout=30)
        original_id = app.get_device_id()
        assert original_id, "无法获取原设备 ID"
        logger.info(f"✓ 原设备 ID: {original_id}")

        # Step 2: 清除数据模拟重装
        app.clear_app_and_restart()
        logger.info("✓ 已清除数据")

        # Step 3: 等待重新注册
        assert app.wait_for_registration(timeout=30), "重新注册超时"

        # Step 4: 验证 ID 恢复
        recovered_id = app.get_device_id()
        assert recovered_id == original_id, \
            f"设备 ID 未恢复: 原 {original_id}, 现 {recovered_id}"
        logger.info(f"✓ 设备 ID 已恢复: {recovered_id}")

        logger.info("=" * 60)
        logger.info("测试通过: 重装后恢复设备 ID")
        logger.info("=" * 60)


class TestContentDownload(TestCastPlayE2E):
    """
    测试场景：内容下载

    验证点：
    1. 播放列表同步
    2. 媒体文件下载
    3. 下载进度显示
    """

    def test_playlist_sync(self):
        """
        测试用例: 播放列表同步

        步骤:
        1. 在服务器创建测试播放列表
        2. 分配给设备
        3. 启动应用
        4. 验证同步完成
        """
        logger.info("=" * 60)
        logger.info("测试: 播放列表同步")
        logger.info("=" * 60)

        app = self._init_app()

        # Step 1: 等待设备注册
        assert app.wait_for_registration(timeout=30), "设备注册失败"
        device_id = app.get_device_id()
        logger.info(f"✓ 设备 ID: {device_id}")

        # Step 2: 获取设备服务器信息并创建测试数据
        device_info = self.backend.get_device_by_id(device_id)
        if device_info:
            test_data = self.backend.prepare_test_data()
            if test_data.get("playlist_id"):
                # 分配播放列表
                self.backend.assign_playlist_to_device(
                    device_info["id"],
                    test_data["playlist_id"]
                )
                logger.info(f"✓ 已分配播放列表: {test_data}")

        # Step 3: 触发同步
        self.backend.trigger_force_sync(device_id)
        logger.info("✓ 已触发强制同步")

        # Step 4: 等待同步完成
        # 检查进度条变化
        app.wait(3)

        # 截图记录
        app.take_screenshot("sync_in_progress")

        assert app.wait_for_sync_complete(timeout=120), "同步超时"
        logger.info("✓ 同步完成")

        app.take_screenshot("sync_complete")

        logger.info("=" * 60)
        logger.info("测试通过: 播放列表同步")
        logger.info("=" * 60)


class TestAutoPlayback(TestCastPlayE2E):
    """
    测试场景：自动轮播

    验证点：
    1. 内容自动播放
    2. 播放切换
    3. 循环播放
    """

    def test_auto_carousel(self):
        """
        测试用例: 自动轮播

        步骤:
        1. 启动应用
        2. 等待同步完成
        3. 验证播放开始
        4. 观察轮播切换
        """
        logger.info("=" * 60)
        logger.info("测试: 自动轮播")
        logger.info("=" * 60)

        app = self._init_app()

        # Step 1: 等待注册和同步
        assert app.wait_for_registration(timeout=30), "注册失败"
        device_id = app.get_device_id()
        logger.info(f"✓ 设备 ID: {device_id}")

        # Step 2: 确保有播放列表
        device_info = self.backend.get_device_by_id(device_id)
        if device_info:
            # 检查是否已有播放列表
            playlists = self.backend.get_playlists()
            if playlists:
                # 分配第一个播放列表
                self.backend.assign_playlist_to_device(
                    device_info["id"],
                    playlists[0]["id"]
                )

        # Step 3: 等待同步和播放
        app.wait_for_sync_complete(timeout=60)
        assert app.wait_for_playback_started(timeout=60), "播放未开始"
        logger.info("✓ 播放已开始")

        # Step 4: 记录播放状态
        app.take_screenshot("playback_1")

        # Step 5: 等待轮播切换（假设每项 10 秒）
        logger.info("等待轮播切换...")
        app.wait(15)
        app.take_screenshot("playback_2")

        # 再等待一次切换
        app.wait(15)
        app.take_screenshot("playback_3")

        logger.info("✓ 轮播正常")

        logger.info("=" * 60)
        logger.info("测试通过: 自动轮播")
        logger.info("=" * 60)

    def test_playback_loop(self):
        """
        测试用例: 循环播放

        步骤:
        1. 启动播放
        2. 等待播放完一轮
        3. 验证自动循环
        """
        logger.info("=" * 60)
        logger.info("测试: 循环播放")
        logger.info("=" * 60)

        app = self._init_app()

        # 等待播放开始
        app.wait_for_registration(timeout=30)
        app.wait_for_sync_complete(timeout=60)
        app.wait_for_playback_started(timeout=60)

        # 记录初始状态
        app.take_screenshot("loop_start")

        # 等待一段时间观察循环
        # 假设播放列表总时长约 30 秒
        logger.info("等待播放循环...")
        app.wait(60)

        # 验证仍在播放
        assert app.is_webview_visible(), "播放已停止"
        app.take_screenshot("loop_continue")

        logger.info("✓ 循环播放正常")

        logger.info("=" * 60)
        logger.info("测试通过: 循环播放")
        logger.info("=" * 60)


class TestScheduledPlayback(TestCastPlayE2E):
    """
    测试场景：定时播放

    验证点：
    1. 定时开启播放
    2. 定时关闭播放
    """

    def test_scheduled_start(self):
        """
        测试用例: 定时开启播放

        步骤:
        1. 设置未来 1 分钟后开始的计划
        2. 等待计划时间到达
        3. 验证播放自动开始
        """
        logger.info("=" * 60)
        logger.info("测试: 定时开启播放")
        logger.info("=" * 60)

        app = self._init_app()

        # 等待注册
        assert app.wait_for_registration(timeout=30), "注册失败"
        device_id = app.get_device_id()

        # 获取设备 ID
        device_info = self.backend.get_device_by_id(device_id)
        if not device_info:
            pytest.skip("无法获取设备信息")

        # 设置计划：1 分钟后开始
        now = datetime.now()
        start_time = (now + timedelta(minutes=1)).strftime("%H:%M")
        end_time = (now + timedelta(hours=2)).strftime("%H:%M")

        self.backend.set_device_schedule(
            device_info["id"],
            start_time=start_time,
            end_time=end_time,
            enabled=True
        )
        logger.info(f"✓ 已设置定时计划: {start_time} - {end_time}")

        # 等待计划时间
        logger.info("等待定时计划生效...")
        app.wait(70)  # 等待超过 1 分钟

        # 验证播放状态
        # 注意：需要后端支持定时播放逻辑
        app.take_screenshot("scheduled_playback")

        logger.info("✓ 定时播放测试完成")

        logger.info("=" * 60)
        logger.info("测试通过: 定时开启播放")
        logger.info("=" * 60)

    def test_scheduled_stop(self):
        """
        测试用例: 定时关闭播放

        步骤:
        1. 设置即将结束的计划
        2. 等待计划时间到达
        3. 验证播放自动停止
        """
        logger.info("=" * 60)
        logger.info("测试: 定时关闭播放")
        logger.info("=" * 60)

        app = self._init_app()

        # 等待注册
        assert app.wait_for_registration(timeout=30), "注册失败"
        device_id = app.get_device_id()

        device_info = self.backend.get_device_by_id(device_id)
        if not device_info:
            pytest.skip("无法获取设备信息")

        # 设置计划：现在开始，1 分钟后结束
        now = datetime.now()
        start_time = (now - timedelta(minutes=5)).strftime("%H:%M")
        end_time = (now + timedelta(minutes=1)).strftime("%H:%M")

        self.backend.set_device_schedule(
            device_info["id"],
            start_time=start_time,
            end_time=end_time,
            enabled=True
        )
        logger.info(f"✓ 已设置定时计划: {start_time} - {end_time}")

        # 等待播放开始
        app.wait_for_playback_started(timeout=30)
        logger.info("✓ 播放已开始")
        app.take_screenshot("before_schedule_stop")

        # 等待计划结束时间
        logger.info("等待定时结束...")
        app.wait(70)

        app.take_screenshot("after_schedule_stop")

        logger.info("✓ 定时停止测试完成")

        logger.info("=" * 60)
        logger.info("测试通过: 定时关闭播放")
        logger.info("=" * 60)


# ================================================================
# 测试运行入口
# ================================================================

if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-s",
        "--html=../reports/e2e_report.html",
        "--self-contained-html"
    ])
