#!/usr/bin/env python3
"""
CastPlay E2E 自动化测试 - 主运行脚本

功能：
1. 自动启动 Android 模拟器
2. 自动启动后端服务
3. 启动 Appium 服务
4. 运行 E2E 测试
5. 生成测试报告

用法：
    python run_e2e_tests.py [--avd AVD_NAME] [--headless] [--skip-emulator] [--skip-backend]

示例：
    python run_e2e_tests.py                           # 完整运行
    python run_e2e_tests.py --avd Pixel_6_API_33      # 指定模拟器
    python run_e2e_tests.py --headless                # 无头模式
    python run_e2e_tests.py --skip-emulator           # 跳过模拟器启动
"""
from utils.backend_manager import BackendManager
from utils.emulator_manager import EmulatorManager
from config.settings import get_default_config, check_environment
import argparse
import subprocess
import sys
import os
import time
import signal
import logging
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            f'reports/e2e_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)


class E2ETestRunner:
    """E2E 测试运行器"""

    def __init__(self, args):
        self.args = args
        self.config = get_default_config()

        # 应用命令行参数
        if args.avd:
            self.config.emulator.avd_name = args.avd
        if args.headless:
            self.config.emulator.headless = True

        self.emulator: EmulatorManager = None
        self.backend: BackendManager = None
        self.appium_process = None

        # 注册信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """信号处理"""
        logger.info("接收到终止信号，清理资源...")
        self.cleanup()
        sys.exit(1)

    def check_prerequisites(self) -> bool:
        """检查前置条件"""
        logger.info("=" * 60)
        logger.info("检查测试环境")
        logger.info("=" * 60)

        env_check = check_environment()

        all_ok = True
        for item, status in env_check.items():
            status_str = "✓" if status else "✗"
            logger.info(f"  {status_str} {item}")
            if not status:
                all_ok = False

        # 检查 Appium
        try:
            result = subprocess.run(
                ["appium", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            appium_version = result.stdout.strip()
            logger.info(f"  ✓ Appium: {appium_version}")
        except Exception:
            logger.info("  ✗ Appium 未安装")
            all_ok = False

        # 检查可用 AVD
        self.emulator = EmulatorManager(self.config.emulator)
        avds = self.emulator.list_avds()
        if avds:
            logger.info(f"  ✓ 可用 AVD: {', '.join(avds)}")
        else:
            logger.info("  ✗ 无可用 AVD")
            all_ok = False

        if self.config.emulator.avd_name not in avds:
            logger.warning(
                f"  ⚠ 指定的 AVD '{self.config.emulator.avd_name}' 不存在")
            if avds:
                logger.info(f"    将使用: {avds[0]}")
                self.config.emulator.avd_name = avds[0]
            else:
                all_ok = False

        return all_ok

    def start_emulator(self) -> bool:
        """启动模拟器"""
        if self.args.skip_emulator:
            logger.info("跳过模拟器启动")
            # 检查是否已有运行中的模拟器
            if self.emulator.is_running():
                logger.info("检测到运行中的模拟器")
                emulators = self.emulator.get_running_emulators()
                if emulators:
                    self.emulator._serial = emulators[0]
                return True
            else:
                logger.error("未检测到运行中的模拟器")
                return False

        logger.info("=" * 60)
        logger.info("启动 Android 模拟器")
        logger.info("=" * 60)

        return self.emulator.start(wait_boot=True)

    def start_backend(self) -> bool:
        """启动后端服务"""
        if self.args.skip_backend:
            logger.info("跳过后端服务启动")
            self.backend = BackendManager(self.config.backend)
            if self.backend.is_running():
                logger.info("后端服务已在运行")
                return True
            else:
                logger.warning("后端服务未运行，测试可能失败")
                return True  # 继续运行

        logger.info("=" * 60)
        logger.info("启动后端服务")
        logger.info("=" * 60)

        self.backend = BackendManager(self.config.backend)
        return self.backend.start(wait_ready=True)

    def start_appium(self) -> bool:
        """启动 Appium 服务"""
        logger.info("=" * 60)
        logger.info("启动 Appium 服务")
        logger.info("=" * 60)

        try:
            # 检查是否已在运行
            import requests
            try:
                response = requests.get(
                    f"{self.config.appium.base_url}/status", timeout=5)
                if response.status_code == 200:
                    logger.info("Appium 服务已在运行")
                    return True
            except Exception:
                pass

            # 启动 Appium
            self.appium_process = subprocess.Popen(
                ["appium", "-p", str(self.config.appium.port),
                 "--relaxed-security"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # 等待 Appium 就绪
            logger.info(
                f"等待 Appium 启动（超时: {self.config.appium.startup_timeout}秒）...")
            start_time = time.time()

            while time.time() - start_time < self.config.appium.startup_timeout:
                try:
                    response = requests.get(
                        f"{self.config.appium.base_url}/status", timeout=5)
                    if response.status_code == 200:
                        logger.info("Appium 服务已就绪")
                        return True
                except Exception:
                    pass
                time.sleep(1)

            logger.error("Appium 启动超时")
            return False

        except Exception as e:
            logger.error(f"启动 Appium 失败: {e}")
            return False

    def run_tests(self) -> int:
        """运行测试"""
        logger.info("=" * 60)
        logger.info("运行 E2E 测试")
        logger.info("=" * 60)

        # 确保报告目录存在
        os.makedirs(self.config.report_dir, exist_ok=True)

        # 构建 pytest 命令
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(
            self.config.report_dir, f"e2e_report_{timestamp}.html")

        cmd = [
            "python", "-m", "pytest",
            "tests/test_castplay_e2e.py",
            "-v",
            "--tb=short",
            "-s",
            f"--html={report_file}",
            "--self-contained-html"
        ]

        # 添加测试过滤
        if self.args.test:
            cmd.extend(["-k", self.args.test])

        logger.info(f"执行命令: {' '.join(cmd)}")

        # 运行测试
        result = subprocess.run(cmd, cwd=str(Path(__file__).parent))

        logger.info("=" * 60)
        if result.returncode == 0:
            logger.info("✓ 测试全部通过")
        else:
            logger.info(f"✗ 测试失败 (退出码: {result.returncode})")
        logger.info(f"测试报告: {report_file}")
        logger.info("=" * 60)

        return result.returncode

    def cleanup(self):
        """清理资源"""
        logger.info("=" * 60)
        logger.info("清理资源")
        logger.info("=" * 60)

        # 停止 Appium
        if self.appium_process:
            try:
                self.appium_process.terminate()
                self.appium_process.wait(timeout=10)
                logger.info("✓ Appium 已停止")
            except Exception:
                self.appium_process.kill()

        # 停止后端（如果是我们启动的）
        if self.backend and self.backend.process and not self.args.skip_backend:
            self.backend.stop()
            logger.info("✓ 后端服务已停止")

        # 停止模拟器（如果是我们启动的）
        if self.emulator and self.emulator.emulator_process and not self.args.skip_emulator:
            self.emulator.stop()
            logger.info("✓ 模拟器已停止")

    def run(self) -> int:
        """运行完整测试流程"""
        try:
            # 1. 检查环境
            if not self.check_prerequisites():
                logger.error("环境检查失败")
                return 1

            # 2. 启动模拟器
            if not self.start_emulator():
                logger.error("模拟器启动失败")
                return 1

            # 3. 启动后端
            if not self.start_backend():
                logger.error("后端服务启动失败")
                return 1

            # 4. 启动 Appium
            if not self.start_appium():
                logger.error("Appium 启动失败")
                return 1

            # 5. 运行测试
            return self.run_tests()

        finally:
            # 6. 清理
            if not self.args.no_cleanup:
                self.cleanup()


def main():
    parser = argparse.ArgumentParser(
        description="CastPlay E2E 自动化测试运行器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    # 完整运行（启动模拟器、后端、Appium）
    python run_e2e_tests.py

    # 指定 AVD
    python run_e2e_tests.py --avd Pixel_6_API_33

    # 无头模式运行
    python run_e2e_tests.py --headless

    # 跳过模拟器启动（使用已运行的）
    python run_e2e_tests.py --skip-emulator

    # 只运行设备注册测试
    python run_e2e_tests.py --test "registration"

    # 不清理资源（调试用）
    python run_e2e_tests.py --no-cleanup
        """
    )

    parser.add_argument(
        "--avd",
        help="指定 AVD 名称"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="无头模式运行模拟器"
    )
    parser.add_argument(
        "--skip-emulator",
        action="store_true",
        help="跳过模拟器启动（使用已运行的）"
    )
    parser.add_argument(
        "--skip-backend",
        action="store_true",
        help="跳过后端服务启动（使用已运行的）"
    )
    parser.add_argument(
        "--test", "-k",
        help="只运行匹配的测试（pytest -k 参数）"
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="测试后不清理资源（调试用）"
    )

    args = parser.parse_args()

    runner = E2ETestRunner(args)
    sys.exit(runner.run())


if __name__ == "__main__":
    main()
