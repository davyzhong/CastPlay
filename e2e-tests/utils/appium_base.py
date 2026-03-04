"""
Appium UI 自动化测试基类

功能：
- Appium 驱动管理
- 页面元素定位
- 常用操作封装
- 断言辅助
"""
import time
import logging
import os
from typing import Optional, Tuple
from datetime import datetime

from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logger = logging.getLogger(__name__)


class AppiumTestBase:
    """Appium 测试基类"""

    def __init__(self, config, emulator_manager, backend_manager):
        """
        初始化

        Args:
            config: TestConfig 配置对象
            emulator_manager: EmulatorManager 实例
            backend_manager: BackendManager 实例
        """
        self.config = config
        self.emulator = emulator_manager
        self.backend = backend_manager
        self.driver: Optional[webdriver.Remote] = None
        self._screenshot_counter = 0

    def setup(self) -> bool:
        """初始化 Appium 驱动"""
        logger.info("初始化 Appium 驱动...")

        try:
            options = UiAutomator2Options()
            options.platform_name = "Android"
            options.device_name = self.emulator.serial or "emulator-5554"
            options.app_package = self.config.app.package_name
            options.app_activity = self.config.app.main_activity
            options.automation_name = "UiAutomator2"
            options.no_reset = False  # 每次重置应用状态
            options.full_reset = False
            options.new_command_timeout = 300

            # 如果指定了 APK 路径
            if self.config.app.apk_path:
                options.app = self.config.app.apk_path

            self.driver = webdriver.Remote(
                command_executor=self.config.appium.base_url,
                options=options
            )

            self.driver.implicitly_wait(self.config.appium.implicit_wait)

            logger.info("Appium 驱动初始化成功")
            return True

        except Exception as e:
            logger.error(f"Appium 驱动初始化失败: {e}")
            return False

    def teardown(self):
        """清理"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None

    # ================================================================
    # 元素定位
    # ================================================================

    def find_element_by_id(self, resource_id: str, timeout: int = 10):
        """通过资源 ID 查找元素"""
        full_id = f"{self.config.app.package_name}:id/{resource_id}"
        return self._wait_for_element(AppiumBy.ID, full_id, timeout)

    def find_element_by_text(self, text: str, timeout: int = 10):
        """通过文本查找元素"""
        return self._wait_for_element(
            AppiumBy.ANDROID_UIAUTOMATOR,
            f'new UiSelector().text("{text}")',
            timeout
        )

    def find_element_by_content_desc(self, desc: str, timeout: int = 10):
        """通过内容描述查找元素"""
        return self._wait_for_element(
            AppiumBy.ACCESSIBILITY_ID,
            desc,
            timeout
        )

    def find_element_by_xpath(self, xpath: str, timeout: int = 10):
        """通过 XPath 查找元素"""
        return self._wait_for_element(AppiumBy.XPATH, xpath, timeout)

    def _wait_for_element(self, by, value, timeout: int = 10):
        """等待元素出现"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            logger.warning(f"等待元素超时: {by}={value}")
            return None

    def element_exists(self, resource_id: str, timeout: int = 5) -> bool:
        """检查元素是否存在"""
        return self.find_element_by_id(resource_id, timeout) is not None

    def get_element_text(self, resource_id: str, timeout: int = 10) -> Optional[str]:
        """获取元素文本"""
        element = self.find_element_by_id(resource_id, timeout)
        if element:
            return element.text
        return None

    # ================================================================
    # 操作封装
    # ================================================================

    def click_element(self, resource_id: str, timeout: int = 10) -> bool:
        """点击元素"""
        element = self.find_element_by_id(resource_id, timeout)
        if element:
            element.click()
            return True
        return False

    def input_text(self, resource_id: str, text: str, timeout: int = 10) -> bool:
        """输入文本"""
        element = self.find_element_by_id(resource_id, timeout)
        if element:
            element.clear()
            element.send_keys(text)
            return True
        return False

    def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int,
              duration: int = 500):
        """滑动"""
        self.driver.swipe(start_x, start_y, end_x, end_y, duration)

    def swipe_up(self):
        """向上滑动"""
        size = self.driver.get_window_size()
        start_x = size['width'] // 2
        start_y = int(size['height'] * 0.8)
        end_y = int(size['height'] * 0.2)
        self.swipe(start_x, start_y, start_x, end_y)

    def swipe_down(self):
        """向下滑动"""
        size = self.driver.get_window_size()
        start_x = size['width'] // 2
        start_y = int(size['height'] * 0.2)
        end_y = int(size['height'] * 0.8)
        self.swipe(start_x, start_y, start_x, end_y)

    def back(self):
        """返回"""
        self.driver.back()

    def home(self):
        """回到桌面"""
        self.driver.press_keycode(3)  # KEYCODE_HOME

    def wait(self, seconds: float):
        """等待"""
        time.sleep(seconds)

    # ================================================================
    # 应用状态
    # ================================================================

    def is_app_running(self) -> bool:
        """检查应用是否在前台运行"""
        try:
            current_package = self.driver.current_package
            return current_package == self.config.app.package_name
        except Exception:
            return False

    def restart_app(self):
        """重启应用"""
        self.driver.terminate_app(self.config.app.package_name)
        time.sleep(1)
        self.driver.activate_app(self.config.app.package_name)
        time.sleep(2)

    def clear_app_and_restart(self):
        """清除应用数据并重启"""
        self.emulator.clear_app_data(self.config.app.package_name)
        time.sleep(1)
        self.driver.activate_app(self.config.app.package_name)
        time.sleep(3)

    # ================================================================
    # WebView 操作
    # ================================================================

    def switch_to_webview(self) -> bool:
        """切换到 WebView 上下文"""
        try:
            contexts = self.driver.contexts
            for context in contexts:
                if 'WEBVIEW' in context:
                    self.driver.switch_to.context(context)
                    logger.info(f"切换到 WebView: {context}")
                    return True
            return False
        except Exception as e:
            logger.error(f"切换 WebView 失败: {e}")
            return False

    def switch_to_native(self):
        """切换回原生上下文"""
        try:
            self.driver.switch_to.context('NATIVE_APP')
        except Exception:
            pass

    def get_webview_content(self) -> Optional[str]:
        """获取 WebView 内容"""
        if self.switch_to_webview():
            try:
                content = self.driver.page_source
                return content
            finally:
                self.switch_to_native()
        return None

    # ================================================================
    # 截图和日志
    # ================================================================

    def take_screenshot(self, name: str = None) -> str:
        """
        截图

        Args:
            name: 截图名称

        Returns:
            截图文件路径
        """
        self._screenshot_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if name:
            filename = f"{timestamp}_{name}.png"
        else:
            filename = f"{timestamp}_{self._screenshot_counter}.png"

        filepath = os.path.join(self.config.report_dir, filename)

        try:
            self.driver.save_screenshot(filepath)
            logger.info(f"截图保存: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"截图失败: {e}")
            return ""

    def get_page_source(self) -> str:
        """获取页面源码"""
        try:
            return self.driver.page_source
        except Exception:
            return ""

    # ================================================================
    # 断言辅助
    # ================================================================

    def assert_element_visible(self, resource_id: str, message: str = ""):
        """断言元素可见"""
        element = self.find_element_by_id(resource_id)
        assert element is not None and element.is_displayed(), \
            message or f"元素不可见: {resource_id}"

    def assert_element_text(self, resource_id: str, expected: str, message: str = ""):
        """断言元素文本"""
        actual = self.get_element_text(resource_id)
        assert actual == expected, \
            message or f"文本不匹配: 期望 '{expected}', 实际 '{actual}'"

    def assert_element_text_contains(self, resource_id: str, expected: str,
                                     message: str = ""):
        """断言元素文本包含"""
        actual = self.get_element_text(resource_id)
        assert actual and expected in actual, \
            message or f"文本不包含: 期望包含 '{expected}', 实际 '{actual}'"


class CastPlayPage(AppiumTestBase):
    """CastPlay 应用页面对象"""

    # 元素 ID
    ID_DEVICE_ID_TEXT = "deviceIdText"
    ID_WEBVIEW = "webView"
    ID_PROGRESS_BAR = "progressBar"
    ID_STATUS_TEXT = "statusText"

    def get_device_id(self) -> Optional[str]:
        """获取设备 ID"""
        text = self.get_element_text(self.ID_DEVICE_ID_TEXT)
        if text:
            # 可能是 "设备ID: CAS-XXXX" 或纯 ID
            if "CAS-" in text:
                import re
                match = re.search(r'CAS-[A-Z0-9]+', text)
                if match:
                    return match.group()
        return text

    def is_device_id_displayed(self) -> bool:
        """设备 ID 是否显示"""
        element = self.find_element_by_id(self.ID_DEVICE_ID_TEXT, timeout=5)
        return element is not None and element.is_displayed()

    def is_webview_visible(self) -> bool:
        """WebView 是否可见"""
        element = self.find_element_by_id(self.ID_WEBVIEW, timeout=5)
        return element is not None and element.is_displayed()

    def is_progress_visible(self) -> bool:
        """进度条是否可见"""
        element = self.find_element_by_id(self.ID_PROGRESS_BAR, timeout=3)
        return element is not None and element.is_displayed()

    def wait_for_registration(self, timeout: int = 30) -> bool:
        """等待设备注册完成"""
        logger.info(f"等待设备注册（超时: {timeout}秒）...")

        start_time = time.time()
        while time.time() - start_time < timeout:
            device_id = self.get_device_id()
            if device_id and device_id.startswith("CAS-"):
                logger.info(f"设备注册成功: {device_id}")
                return True
            time.sleep(1)

        logger.error("设备注册超时")
        return False

    def wait_for_sync_complete(self, timeout: int = 120) -> bool:
        """等待同步完成"""
        logger.info(f"等待同步完成（超时: {timeout}秒）...")

        start_time = time.time()
        while time.time() - start_time < timeout:
            # 检查进度条是否消失
            if not self.is_progress_visible():
                # 进度条消失后稍等确认
                time.sleep(2)
                if not self.is_progress_visible():
                    logger.info("同步完成")
                    return True
            time.sleep(2)

        logger.error("同步超时")
        return False

    def wait_for_playback_started(self, timeout: int = 60) -> bool:
        """等待播放开始"""
        logger.info(f"等待播放开始（超时: {timeout}秒）...")

        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.is_webview_visible():
                # 检查 WebView 内容
                content = self.get_webview_content()
                if content and len(content) > 100:
                    logger.info("播放已开始")
                    return True
            time.sleep(2)

        logger.error("播放启动超时")
        return False
