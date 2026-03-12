"""
CastPlay All-in-One 测试运行脚本

提供便捷的测试运行命令
"""
import argparse
import subprocess
import sys
import os
from pathlib import Path


class TestRunner:
    """测试运行器"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.tests_dir = self.project_root / "tests"
        self.coverage_dir = self.project_root / "htmlcov"
        self.pytest_args = []

    def run_all_tests(self, verbose=False):
        """运行所有测试"""
        args = ["pytest", "tests/"]
        if verbose:
            args.append("-v")
        self._run_pytest(args)

    def run_unit_tests(self, verbose=False):
        """运行单元测试"""
        args = ["pytest", "tests/unit/", "-m", "unit"]
        if verbose:
            args.append("-v")
        self._run_pytest(args)

    def run_integration_tests(self, verbose=False):
        """运行集成测试"""
        args = ["pytest", "tests/integration/", "-m", "integration"]
        if verbose:
            args.append("-v")
        self._run_pytest(args)

    def run_e2e_tests(self, verbose=False):
        """运行端到端测试"""
        args = ["pytest", "tests/e2e/", "-m", "e2e"]
        if verbose:
            args.append("-v")
        self._run_pytest(args)

    def run_performance_tests(self, verbose=False):
        """运行性能测试"""
        args = ["pytest", "tests/performance/", "-m", "performance"]
        if verbose:
            args.append("-v")
        # 性能测试通常需要运行
        args.append("--runslow")
        self._run_pytest(args)

    def run_specific_test(self, test_path, verbose=False):
        """运行特定测试"""
        args = ["pytest", test_path]
        if verbose:
            args.append("-v")
        self._run_pytest(args)

    def run_with_coverage(self, verbose=False):
        """运行测试并生成覆盖率报告"""
        args = [
            "pytest",
            "tests/",
            "--cov=app",
            "--cov-report=html",
            "--cov-report=term",
            "--cov-report=xml",
        ]
        if verbose:
            args.append("-v")
        self._run_pytest(args)

        # 打开覆盖率报告
        if self.coverage_dir.exists():
            index_file = self.coverage_dir / "index.html"
            print(f"\n覆盖率报告已生成: {index_file}")
            print("在浏览器中打开查看详细报告")

    def run_with_parallel(self, workers=4, verbose=False):
        """并行运行测试"""
        args = [
            "pytest",
            "tests/",
            "-n", str(workers),
        ]
        if verbose:
            args.append("-v")
        self._run_pytest(args)

    def run_slow_tests(self, verbose=False):
        """运行慢速测试"""
        args = ["pytest", "tests/", "-m", "slow"]
        if verbose:
            args.append("-v")
        self._run_pytest(args)

    def run_fast_tests_only(self, verbose=False):
        """只运行快速测试（排除慢速测试）"""
        args = ["pytest", "tests/", "-m", "not slow"]
        if verbose:
            args.append("-v")
        self._run_pytest(args)

    def _run_pytest(self, args):
        """运行 pytest"""
        # 确保在项目根目录
        os.chdir(self.project_root)

        # 打印执行命令
        print(f"执行: pytest {' '.join(args)}")
        print("-" * 50)

        # 运行 pytest
        result = subprocess.run(
            [sys.executable, "-m", "pytest"] + args,
            cwd=self.project_root
        )

        sys.exit(result.returncode)

    def show_help(self):
        """显示帮助信息"""
        print("CastPlay All-in-One 测试运行器")
        print("=" * 50)
        print("\n用法:")
        print("  python tests/run_tests.py [命令] [选项]")
        print("\n命令:")
        print("  all          运行所有测试")
        print("  unit         运行单元测试")
        print("  integration  运行集成测试")
        print("  e2e          运行端到端测试")
        print("  performance  运行性能测试")
        print("  coverage     运行测试并生成覆盖率报告")
        print("  parallel     并行运行测试")
        print("  slow         运行慢速测试")
        print("  fast         只运行快速测试")
        print("  <path>       运行指定路径的测试")
        print("\n选项:")
        print("  -v, --verbose  显示详细输出")
        print("  -w, --workers  并行工作线程数（默认: 4）")
        print("\n示例:")
        print("  python tests/run_tests.py all -v")
        print("  python tests/run_tests.py unit")
        print("  python tests/run_tests.py coverage")
        print("  python tests/run_tests.py tests/unit/test_models.py -v")
        print("  python tests/run_tests.py parallel -w 8")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="CastPlay All-in-One 测试运行器",
        add_help=False
    )

    parser.add_argument(
        "command",
        nargs="?",
        default="all",
        help="测试命令"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="显示详细输出"
    )

    parser.add_argument(
        "-w", "--workers",
        type=int,
        default=4,
        help="并行工作线程数"
    )

    parser.add_argument(
        "-h", "--help",
        action="store_true",
        help="显示帮助信息"
    )

    args = parser.parse_args()

    if args.help:
        runner = TestRunner()
        runner.show_help()
        return

    runner = TestRunner()
    verbose = args.verbose
    workers = args.workers

    if args.command == "all":
        runner.run_all_tests(verbose)
    elif args.command == "unit":
        runner.run_unit_tests(verbose)
    elif args.command == "integration":
        runner.run_integration_tests(verbose)
    elif args.command == "e2e":
        runner.run_e2e_tests(verbose)
    elif args.command == "performance":
        runner.run_performance_tests(verbose)
    elif args.command == "coverage":
        runner.run_with_coverage(verbose)
    elif args.command == "parallel":
        runner.run_with_parallel(workers, verbose)
    elif args.command == "slow":
        runner.run_slow_tests(verbose)
    elif args.command == "fast":
        runner.run_fast_tests_only(verbose)
    elif os.path.exists(args.command):
        runner.run_specific_test(args.command, verbose)
    else:
        print(f"未知命令: {args.command}")
        runner.show_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
