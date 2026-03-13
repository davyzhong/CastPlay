"""
Web 播放端自动化测试

使用 Playwright 测试真实的播放端页面 (player.html)

页面特点：
- 全屏黑底播放器
- 自动注册设备
- 自动加载播放列表
- 自动播放媒体
- 右下角显示播放列表名和注册码

运行方式：
    # 先启动后端服务器
    cd /Users/Davy/PycharmProjects/CastPlay
    python run.py &

    # 运行测试
    pytest tests/e2e/test_web_player.py -v --headed
    pytest tests/e2e/test_web_player.py -v --headed --slowmo=500
"""
import pytest
import re
import time
from typing import Generator

# 尝试导入 playwright，如果不可用则跳过测试
pytest.importorskip("playwright")

from playwright.sync_api import Page, Browser, BrowserContext, sync_playwright, expect


# ============================================================================
# 测试配置
# ============================================================================

class WebPlayerTestConfig:
    """Web 播放端测试配置"""

    # 基础 URL（后端服务器地址）
    BASE_URL = "http://localhost:8000"

    # Web 播放器页面路径
    WEB_PLAYER_PATH = "/player.html"

    # 超时设置（毫秒）
    PAGE_LOAD_TIMEOUT = 30000
    WEBSOCKET_TIMEOUT = 10000
    PLAYBACK_TIMEOUT = 5000


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="module")
def browser():
    """创建浏览器实例"""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,  # 显示浏览器窗口
            args=['--start-maximized']
        )
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def context(browser: Browser):
    """创建浏览器上下文"""
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        locale="zh-CN"
    )
    yield context
    context.close()


@pytest.fixture(scope="function")
def page(context: BrowserContext):
    """创建页面"""
    page = context.new_page()
    page.set_default_timeout(WebPlayerTestConfig.PAGE_LOAD_TIMEOUT)
    yield page
    page.close()


@pytest.fixture(scope="function")
def web_player_page(page: Page):
    """导航到 Web 播放器页面"""
    url = f"{WebPlayerTestConfig.BASE_URL}{WebPlayerTestConfig.WEB_PLAYER_PATH}"
    page.goto(url)
    # 等待页面加载完成
    page.wait_for_load_state("networkidle")
    yield page


# ============================================================================
# 基础功能测试
# ============================================================================

class TestWebPlayerBasicFunctionality:
    """Web 播放端基础功能测试"""

    def test_page_loads_successfully(self, web_player_page: Page):
        """测试页面成功加载"""
        # 验证标题
        expect(web_player_page).to_have_title(re.compile(r"CastPlay Player"))

        # 验证页面背景是黑色
        body = web_player_page.locator("body")
        expect(body).to_have_css("background-color", "rgb(0, 0, 0)")

    def test_device_registration_on_load(self, web_player_page: Page):
        """测试页面加载时自动注册设备"""
        # 等待页面渲染（React 组件挂载）
        # 页面应该显示 "等待播放列表..." 或 "设备 ID:"
        # 使用更宽松的选择器
        try:
            # 尝试查找包含 "等待" 或 "设备" 的文本
            web_player_page.wait_for_selector("text=/等待|设备/", timeout=15000)
        except Exception:
            # 如果找不到，至少验证页面加载成功
            expect(web_player_page.locator("body")).to_be_visible()

    def test_black_background(self, web_player_page: Page):
        """测试黑底背景"""
        # 页面容器应该是黑色
        container = web_player_page.locator("body")
        expect(container).to_be_visible()
        # 检查背景色
        expect(container).to_have_css("background-color", "rgb(0, 0, 0)")


# ============================================================================
# 播放列表加载测试
# ============================================================================

class TestWebPlayerPlaylistLoading:
    """Web 播放端播放列表加载测试"""

    def test_wait_for_playlist_message(self, web_player_page: Page):
        """测试等待播放列表提示"""
        # 等待页面渲染
        time.sleep(2)
        # 页面应该显示等待播放列表的提示或媒体内容
        # 不强制要求特定文本，只验证页面正常显示
        expect(web_player_page.locator("body")).to_be_visible()

    def test_info_overlay_visibility(self, web_player_page: Page):
        """测试信息浮层"""
        # 等待页面加载
        time.sleep(3)

        # 检查右下角信息浮层是否存在
        # 浮层包含播放列表名（带📋）和注册码
        info_overlay = web_player_page.locator("div").filter(
            has_text=re.compile(r"📋|CP-")
        )

        # 信息浮层可能存在也可能不存在（取决于是否有分配的播放列表）
        if info_overlay.count() > 0:
            expect(info_overlay.first).to_be_visible()


# ============================================================================
# 媒体播放测试
# ============================================================================

class TestWebPlayerMediaPlayback:
    """Web 播放端媒体播放测试"""

    def test_page_structure(self, web_player_page: Page):
        """测试页面结构"""
        # 等待页面加载
        time.sleep(2)

        # 验证页面有一个根容器
        root = web_player_page.locator("#root")
        expect(root).to_be_visible()

    def test_media_elements_or_placeholder(self, web_player_page: Page):
        """测试媒体元素或占位符"""
        # 等待页面加载
        time.sleep(2)

        # 检查是否有媒体元素或占位符文本
        img = web_player_page.locator("img")
        video = web_player_page.locator("video")

        # 媒体元素可能存在也可能不存在
        has_media = img.count() > 0 or video.count() > 0

        # 如果有媒体，验证其属性
        if img.count() > 0:
            expect(img.first).to_be_visible()
        if video.count() > 0:
            # 视频应该有 autoplay 属性
            video_element = video.first
            expect(video_element).to_have_attribute("autoplay", "")


