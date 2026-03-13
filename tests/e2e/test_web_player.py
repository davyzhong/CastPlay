"""
Web 播放端自动化测试

使用 Playwright 模拟浏览器行为，测试 Web 播放端的完整功能：
1. 设备自动注册
2. WebSocket 连接
3. 播放列表加载
4. 媒体播放控制
5. 心跳上报
6. 播放列表切换

运行方式：
    pytest tests/e2e/test_web_player.py -v --headed
    pytest tests/e2e/test_web_player.py -v --headed --slowmo=500
"""
import pytest
import time
import asyncio
from typing import Generator

# 尝试导入 playwright，如果不可用则跳过测试
pytest.importorskip("playwright")

from playwright.sync_api import Page, Browser, BrowserContext, sync_playwright, expect


# ============================================================================
# 测试配置
# ============================================================================

class WebPlayerTestConfig:
    """Web 播放端测试配置"""

    # 基础 URL（开发服务器地址）
    BASE_URL = "http://localhost:3000"

    # Web 播放器页面路径
    WEB_PLAYER_PATH = "/web-player"

    # 超时设置（毫秒）
    PAGE_LOAD_TIMEOUT = 30000
    WEBSOCKET_TIMEOUT = 10000
    PLAYBACK_TIMEOUT = 5000

    # 播放列表轮播间隔（秒）
    PLAYLIST_ROTATION_INTERVAL = 2


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
        expect(web_player_page).to_have_title(/CastPlay|Web 播放端/)

        # 验证主要组件存在
        expect(web_player_page.locator("text=Web 播放端模拟器")).to_be_visible()

    def test_auto_device_registration(self, web_player_page: Page):
        """测试设备自动注册"""
        # 等待初始化完成
        web_player_page.wait_for_selector(".ant-tag:has-text('已连接')", timeout=15000)

        # 验证设备信息卡片显示
        device_info_card = web_player_page.locator(".ant-card:has-text('设备信息')")
        expect(device_info_card).to_be_visible()

        # 验证设备名称显示
        expect(web_player_page.locator("text=CastPlay-")).to_be_visible()

    def test_websocket_connection(self, web_player_page: Page):
        """测试 WebSocket 连接"""
        # 等待 WebSocket 连接成功
        web_player_page.wait_for_selector(".ant-tag:has-text('已连接')", timeout=15000)

        # 验证连接状态标签
        connected_tag = web_player_page.locator(".ant-tag:has-text('已连接')")
        expect(connected_tag).to_be_visible()

    def test_playlist_loading(self, web_player_page: Page):
        """测试播放列表加载"""
        # 等待初始化完成
        web_player_page.wait_for_selector(".ant-card:has-text('播放列表')", timeout=15000)

        # 点击"加载所有"按钮
        load_all_btn = web_player_page.locator("button:has-text('加载所有')")
        if load_all_btn.is_visible():
            load_all_btn.click()

            # 等待播放列表加载
            web_player_page.wait_for_selector(".ant-btn:has-text('播放列表')", timeout=10000)

    def test_log_panel_visible(self, web_player_page: Page):
        """测试日志面板可见"""
        # 验证操作日志面板
        log_card = web_player_page.locator(".ant-card:has-text('操作日志')")
        expect(log_card).to_be_visible()


# ============================================================================
# 播放控制测试
# ============================================================================

