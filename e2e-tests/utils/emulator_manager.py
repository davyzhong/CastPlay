"""
Android 模拟器管理工具

功能：
- 自动启动/关闭模拟器
- 等待模拟器启动完成
- 检测模拟器状态
- 安装/卸载 APK
"""
import subprocess
import time
import logging
import re
from typing import Optional, List

logger = logging.getLogger(__name__)


class EmulatorManager:
    """Android 模拟器管理器"""

    def __init__(self, config):
        """
        初始化模拟器管理器

        Args:
            config: EmulatorConfig 配置对象
        """
        self.config = config
        self.emulator_process: Optional[subprocess.Popen] = None
        self._serial: Optional[str] = None

    @property
    def serial(self) -> Optional[str]:
        """获取模拟器序列号"""
        return self._serial

    def list_avds(self) -> List[str]:
        """列出所有可用的 AVD"""
        try:
            result = subprocess.run(
                [self.config.emulator_path, "-list-avds"],
                capture_output=True,
                text=True,
                timeout=10
            )
            avds = [line.strip()
                    for line in result.stdout.strip().split('\n') if line.strip()]
            return avds
        except Exception as e:
            logger.error(f"列出 AVD 失败: {e}")
            return []

    def is_running(self) -> bool:
        """检查模拟器是否正在运行"""
        try:
            result = subprocess.run(
                [self.config.adb_path, "devices"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return "emulator" in result.stdout and "device" in result.stdout
        except Exception as e:
            logger.error(f"检查模拟器状态失败: {e}")
            return False

    def get_running_emulators(self) -> List[str]:
        """获取正在运行的模拟器列表"""
        try:
            result = subprocess.run(
                [self.config.adb_path, "devices"],
                capture_output=True,
                text=True,
                timeout=10
            )
            emulators = []
            for line in result.stdout.strip().split('\n'):
                if 'emulator' in line and 'device' in line:
                    parts = line.split()
                    if parts:
                        emulators.append(parts[0])
            return emulators
        except Exception as e:
            logger.error(f"获取运行中模拟器失败: {e}")
            return []

    def start(self, wait_boot: bool = True) -> bool:
        """
        启动模拟器

        Args:
            wait_boot: 是否等待启动完成

        Returns:
            是否启动成功
        """
        # 检查 AVD 是否存在
        avds = self.list_avds()
        if self.config.avd_name not in avds:
            logger.error(f"AVD '{self.config.avd_name}' 不存在")
            logger.info(f"可用的 AVD: {avds}")
            return False

        # 检查是否已在运行
        if self.is_running():
            logger.info("模拟器已在运行")
            emulators = self.get_running_emulators()
            if emulators:
                self._serial = emulators[0]
            return True

        # 构建启动命令
        cmd = [
            self.config.emulator_path,
            "-avd", self.config.avd_name,
            "-no-snapshot-save",  # 不保存快照
            "-no-audio",  # 禁用音频
        ]

        if self.config.headless:
            cmd.append("-no-window")

        if self.config.wipe_data:
            cmd.append("-wipe-data")

        logger.info(f"启动模拟器: {' '.join(cmd)}")

        try:
            # 启动模拟器进程
            self.emulator_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            if wait_boot:
                return self._wait_for_boot()

            return True

        except Exception as e:
            logger.error(f"启动模拟器失败: {e}")
            return False

    def _wait_for_boot(self) -> bool:
        """等待模拟器启动完成"""
        logger.info(f"等待模拟器启动（超时: {self.config.boot_timeout}秒）...")

        start_time = time.time()

        while time.time() - start_time < self.config.boot_timeout:
            # 检查设备是否出现
            emulators = self.get_running_emulators()
            if emulators:
                self._serial = emulators[0]

                # 检查 boot 是否完成
                if self._check_boot_completed():
                    logger.info(f"模拟器启动完成: {self._serial}")
                    return True

            time.sleep(2)

        logger.error("模拟器启动超时")
        return False

    def _check_boot_completed(self) -> bool:
        """检查启动是否完成"""
        try:
            # 检查 sys.boot_completed 属性
            result = subprocess.run(
                [self.config.adb_path, "-s", self._serial, "shell",
                 "getprop", "sys.boot_completed"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout.strip() == "1"
        except Exception:
            return False

    def stop(self) -> bool:
        """停止模拟器"""
        logger.info("停止模拟器...")

        try:
            if self._serial:
                # 通过 adb 关闭
                subprocess.run(
                    [self.config.adb_path, "-s", self._serial, "emu", "kill"],
                    capture_output=True,
                    timeout=30
                )

            if self.emulator_process:
                self.emulator_process.terminate()
                self.emulator_process.wait(timeout=10)
                self.emulator_process = None

            self._serial = None
            logger.info("模拟器已停止")
            return True

        except Exception as e:
            logger.error(f"停止模拟器失败: {e}")
            return False

    def install_apk(self, apk_path: str) -> bool:
        """
        安装 APK

        Args:
            apk_path: APK 文件路径

        Returns:
            是否安装成功
        """
        if not self._serial:
            logger.error("模拟器未运行")
            return False

        logger.info(f"安装 APK: {apk_path}")

        try:
            result = subprocess.run(
                [self.config.adb_path, "-s", self._serial,
                    "install", "-r", apk_path],
                capture_output=True,
                text=True,
                timeout=120
            )

            if "Success" in result.stdout:
                logger.info("APK 安装成功")
                return True
            else:
                logger.error(f"APK 安装失败: {result.stdout} {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"安装 APK 异常: {e}")
            return False

    def uninstall_app(self, package_name: str) -> bool:
        """卸载应用"""
        if not self._serial:
            return False

        try:
            subprocess.run(
                [self.config.adb_path, "-s", self._serial,
                    "uninstall", package_name],
                capture_output=True,
                timeout=30
            )
            return True
        except Exception:
            return False

    def clear_app_data(self, package_name: str) -> bool:
        """清除应用数据"""
        if not self._serial:
            return False

        logger.info(f"清除应用数据: {package_name}")

        try:
            result = subprocess.run(
                [self.config.adb_path, "-s", self._serial, "shell",
                 "pm", "clear", package_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            return "Success" in result.stdout
        except Exception as e:
            logger.error(f"清除应用数据失败: {e}")
            return False

    def launch_app(self, package_name: str, activity: str) -> bool:
        """启动应用"""
        if not self._serial:
            return False

        logger.info(f"启动应用: {package_name}/{activity}")

        try:
            subprocess.run(
                [self.config.adb_path, "-s", self._serial, "shell",
                 "am", "start", "-n", f"{package_name}/{activity}"],
                capture_output=True,
                timeout=30
            )
            return True
        except Exception as e:
            logger.error(f"启动应用失败: {e}")
            return False

    def take_screenshot(self, output_path: str) -> bool:
        """截图"""
        if not self._serial:
            return False

        try:
            # 在设备上截图
            subprocess.run(
                [self.config.adb_path, "-s", self._serial, "shell",
                 "screencap", "-p", "/sdcard/screenshot.png"],
                capture_output=True,
                timeout=30
            )

            # 拉取到本地
            subprocess.run(
                [self.config.adb_path, "-s", self._serial, "pull",
                 "/sdcard/screenshot.png", output_path],
                capture_output=True,
                timeout=30
            )

            return True
        except Exception as e:
            logger.error(f"截图失败: {e}")
            return False

    def get_logcat(self, lines: int = 100) -> str:
        """获取 logcat 日志"""
        if not self._serial:
            return ""

        try:
            result = subprocess.run(
                [self.config.adb_path, "-s", self._serial, "logcat",
                 "-d", "-t", str(lines)],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout
        except Exception:
            return ""

    def get_app_logcat(self, package_name: str, lines: int = 100) -> str:
        """获取应用的 logcat 日志"""
        if not self._serial:
            return ""

        try:
            # 获取应用 PID
            result = subprocess.run(
                [self.config.adb_path, "-s", self._serial, "shell",
                 "pidof", package_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            pid = result.stdout.strip()

            if pid:
                # 过滤该 PID 的日志
                result = subprocess.run(
                    [self.config.adb_path, "-s", self._serial, "logcat",
                     "-d", "-t", str(lines), "--pid", pid],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                return result.stdout

            return ""
        except Exception:
            return ""
