"""
CastPlay E2E 自动化测试 - 配置文件
"""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class EmulatorConfig:
    """模拟器配置"""
    avd_name: str = "Pixel_4_API_30"  # 模拟器名称
    sdk_path: str = os.environ.get(
        "ANDROID_HOME", os.path.expanduser("~/Library/Android/sdk"))
    boot_timeout: int = 120  # 启动超时（秒）
    headless: bool = False  # 是否无头模式
    wipe_data: bool = False  # 是否清除数据

    @property
    def emulator_path(self) -> str:
        return os.path.join(self.sdk_path, "emulator", "emulator")

    @property
    def adb_path(self) -> str:
        return os.path.join(self.sdk_path, "platform-tools", "adb")


@dataclass
class AppConfig:
    """应用配置"""
    package_name: str = "com.castplay.player"
    main_activity: str = "com.castplay.player.MainActivity"
    apk_path: Optional[str] = None  # APK 路径，None 表示使用已安装的


@dataclass
class BackendConfig:
    """后端服务配置"""
    host: str = "127.0.0.1"
    port: int = 5001
    base_url: str = "http://127.0.0.1:5001"
    api_url: str = "http://127.0.0.1:5001/api"
    ws_url: str = "ws://127.0.0.1:5001"
    startup_timeout: int = 30  # 启动超时（秒）
    project_path: str = os.path.expanduser(
        "~/PycharmProjects/CastPlay/castplay-server")


@dataclass
class AppiumConfig:
    """Appium 配置"""
    host: str = "127.0.0.1"
    port: int = 4723
    base_url: str = "http://127.0.0.1:4723"
    implicit_wait: int = 10  # 隐式等待（秒）
    startup_timeout: int = 30  # 启动超时（秒）


@dataclass
class TestConfig:
    """测试配置"""
    emulator: EmulatorConfig
    app: AppConfig
    backend: BackendConfig
    appium: AppiumConfig

    # 测试超时
    register_timeout: int = 30  # 注册超时
    download_timeout: int = 120  # 下载超时
    playback_check_interval: int = 5  # 播放检查间隔

    # 报告
    report_dir: str = os.path.expanduser(
        "~/PycharmProjects/CastPlay/e2e-tests/reports")
    screenshot_on_failure: bool = True


def get_default_config() -> TestConfig:
    """获取默认配置"""
    return TestConfig(
        emulator=EmulatorConfig(),
        app=AppConfig(),
        backend=BackendConfig(),
        appium=AppiumConfig()
    )


# 环境检测
def check_environment() -> dict:
    """检查测试环境"""
    config = get_default_config()
    result = {
        "android_sdk": os.path.exists(config.emulator.sdk_path),
        "emulator": os.path.exists(config.emulator.emulator_path),
        "adb": os.path.exists(config.emulator.adb_path),
        "backend_project": os.path.exists(config.backend.project_path),
    }
    return result