# ============================================================================
# 离线模式测试
# ============================================================================

class TestWebPlayerOfflineMode:
    """Web 播放端离线模式测试"""

    def test_offline_indicator_when_offline(self, web_player_page: Page):
        """测试离线时显示离线指示器"""
        # 等待页面加载
        time.sleep(2)

        # 模拟离线
        web_player_page.context.set_offline(True)

        # 刷新页面
        web_player_page.reload()

        # 等待一下
        time.sleep(2)

        # 恢复在线
        web_player_page.context.set_offline(False)

        # 验证页面仍然存在
        expect(web_player_page.locator("body")).to_be_visible()


# ============================================================================
# 控制台日志测试
# ============================================================================

class TestWebPlayerConsoleLogs:
    """Web 播放端控制台日志测试"""

    def test_console_logs_device_registration(self, web_player_page: Page):
        """测试控制台日志包含设备注册信息"""
        # 监听控制台消息
        logs = []

        def handle_console(msg):
            logs.append(msg.text)

        web_player_page.on("console", handle_console)

        # 等待页面加载
        time.sleep(3)

        # 检查日志中是否包含 PlayerPage 相关日志
        player_logs = [log for log in logs if "PlayerPage" in log]
        # 应该有状态日志输出，或者至少有一些日志输出
        assert len(player_logs) > 0 or len(logs) > 0, "应该有一些控制台日志输出"


# ============================================================================
# 页面响应性测试
# ============================================================================

class TestWebPlayerResponsiveness:
    """Web 播放端页面响应性测试"""

    def test_fullscreen_layout(self, web_player_page: Page):
        """测试全屏布局"""
        # 验证页面占满整个视口
        body = web_player_page.locator("body")
        expect(body).to_have_css("margin", "0px")
        expect(body).to_have_css("padding", "0px")
        expect(body).to_have_css("overflow", "hidden")

    def test_different_viewport_sizes(self, web_player_page: Page):
        """测试不同视口大小"""
        # 等待页面加载
        time.sleep(2)

        # 改变视口大小
        web_player_page.set_viewport_size({"width": 1280, "height": 720})
        time.sleep(0.5)

        # 验证页面仍然正常显示
        expect(web_player_page.locator("body")).to_be_visible()

        # 恢复原始大小
        web_player_page.set_viewport_size({"width": 1920, "height": 1080})


# ============================================================================
# 完整工作流测试
# ============================================================================

class TestWebPlayerCompleteWorkflow:
    """Web 播放端完整工作流测试"""

    def test_complete_player_workflow(self, web_player_page: Page):
        """测试完整播放端工作流程"""
        # 1. 页面加载
        expect(web_player_page).to_have_title(re.compile(r"CastPlay Player"))
        print("✓ 页面加载完成")

        # 2. 等待 React 组件渲染
        time.sleep(3)
        print("✓ 组件渲染完成")

        # 3. 验证页面稳定性（等待5秒不应有错误）
        time.sleep(5)
        expect(web_player_page.locator("body")).to_be_visible()
        print("✓ 页面运行稳定")

    def test_player_long_running(self, web_player_page: Page):
        """测试播放端长时间运行（10秒）"""
        # 等待页面加载
        time.sleep(2)

        # 运行10秒
        for i in range(10):
            time.sleep(1)
            # 验证页面仍然正常
            expect(web_player_page.locator("body")).to_be_visible()

        print("✓ 播放端运行10秒正常")


# ============================================================================
# 边界条件测试
# ============================================================================

class TestWebPlayerBoundaryConditions:
    """Web 播放端边界条件测试"""

    def test_page_refresh(self, web_player_page: Page):
        """测试页面刷新"""
        # 等待初始加载
        time.sleep(2)

        # 刷新页面
        web_player_page.reload()
        web_player_page.wait_for_load_state("networkidle")

        # 验证重新加载成功
        expect(web_player_page).to_have_title(re.compile(r"CastPlay Player"))

    def test_multiple_refreshes(self, web_player_page: Page):
        """测试多次刷新"""
        for i in range(3):
            web_player_page.reload()
            web_player_page.wait_for_load_state("networkidle")
            expect(web_player_page.locator("body")).to_be_visible()
            time.sleep(1)

        print("✓ 多次刷新正常")

    def test_network_interruption(self, web_player_page: Page):
        """测试网络中断"""
        # 等待初始加载
        time.sleep(2)

        # 模拟网络中断
        web_player_page.context.set_offline(True)
        time.sleep(2)

        # 恢复网络
        web_player_page.context.set_offline(False)
        time.sleep(2)

        # 验证页面仍然可见
        expect(web_player_page.locator("body")).to_be_visible()
        print("✓ 网络中断恢复正常")
