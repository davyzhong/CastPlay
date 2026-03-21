#!/usr/bin/env python
"""
Web 播放端自动化测试运行脚本

运行 Web 播放端的集成测试和 E2E 测试。

前置条件：
    1. 后端服务器已启动 (运行 scripts/testing/start_web_env.py)
    2. 访问地址: http://localhost:8000

运行方式：
    # 运行所有 Web 播放端测试
    python scripts/testing/run_web_tests.py

    # 运行集成测试（API 测试，不需要服务器）
    python scripts/testing/run_web_tests.py --integration

    # 运行 E2E 测试（Playwright 浏览器测试，需要服务器）
    python scripts/testing/run_web_tests.py --e2e

    # 显示浏览器窗口
    python scripts/testing/run_web_tests.py --e2e --headed

    # 慢速模式（便于观察）
    python scripts/testing/run_web_tests.py --e2e --headed --slowmo=500

依赖安装：
    pip install pytest pytest-playwright
    playwright install chromium
"""
import argparse
import subprocess
import sys
import os
import requests
from pathlib import Path


class WebPlayerTestRunner:
    """Web 播放端测试运行器"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.tests_dir = self.project_root / "tests"
        self.base_url = "http://localhost:8000"

    def check_dependencies(self):
        """检查依赖是否安装"""
        try:
            import pytest
            print("✓ pytest 已安装")
            return True
        except ImportError:
            print("✗ pytest 未安装，请运行: pip install pytest")
            return False

    def check_playwright(self):
        """检查 Playwright 是否安装"""
        try:
            import playwright
            print("✓ playwright 已安装")
            return True
        except ImportError:
            print("✗ playwright 未安装，请运行: pip install pytest-playwright")
            return False

    def check_server(self):
        """检查后端服务器是否运行"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=2)
            if response.status_code == 200:
                print(f"✓ 后端服务器运行中: {self.base_url}")
                return True
        except Exception:
            pass

        print(f"✗ 后端服务器未运行: {self.base_url}")
        print("  请先启动服务器: python scripts/start_web_player_test_env.py")
        return False

    def run_integration_tests(self, verbose=False):
        """运行 Web 播放端集成测试（不需要服务器）"""
        print("\n" + "=" * 50)
        print("运行 Web 播放端集成测试 (API)")
        print("=" * 50 + "\n")

        args = [
            sys.executable, "-m", "pytest",
            "tests/integration/test_web_player_features.py",
            "-v" if verbose else ""
        ]
        args = [a for a in args if a]  # 移除空字符串

        result = subprocess.run(args, cwd=self.project_root)
        return result.returncode

    def run_e2e_tests(self, verbose=False, headed=False, slowmo=0):
        """运行 Web 播放端 E2E 测试（需要服务器）"""
        print("\n" + "=" * 50)
        print("运行 Web 播放端 E2E 测试 (Playwright)")
        print("=" * 50 + "\n")

        if not self.check_playwright():
            return 1

        # 检查服务器是否运行
        if not self.check_server():
            return 1

        args = [
            sys.executable, "-m", "pytest",
            "tests/e2e/test_web_player.py",
            "-v" if verbose else "",
        ]

        if headed:
            args.append("--headed")

        if slowmo > 0:
            args.append(f"--slowmo={slowmo}")

        args = [a for a in args if a]  # 移除空字符串

        result = subprocess.run(args, cwd=self.project_root)
        return result.returncode

    def run_all_tests(self, verbose=False, headed=False, slowmo=0):
        """运行所有 Web 播放端测试"""
        print("\n" + "=" * 50)
        print("运行所有 Web 播放端测试")
        print("=" * 50 + "\n")

        if not self.check_dependencies():
            return 1

        # 运行集成测试
        integration_result = self.run_integration_tests(verbose)

        # 运行 E2E 测试
        e2e_result = self.run_e2e_tests(verbose, headed, slowmo)

        if integration_result == 0 and e2e_result == 0:
            print("\n✓ 所有 Web 播放端测试通过！")
            return 0
        else:
            print(f"\n✗ 测试失败: 集成测试={integration_result}, E2E测试={e2e_result}")
            return 1

    def install_playwright(self):
        """安装 Playwright 浏览器"""
        print("安装 Playwright 浏览器...")
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            cwd=self.project_root
        )
        return result.returncode


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Web 播放端自动化测试运行器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
前置条件:
  E2E 测试需要先启动后端服务器:
    python scripts/testing/start_web_env.py

示例:
  # 运行所有 Web 播放端测试
  python scripts/testing/run_web_tests.py

  # 只运行集成测试（不需要服务器）
  python scripts/testing/run_web_tests.py --integration

  # 只运行 E2E 测试（需要服务器）
  python scripts/testing/run_web_tests.py --e2e

  # 显示浏览器窗口
  python scripts/testing/run_web_tests.py --e2e --headed

  # 慢速模式
  python scripts/testing/run_web_tests.py --e2e --headed --slowmo=500

  # 安装 Playwright 浏览器
  python scripts/testing/run_web_tests.py --install-playwright
        """
    )

    parser.add_argument(
        "--integration",
        action="store_true",
        help="只运行集成测试（不需要服务器）"
    )

    parser.add_argument(
        "--e2e",
        action="store_true",
        help="只运行 E2E 测试（需要服务器）"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="显示详细输出"
    )

    parser.add_argument(
        "--headed",
        action="store_true",
        help="显示浏览器窗口（仅 E2E 测试）"
    )

    parser.add_argument(
        "--slowmo",
        type=int,
        default=0,
        help="慢速模式延迟（毫秒，仅 E2E 测试）"
    )

    parser.add_argument(
        "--install-playwright",
        action="store_true",
        help="安装 Playwright 浏览器"
    )

    args = parser.parse_args()

    runner = WebPlayerTestRunner()

    if args.install_playwright:
        sys.exit(runner.install_playwright())

    if args.integration:
        sys.exit(runner.run_integration_tests(args.verbose))
    elif args.e2e:
        sys.exit(runner.run_e2e_tests(args.verbose, args.headed, args.slowmo))
    else:
        sys.exit(runner.run_all_tests(args.verbose, args.headed, args.slowmo))


if __name__ == "__main__":
    main()