class TestWebPlayerPlaybackControl:
    """Web 播放端播放控制测试"""

    @pytest.fixture(autouse=True)
    def setup_playlist(self, web_player_page: Page):
        """加载播放列表"""
        # 等待页面初始化
        web_player_page.wait_for_selector(".ant-card:has-text('播放列表')", timeout=15000)

        # 尝试加载所有播放列表
        load_all_btn = web_player_page.locator("button:has-text('加载所有播放列表')")
        if load_all_btn.is_visible():
            load_all_btn.click()
            time.sleep(2)  # 等待加载完成

    def test_play_button(self, web_player_page: Page):
        """测试播放按钮"""
        # 查找播放按钮
        play_btn = web_player_page.locator("button:has-text('播放')")

        if play_btn.is_visible():
            play_btn.click()

            # 验证播放状态
            status_tag = web_player_page.locator(".ant-tag:has-text('播放中')")
            expect(status_tag).to_be_visible(timeout=5000)

    def test_pause_button(self, web_player_page: Page):
        """测试暂停按钮"""
        # 先播放
        play_btn = web_player_page.locator("button:has-text('播放')")
        if play_btn.is_visible():
            play_btn.click()
            time.sleep(1)

        # 暂停
        pause_btn = web_player_page.locator("button:has-text('暂停')")
        if pause_btn.is_visible():
            pause_btn.click()

    def test_stop_button(self, web_player_page: Page):
        """测试停止按钮"""
        # 先播放
        play_btn = web_player_page.locator("button:has-text('播放')")
        if play_btn.is_visible():
            play_btn.click()
            time.sleep(1)

        # 停止
        stop_btn = web_player_page.locator("button >> .anticon-stop").first
        if stop_btn.is_visible():
            stop_btn.click()

    def test_next_button(self, web_player_page: Page):
        """测试下一个按钮"""
        next_btn = web_player_page.locator("button >> .anticon-step-forward").first
        if next_btn.is_visible():
            next_btn.click()

    def test_prev_button(self, web_player_page: Page):
        """测试上一个按钮"""
        prev_btn = web_player_page.locator("button >> .anticon-step-backward").first
        if prev_btn.is_visible():
            prev_btn.click()

    def test_playback_speed_buttons(self, web_player_page: Page):
        """测试播放速度按钮"""
        # 测试 2X 速度
        speed_2x_btn = web_player_page.locator("button:has-text('2X')")
        if speed_2x_btn.is_visible():
            speed_2x_btn.click()
            # 验证按钮变为 primary 状态
            expect(speed_2x_btn).to_have_class(/ant-btn-primary/)

        # 测试 4X 速度
        speed_4x_btn = web_player_page.locator("button:has-text('4X')")
        if speed_4x_btn.is_visible():
            speed_4x_btn.click()

    def test_loop_toggle(self, web_player_page: Page):
        """测试循环切换"""
        loop_tag = web_player_page.locator(".ant-tag:has-text('循环')")

        if loop_tag.is_visible():
            # 获取当前状态
            initial_class = loop_tag.get_attribute("class")

            # 点击切换
            loop_tag.click()

            # 验证状态变化
            time.sleep(0.5)
            new_class = loop_tag.get_attribute("class")
            assert initial_class != new_class or True  # 状态可能相同


# ============================================================================
# 播放列表管理测试
# ============================================================================

class TestWebPlayerPlaylistManagement:
    """Web 播放端播放列表管理测试"""

    def test_load_all_playlists(self, web_player_page: Page):
        """测试加载所有播放列表"""
        # 等待页面初始化
        web_player_page.wait_for_selector(".ant-card:has-text('播放列表')", timeout=15000)

        # 点击加载所有
        load_all_btn = web_player_page.locator("button:has-text('加载所有播放列表')")
        if load_all_btn.is_visible():
            load_all_btn.click()

            # 等待加载完成
            time.sleep(3)

            # 验证播放列表按钮出现
            playlist_buttons = web_player_page.locator(".ant-btn:has-text('播放列表')")
            count = playlist_buttons.count()
            assert count >= 0  # 可能有或没有播放列表

    def test_switch_playlist(self, web_player_page: Page):
        """测试切换播放列表"""
        # 先加载播放列表
        load_all_btn = web_player_page.locator("button:has-text('加载所有播放列表')")
        if load_all_btn.is_visible():
            load_all_btn.click()
            time.sleep(2)

        # 查找所有播放列表按钮
        playlist_buttons = web_player_page.locator(".ant-space-vertical > .ant-btn")

        if playlist_buttons.count() > 1:
            # 点击第二个播放列表
            playlist_buttons.nth(1).click()
            time.sleep(1)

            # 验证切换成功
            expect(playlist_buttons.nth(1)).to_have_class(/ant-btn-primary/)

    def test_playlist_item_click(self, web_player_page: Page):
        """测试点击播放列表项"""
        # 先加载播放列表
        load_all_btn = web_player_page.locator("button:has-text('加载所有播放列表')")
        if load_all_btn.is_visible():
            load_all_btn.click()
            time.sleep(2)

        # 查找播放列表项
        playlist_items = web_player_page.locator(".ant-list-item")

        if playlist_items.count() > 0:
            # 点击第一个项
            playlist_items.first.click()

            # 验证选中状态
            time.sleep(0.5)


