#!/usr/bin/env python3
"""
Test Runner Script for CastPlay Server
执行单元测试和生成覆盖率报告
"""
import sys
import subprocess
import os


def run_tests(test_type='all', verbose=True, coverage=True):
    """
    运行测试

    Args:
        test_type: 测试类型 ('all', 'unit', 'integration')
        verbose: 是否显示详细输出
        coverage: 是否生成覆盖率报告
    """
    # 切换到项目根目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # 构建 pytest 命令
    cmd = ['pytest']

    # 添加测试类型标记
    if test_type == 'unit':
        cmd.extend(['-m', 'unit', 'tests/unit'])
    elif test_type == 'integration':
        cmd.extend(['-m', 'integration', 'tests/integration'])
    else:
        cmd.append('tests/')

    # 添加详细输出
    if verbose:
        cmd.append('-v')

    # 添加覆盖率
    if coverage:
        cmd.extend([
            '--cov=app',
            '--cov-report=html',
            '--cov-report=term-missing'
        ])

    print(f"Running command: {' '.join(cmd)}")
    print("=" * 70)

    # 执行测试
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("\n" + "=" * 70)
        print("✅ All tests passed!")
        if coverage:
            print("📊 Coverage report generated in htmlcov/index.html")
    else:
        print("\n" + "=" * 70)
        print("❌ Some tests failed!")

    return result.returncode


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='Run CastPlay Server tests')
    parser.add_argument(
        '--type',
        choices=['all', 'unit', 'integration'],
        default='all',
        help='Type of tests to run (default: all)'
    )
    parser.add_argument(
        '--no-coverage',
        action='store_true',
        help='Disable coverage report'
    )
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Quiet mode (less verbose)'
    )

    args = parser.parse_args()

    exit_code = run_tests(
        test_type=args.type,
        verbose=not args.quiet,
        coverage=not args.no_coverage
    )

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
