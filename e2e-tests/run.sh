#!/bin/bash
# ============================================================
# CastPlay E2E 自动化测试快速启动脚本
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo ""
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================${NC}"
    echo ""
}

print_step() {
    echo -e "${GREEN}>>> $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# 检查 Python 环境
check_python() {
    print_step "检查 Python 环境..."

    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装"
        exit 1
    fi

    python3 --version
}

# 安装依赖
install_deps() {
    print_step "安装 Python 依赖..."
    pip3 install -r requirements.txt
}

# 检查 Appium
check_appium() {
    print_step "检查 Appium..."

    if ! command -v appium &> /dev/null; then
        print_warning "Appium 未安装，正在安装..."
        npm install -g appium
        appium driver install uiautomator2
    fi

    appium --version
}

# 检查 Android SDK
check_android_sdk() {
    print_step "检查 Android SDK..."

    if [ -z "$ANDROID_HOME" ]; then
        # 尝试常见路径
        if [ -d "$HOME/Library/Android/sdk" ]; then
            export ANDROID_HOME="$HOME/Library/Android/sdk"
        elif [ -d "$HOME/Android/Sdk" ]; then
            export ANDROID_HOME="$HOME/Android/Sdk"
        else
            print_error "ANDROID_HOME 未设置"
            echo "请设置: export ANDROID_HOME=/path/to/android/sdk"
            exit 1
        fi
    fi

    echo "ANDROID_HOME: $ANDROID_HOME"

    # 检查 emulator
    if [ ! -f "$ANDROID_HOME/emulator/emulator" ]; then
        print_error "Android Emulator 未安装"
        exit 1
    fi

    # 列出 AVD
    echo "可用的 AVD:"
    $ANDROID_HOME/emulator/emulator -list-avds
}

# 启动测试
run_tests() {
    print_header "启动 E2E 测试"

    # 确保报告目录存在
    mkdir -p reports

    python3 run_e2e_tests.py "$@"
}

# 显示帮助
show_help() {
    echo "用法: $0 [command] [options]"
    echo ""
    echo "命令:"
    echo "  setup       安装依赖和检查环境"
    echo "  run         运行测试"
    echo "  help        显示帮助"
    echo ""
    echo "运行选项 (传递给 run_e2e_tests.py):"
    echo "  --avd NAME           指定 AVD 名称"
    echo "  --headless           无头模式"
    echo "  --skip-emulator      跳过模拟器启动"
    echo "  --skip-backend       跳过后端启动"
    echo "  --test PATTERN       只运行匹配的测试"
    echo "  --no-cleanup         不清理资源"
    echo ""
    echo "示例:"
    echo "  $0 setup                            # 设置环境"
    echo "  $0 run                              # 运行全部测试"
    echo "  $0 run --skip-emulator              # 使用已运行的模拟器"
    echo "  $0 run --test registration          # 只运行注册测试"
}

# 主入口
main() {
    case "${1:-run}" in
        setup)
            print_header "设置测试环境"
            check_python
            install_deps
            check_appium
            check_android_sdk
            echo ""
            echo -e "${GREEN}✓ 环境设置完成${NC}"
            ;;
        run)
            shift
            run_tests "$@"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
