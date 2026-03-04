"""
E2E 测试环境验证 - 验证测试基础设施是否正常工作
"""
import pytest
import subprocess
import os
import requests
import time
from datetime import datetime


class TestEnvironmentValidation:
    """测试环境验证"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """测试准备"""
        self.android_home = os.environ.get(
            "ANDROID_HOME",
            "/Users/Davy/PycharmProjects/CastPlay/android-sdk"
        )
        self.adb = os.path.join(self.android_home, "platform-tools", "adb")
        self.appium_url = "http://127.0.0.1:4723"

    def test_appium_server_running(self):
        """测试 Appium 服务器是否运行"""
        try:
            resp = requests.get(f"{self.appium_url}/status", timeout=5)
            assert resp.status_code == 200, f"Appium 状态码异常: {resp.status_code}"
            status = resp.json()
            assert status.get("value", {}).get("ready") is True, "Appium 未就绪"
            print(f"\n✓ Appium 服务器正常运行")
            print(
                f"  版本: {status.get('value', {}).get('build', {}).get('version', 'N/A')}")
        except requests.exceptions.ConnectionError:
            pytest.fail("Appium 服务器未运行")

    def test_emulator_connected(self):
        """测试模拟器是否连接"""
        result = subprocess.run(
            [self.adb, "devices"],
            capture_output=True,
            text=True
        )
        assert "emulator" in result.stdout, "未检测到模拟器连接"
        assert "device" in result.stdout, "模拟器状态异常"

        # 提取模拟器信息
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if "emulator" in line and "device" in line:
                serial = line.split()[0]
                print(f"\n✓ 模拟器已连接: {serial}")
                break

    def test_emulator_boot_completed(self):
        """测试模拟器是否启动完成"""
        result = subprocess.run(
            [self.adb, "shell", "getprop", "sys.boot_completed"],
            capture_output=True,
            text=True
        )
        boot_completed = result.stdout.strip()
        assert boot_completed == "1", f"模拟器未完全启动: {boot_completed}"
        print(f"\n✓ 模拟器启动完成")

    def test_android_sdk_components(self):
        """测试 Android SDK 组件是否完整"""
        components = {
            "emulator": os.path.join(self.android_home, "emulator", "emulator"),
            "adb": self.adb,
            "platform-tools": os.path.join(self.android_home, "platform-tools"),
            "system-images": os.path.join(self.android_home, "system-images"),
        }

        missing = []
        for name, path in components.items():
            if not os.path.exists(path):
                missing.append(name)

        assert not missing, f"缺少 SDK 组件: {missing}"
        print(f"\n✓ Android SDK 组件完整")
        for name, path in components.items():
            print(f"  - {name}: {path}")

    def test_appium_can_start_session(self):
        """测试 Appium 是否能启动会话（使用浏览器）"""
        from appium import webdriver
        from appium.options.android import UiAutomator2Options

        options = UiAutomator2Options()
        options.platform_name = "Android"
        options.device_name = "emulator-5554"
        options.automation_name = "UiAutomator2"
        # 使用设置应用测试
        options.app_package = "com.android.settings"
        options.app_activity = ".Settings"
        options.no_reset = True
        options.new_command_timeout = 60

        driver = None
        try:
            driver = webdriver.Remote(
                command_executor=self.appium_url,
                options=options
            )

            # 验证会话创建成功
            assert driver.session_id is not None, "会话创建失败"

            # 获取当前 activity
            current_activity = driver.current_activity
            assert current_activity is not None, "无法获取当前 activity"

            print(f"\n✓ Appium 会话创建成功")
            print(f"  Session ID: {driver.session_id}")
            print(f"  Current Activity: {current_activity}")

        finally:
            if driver:
                driver.quit()

    def test_backend_server_accessible(self):
        """测试后端服务器是否可访问（如果运行中）"""
        backend_url = "http://127.0.0.1:5001"
        try:
            resp = requests.get(f"{backend_url}/api/health", timeout=5)
            if resp.status_code == 200:
                print(f"\n✓ 后端服务器运行中")
                print(f"  URL: {backend_url}")
            else:
                print(f"\n⚠ 后端服务器响应异常: {resp.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"\n⚠ 后端服务器未运行 (可选)")
            # 不作为失败条件
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