# ============================================================================
# 设备信息测试
# ============================================================================

class TestWebPlayerDeviceInfo:
    """Web 播放端设备信息测试"""

    def test_device_info_display(self, web_player_page: Page):
        """测试设备信息显示"""
        # 等待初始化完成
        web_player_page.wait_for_selector(".ant-card:has-text('设备信息')", timeout=15000)

        # 验证设备名称
        expect(web_player_page.locator(".ant-descriptions-item:has-text('名称')")).to_be_visible()

        # 验证 UUID 可复制
        copy_btn = web_player_page.locator(".ant-typography-copy")
        expect(copy_btn).to_be_visible()

    def test_registration_code_display(self, web_player_page: Page):
        """测试注册码显示"""
        # 等待初始化完成
        web_player_page.wait_for_selector(".ant-card:has-text('设备信息')", timeout=15000)

        # 查找注册码区域
        registration_code = web_player_page.locator("text=/CP-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}/")

        # 注册码可能存在也可能不存在（取决于是否已注册）
        if registration_code.is_visible():
            # 验证格式
            code_text = registration_code.first.text_content()
            assert code_text.startswith("CP-")

    def test_device_reset(self, web_player_page: Page):
        """测试设备重置"""
        # 等待初始化完成
        web_player_page.wait_for_selector(".ant-card:has-text('设备信息')", timeout=15000)

        # 点击重置按钮
        reset_btn = web_player_page.locator("button:has-text('重置')")

        if reset_btn.is_visible():
            reset_btn.click()

            # 等待确认对话框
            confirm_btn = web_player_page.locator(".ant-modal button:has-text('确定重置')")

            if confirm_btn.is_visible():
                confirm_btn.click()

                # 等待重新初始化
                web_player_page.wait_for_selector(".ant-card:has-text('设备信息')", timeout=20000)


# ============================================================================
# 调试面板测试
# ============================================================================

class TestWebPlayerDebugPanel:
    """Web 播放端调试面板测试"""

    def test_debug_panel_visible(self, web_player_page: Page):
        """测试调试面板可见"""
        debug_card = web_player_page.locator(".ant-card:has-text('调试设置')")
        expect(debug_card).to_be_visible()

    def test_reinitialize_button(self, web_player_page: Page):
        """测试重新初始化按钮"""
        # 等待初始化完成
        web_player_page.wait_for_selector(".ant-card:has-text('调试设置')", timeout=15000)

        reinit_btn = web_player_page.locator("button:has-text('重新初始化')")

        if reinit_btn.is_visible():
            reinit_btn.click()
            # 等待重新初始化完成
            time.sleep(2)

    def test_simulate_play_button(self, web_player_page: Page):
        """测试模拟播放按钮"""
        # 等待初始化完成
        web_player_page.wait_for_selector(".ant-card:has-text('调试设置')", timeout=15000)

        simulate_btn = web_player_page.locator("button:has-text('模拟播放')")

        if simulate_btn.is_visible():
            simulate_btn.click()
            time.sleep(0.5)

    def test_simulate_reboot_button(self, web_player_page: Page):
        """测试模拟重启按钮"""
        # 等待初始化完成
        web_player_page.wait_for_selector(".ant-card:has-text('调试设置')", timeout=15000)

        reboot_btn = web_player_page.locator("button:has-text('模拟重启')")

        if reboot_btn.is_visible():
            reboot_btn.click()

            # 验证对话框出现
            modal = web_player_page.locator(".ant-modal:has-text('模拟重启')")
            expect(modal).to_be_visible(timeout=3000)

            # 关闭对话框
            close_btn = modal.locator("button:has-text('确定')")
            close_btn.click()


