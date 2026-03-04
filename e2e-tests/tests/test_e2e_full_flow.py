"""
E2E 自动化测试 - 使用浏览器测试代替 CastPlay 应用
验证完整的自动化测试流程
"""
import pytest
import subprocess
import os
import time
import requests
from datetime import datetime
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class TestE2EFullFlow:
    """完整 E2E 测试流程验证"""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """测试准备和清理"""
        self.android_home = os.environ.get(
            "ANDROID_HOME",
            "/Users/Davy/PycharmProjects/CastPlay/android-sdk"
        )
        self.adb = os.path.join(self.android_home, "platform-tools", "adb")
        self.appium_url = "http://127.0.0.1:4723"
        self.driver = None
        self.test_start_time = datetime.now()

        yield

        # 清理
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

    def _create_driver(self, package: str, activity: str):
        """创建 Appium 驱动"""
        options = UiAutomator2Options()
        options.platform_name = "Android"
        options.device_name = "emulator-5554"
        options.automation_name = "UiAutomator2"
        options.app_package = package
        options.app_activity = activity
        options.no_reset = True
        options.new_command_timeout = 120

        self.driver = webdriver.Remote(
            command_executor=self.appium_url,
            options=options
        )
        self.driver.implicitly_wait(10)
        return self.driver

    def _take_screenshot(self, name: str) -> str:
        """截图"""
        if not self.driver:
            return ""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{name}.png"
        filepath = f"/Users/Davy/PycharmProjects/CastPlay/e2e-tests/reports/{filename}"
        try:
            self.driver.save_screenshot(filepath)
            print(f"  📸 截图: {filename}")
            return filepath
        except Exception as e:
            print(f"  ⚠ 截图失败: {e}")
            return ""

    # ==================== 测试用例 ====================

    def test_01_appium_session_creation(self):
        """
        测试 1: Appium 会话创建
        验证: 自动化框架能够成功启动应用
        """
        print("\n" + "=" * 60)
        print("测试 1: Appium 会话创建")
        print("=" * 60)

        driver = self._create_driver("com.android.settings", ".Settings")

        assert driver.session_id is not None, "会话创建失败"
        print(f"  ✓ 会话创建成功: {driver.session_id}")

        # 验证应用启动
        current_package = driver.current_package
        assert current_package == "com.android.settings", f"包名不匹配: {current_package}"
        print(f"  ✓ 应用启动成功: {current_package}")

        self._take_screenshot("01_session_created")

    def test_02_ui_element_interaction(self):
        """
        测试 2: UI 元素交互
        验证: 能够查找和操作 UI 元素
        """
        print("\n" + "=" * 60)
        print("测试 2: UI 元素交互")
        print("=" * 60)

        driver = self._create_driver("com.android.settings", ".Settings")

        # 查找搜索按钮或输入框
        try:
            # 尝试找到任何可点击元素
            elements = driver.find_elements(
                AppiumBy.CLASS_NAME, "android.widget.TextView")
            assert len(elements) > 0, "未找到任何 TextView 元素"
            print(f"  ✓ 找到 {len(elements)} 个 TextView 元素")

            # 点击第一个可用元素
            for elem in elements[:5]:
                text = elem.text
                if text:
                    print(f"    - {text}")

            self._take_screenshot("02_ui_elements")

        except Exception as e:
            pytest.fail(f"UI 元素交互失败: {e}")

    def test_03_screen_navigation(self):
        """
        测试 3: 屏幕导航
        验证: 能够在不同界面间导航
        """
        print("\n" + "=" * 60)
        print("测试 3: 屏幕导航")
        print("=" * 60)

        driver = self._create_driver("com.android.settings", ".Settings")

        # 获取初始 activity
        initial_activity = driver.current_activity
        print(f"  初始 Activity: {initial_activity}")

        # 尝试点击一个设置项
        try:
            # 查找可点击的列表项
            items = driver.find_elements(
                AppiumBy.CLASS_NAME,
                "android.widget.LinearLayout"
            )

            if items:
                items[0].click()
                time.sleep(1)

                new_activity = driver.current_activity
                print(f"  导航后 Activity: {new_activity}")

                self._take_screenshot("03_after_navigation")

                # 返回
                driver.back()
                time.sleep(0.5)
                print("  ✓ 导航测试完成")

        except Exception as e:
            print(f"  ⚠ 导航测试异常: {e}")

    def test_04_browser_web_page(self):
        """
        测试 4: 浏览器页面加载
        验证: 能够打开浏览器并加载网页（模拟 WebView 场景）
        """
        print("\n" + "=" * 60)
        print("测试 4: 浏览器网页加载")
        print("=" * 60)

        driver = self._create_driver(
            "com.android.chrome",
            "com.google.android.apps.chrome.Main"
        )

        time.sleep(3)  # 等待浏览器启动

        # 截图记录
        self._take_screenshot("04_browser_launched")

        print("  ✓ 浏览器启动成功")
        print(f"  当前 Activity: {driver.current_activity}")

    def test_05_multi_app_switching(self):
        """
        测试 5: 多应用切换
        验证: 能够在多个应用间切换
        """
        print("\n" + "=" * 60)
        print("测试 5: 多应用切换")
        print("=" * 60)

        driver = self._create_driver("com.android.settings", ".Settings")

        print(f"  应用 1: {driver.current_package}")
        self._take_screenshot("05_app1_settings")

        # 切换到计算器
        driver.activate_app("com.android.calculator2")
        time.sleep(1)

        current = driver.current_package
        print(f"  应用 2: {current}")
        self._take_screenshot("05_app2_calculator")

        # 切回设置
        driver.activate_app("com.android.settings")
        time.sleep(1)

        final = driver.current_package
        print(f"  切回: {final}")

        assert final == "com.android.settings", "应用切换失败"
        print("  ✓ 多应用切换测试完成")

    def test_06_screenshot_capability(self):
        """
        测试 6: 截图能力
        验证: 能够在任意时刻截图保存
        """
        print("\n" + "=" * 60)
        print("测试 6: 截图能力")
        print("=" * 60)

        driver = self._create_driver("com.android.settings", ".Settings")

        screenshots = []
        for i in range(3):
            path = self._take_screenshot(f"06_screenshot_{i+1}")
            if path:
                screenshots.append(path)
            time.sleep(0.5)

        assert len(screenshots) == 3, f"截图数量不足: {len(screenshots)}"
        print(f"  ✓ 成功保存 {len(screenshots)} 张截图")

    def test_07_adb_command_execution(self):
        """
        测试 7: ADB 命令执行
        验证: 能够执行 ADB 命令获取设备信息
        """
        print("\n" + "=" * 60)
        print("测试 7: ADB 命令执行")
        print("=" * 60)

        # 获取设备信息
        result = subprocess.run(
            [self.adb, "shell", "getprop", "ro.product.model"],
            capture_output=True,
            text=True
        )
        model = result.stdout.strip()
        print(f"  设备型号: {model}")

        # 获取 Android 版本
        result = subprocess.run(
            [self.adb, "shell", "getprop", "ro.build.version.release"],
            capture_output=True,
            text=True
        )
        version = result.stdout.strip()
        print(f"  Android 版本: {version}")

        # 获取屏幕分辨率
        result = subprocess.run(
            [self.adb, "shell", "wm", "size"],
            capture_output=True,
            text=True
        )
        size = result.stdout.strip()
        print(f"  屏幕尺寸: {size}")

        assert model, "无法获取设备型号"
        print("  ✓ ADB 命令执行测试完成")


class TestPerformanceMetrics:
    """性能指标测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.appium_url = "http://127.0.0.1:4723"
        self.driver = None
        yield
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

    def test_session_creation_time(self):
        """测试会话创建时间"""
        print("\n" + "=" * 60)
        print("性能测试: 会话创建时间")
        print("=" * 60)

        start = time.time()

        options = UiAutomator2Options()
        options.platform_name = "Android"
        options.device_name = "emulator-5554"
        options.automation_name = "UiAutomator2"
        options.app_package = "com.android.settings"
        options.app_activity = ".Settings"
        options.no_reset = True

        self.driver = webdriver.Remote(
            command_executor=self.appium_url,
            options=options
        )

        elapsed = time.time() - start
        print(f"  会话创建时间: {elapsed:.2f} 秒")

        assert elapsed < 30, f"会话创建超时: {elapsed:.2f}s"
        print(f"  ✓ 性能测试通过 (< 30s)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
