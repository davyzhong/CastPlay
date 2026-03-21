#!/usr/bin/env python
"""
Android 播放端自动化测试运行脚本

运行 Android 播放端的单元测试和集成测试。

前置条件：
    - 集成测试使用内存数据库，不需要启动服务器
    - E2E 测试需要先启动服务器: python scripts/testing/start_android_env.py

运行方式：
    # 运行所有 Android 播放端测试
    python scripts/testing/run_android_tests.py

    # 运行单元测试
    python scripts/testing/run_android_tests.py --unit

    # 运行集成测试（API 测试）
    python scripts/testing/run_android_tests.py --integration

    # 显示详细输出
    python scripts/testing/run_android_tests.py -v

依赖安装：
    pip install pytest
"""
import argparse
import subprocess
import sys
import os
from pathlib import Path


class AndroidTestRunner:
    """Android 播放端测试运行器"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.tests_dir = self.project_root / "tests"

    def check_dependencies(self):
        """检查依赖是否安装"""
        try:
            import pytest
            print("✓ pytest 已安装")
            return True
        except ImportError:
            print("✗ pytest 未安装，请运行: pip install pytest")
            return False

    def run_unit_tests(self, verbose=False):
        """运行 Android 播放端单元测试"""
        print("\n" + "=" * 50)
        print("运行 Android 播放端单元测试")
        print("=" * 50 + "\n")

        args = [
            sys.executable, "-m", "pytest",
            "tests/unit/test_android_models.py",
            "-v" if verbose else ""
        ]
        args = [a for a in args if a]  # 移除空字符串

        result = subprocess.run(args, cwd=self.project_root)
        return result.returncode

    def run_integration_tests(self, verbose=False):
        """运行 Android 播放端集成测试（不需要服务器）"""
        print("\n" + "=" * 50)
        print("运行 Android 播放端集成测试 (API)")
        print("=" * 50 + "\n")

        args = [
            sys.executable, "-m", "pytest",
            "tests/integration/test_android_features.py",
            "-v" if verbose else ""
        ]
        args = [a for a in args if a]  # 移除空字符串

        result = subprocess.run(args, cwd=self.project_root)
        return result.returncode

    def run_all_tests(self, verbose=False):
        """运行所有 Android 播放端测试"""
        print("\n" + "=" * 50)
        print("运行所有 Android 播放端测试")
        print("=" * 50 + "\n")

        if not self.check_dependencies():
            return 1

        # 运行单元测试
        unit_result = self.run_unit_tests(verbose)

        # 运行集成测试
        integration_result = self.run_integration_tests(verbose)

        if unit_result == 0 and integration_result == 0:
            print("\n✓ 所有 Android 播放端测试通过！")
            return 0
        else:
            print(f"\n✗ 测试失败: 单元测试={unit_result}, 集成测试={integration_result}")
            return 1


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Android 播放端自动化测试运行器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 运行所有 Android 播放端测试
  python scripts/testing/run_android_tests.py

  # 只运行单元测试
  python scripts/testing/run_android_tests.py --unit

  # 只运行集成测试
  python scripts/testing/run_android_tests.py --integration

  # 显示详细输出
  python scripts/testing/run_android_tests.py -v
        """
    )

    parser.add_argument(
        "--unit",
        action="store_true",
        help="只运行单元测试"
    )

    parser.add_argument(
        "--integration",
        action="store_true",
        help="只运行集成测试"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="显示详细输出"
    )

    args = parser.parse_args()

    runner = AndroidTestRunner()

    if args.unit:
        sys.exit(runner.run_unit_tests(args.verbose))
    elif args.integration:
        sys.exit(runner.run_integration_tests(args.verbose))
    else:
        sys.exit(runner.run_all_tests(args.verbose))


if __name__ == "__main__":
    main()