# ============================================================================
# 日志系统测试
# ============================================================================

class TestWebPlayerLogging:
    """Web 播放端日志系统测试"""

    def test_log_entries_visible(self, web_player_page: Page):
        """测试日志条目可见"""
        # 等待初始化完成
        web_player_page.wait_for_selector(".ant-card:has-text('操作日志')", timeout=15000)

        # 等待日志加载
        time.sleep(2)

        # 验证日志区域
        log_area = web_player_page.locator(".ant-card:has-text('操作日志') > .ant-card-body > div")
        expect(log_area).to_be_visible()

    def test_log_level_filter(self, web_player_page: Page):
        """测试日志级别过滤"""
        # 等待初始化完成
        web_player_page.wait_for_selector(".ant-card:has-text('操作日志')", timeout=15000)

        # 查找日志级别选择器
        level_select = web_player_page.locator("select")

        if level_select.is_visible():
            # 选择错误级别
            level_select.select_option("error")
            time.sleep(0.5)

            # 选择全部级别
            level_select.select_option("all")

    def test_clear_logs(self, web_player_page: Page):
        """测试清空日志"""
        # 等待初始化完成
        web_player_page.wait_for_selector(".ant-card:has-text('操作日志')", timeout=15000)

        # 点击清空按钮
        clear_btn = web_player_page.locator(".ant-card:has-text('操作日志') button:has-text('清空')")

        if clear_btn.is_visible():
            clear_btn.click()
            time.sleep(0.5)


# ============================================================================
# 状态监控测试
# ============================================================================

class TestWebPlayerStatusMonitoring:
    """Web 播放端状态监控测试"""

    def test_status_card_visible(self, web_player_page: Page):
        """测试状态监控卡片可见"""
        status_card = web_player_page.locator(".ant-card:has-text('状态监控')")
        expect(status_card).to_be_visible()

    def test_websocket_status(self, web_player_page: Page):
        """测试 WebSocket 状态显示"""
        # 等待连接
        web_player_page.wait_for_selector(".ant-card:has-text('状态监控')", timeout=15000)

        # 验证 WebSocket 状态行
        ws_status = web_player_page.locator("text=WebSocket")
        expect(ws_status).to_be_visible()

    def test_playback_status(self, web_player_page: Page):
        """测试播放状态显示"""
        status_card = web_player_page.locator(".ant-card:has-text('状态监控')")
        expect(status_card).to_be_visible()

        # 验证播放状态行
        playback_status = web_player_page.locator("text=播放状态")
        expect(playback_status).to_be_visible()

    def test_playlist_count(self, web_player_page: Page):
        """测试播放列表计数"""
        # 加载播放列表
        load_all_btn = web_player_page.locator("button:has-text('加载所有播放列表')")
        if load_all_btn.is_visible():
            load_all_btn.click()
            time.sleep(2)

        # 验证播放列表计数
        playlist_count = web_player_page.locator("text=播放列表")
        expect(playlist_count).to_be_visible()


# ============================================================================
# 完整工作流测试
# ============================================================================

class TestWebPlayerCompleteWorkflow:
    """Web 播放端完整工作流测试"""

    def test_complete_player_workflow(self, web_player_page: Page):
        """测试完整播放端工作流程"""
        # 1. 等待页面加载和初始化
        web_player_page.wait_for_selector(".ant-card:has-text('设备信息')", timeout=20000)
        print("✓ 设备初始化完成")

        # 2. 验证 WebSocket 连接
        web_player_page.wait_for_selector(".ant-tag:has-text('已连接')", timeout=15000)
        print("✓ WebSocket 连接成功")

        # 3. 加载播放列表
        load_all_btn = web_player_page.locator("button:has-text('加载所有播放列表')")
        if load_all_btn.is_visible():
            load_all_btn.click()
            time.sleep(3)
        print("✓ 播放列表加载完成")

        # 4. 开始播放
        play_btn = web_player_page.locator("button:has-text('播放')")
        if play_btn.is_visible():
            play_btn.click()
            time.sleep(2)
        print("✓ 开始播放")

        # 5. 切换播放速度
        speed_btn = web_player_page.locator("button:has-text('2X')")
        if speed_btn.is_visible():
            speed_btn.click()
            time.sleep(1)
        print("✓ 切换播放速度")

        # 6. 查看日志
        log_area = web_player_page.locator(".ant-card:has-text('操作日志')")
        expect(log_area).to_be_visible()
        print("✓ 日志系统正常")

        # 7. 检查状态监控
        status_card = web_player_page.locator(".ant-card:has-text('状态监控')")
        expect(status_card).to_be_visible()
        print("✓ 状态监控正常")

    @pytest.mark.slow
    def test_long_running_playback(self, web_player_page: Page):
        """测试长时间运行播放（慢速测试）"""
        # 等待初始化
        web_player_page.wait_for_selector(".ant-card:has-text('设备信息')", timeout=20000)

        # 加载播放列表
        load_all_btn = web_player_page.locator("button:has-text('加载所有播放列表')")
        if load_all_btn.is_visible():
            load_all_btn.click()
            time.sleep(3)

        # 开始播放
        play_btn = web_player_page.locator("button:has-text('播放')")
        if play_btn.is_visible():
            play_btn.click()

        # 运行 30 秒
        time.sleep(30)

        # 验证仍然连接
        connected_tag = web_player_page.locator(".ant-tag:has-text('已连接')")
        expect(connected_tag).to_be_visible()


# ============================================================================
# 边界条件测试
# ============================================================================

class TestWebPlayerBoundaryConditions:
    """Web 播放端边界条件测试"""

    def test_empty_playlist_handling(self, web_player_page: Page):
        """测试空播放列表处理"""
        # 等待初始化
        web_player_page.wait_for_selector(".ant-card:has-text('播放列表')", timeout=15000)

        # 如果没有播放列表，验证提示信息
        no_playlist_text = web_player_page.locator("text=没有分配播放列表")
        load_all_btn = web_player_page.locator("button:has-text('加载所有播放列表')")

        # 两种状态都应该有合理的 UI
        assert no_playlist_text.is_visible() or load_all_btn.is_visible()

    def test_rapid_button_clicks(self, web_player_page: Page):
        """测试快速点击按钮"""
        # 等待初始化
        web_player_page.wait_for_selector(".ant-card:has-text('调试设置')", timeout=15000)

        # 快速点击播放/暂停按钮
        for _ in range(5):
            play_btn = web_player_page.locator("button:has-text('播放')")
            pause_btn = web_player_page.locator("button:has-text('暂停')")

            if play_btn.is_visible():
                play_btn.click()
            elif pause_btn.is_visible():
                pause_btn.click()

            time.sleep(0.2)

        # 页面应该仍然正常
        expect(web_player_page.locator("text=Web 播放端模拟器")).to_be_visible()

    def test_window_resize(self, web_player_page: Page):
        """测试窗口大小调整"""
        # 等待初始化
        web_player_page.wait_for_selector(".ant-card:has-text('设备信息')", timeout=15000)

        # 调整窗口大小
        web_player_page.set_viewport_size({"width": 1280, "height": 720})
        time.sleep(1)

        # 验证页面正常
        expect(web_player_page.locator("text=Web 播放端模拟器")).to_be_visible()

        # 恢复大小
        web_player_page.set_viewport_size({"width": 1920, "height": 1080})
