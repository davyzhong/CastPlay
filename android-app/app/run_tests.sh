#!/bin/bash
# ============================================================
# Android 测试运行脚本
# ============================================================
#
# 用法:
#   ./run_tests.sh [unit|instrumented|all]
#
# 示例:
#   ./run_tests.sh unit        # 仅运行单元测试
#   ./run_tests.sh instrumented # 运行仪器测试（需连接设备/模拟器）
#   ./run_tests.sh all         # 运行全部测试
#   ./run_tests.sh             # 默认运行单元测试
#
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo ""
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# 运行单元测试
run_unit_tests() {
    print_header "运行单元测试 (JVM)"

    cd "$PROJECT_DIR"

    echo "执行: ./gradlew testDebugUnitTest"

    if ./gradlew testDebugUnitTest --info; then
        print_success "单元测试通过"

        # 显示测试报告路径
        REPORT_PATH="$PROJECT_DIR/app/build/reports/tests/testDebugUnitTest/index.html"
        if [ -f "$REPORT_PATH" ]; then
            echo ""
            echo "测试报告: file://$REPORT_PATH"
        fi
        return 0
    else
        print_error "单元测试失败"
        return 1
    fi
}

# 运行仪器测试
run_instrumented_tests() {
    print_header "运行仪器测试 (Android Device/Emulator)"

    # 检查设备连接
    if ! adb devices | grep -q "device$"; then
        print_warning "未检测到 Android 设备或模拟器"
        echo "请确保:"
        echo "  1. 已启动 Android 模拟器，或"
        echo "  2. 已通过 USB 连接真机并启用调试"
        return 1
    fi

    cd "$PROJECT_DIR"

    echo "执行: ./gradlew connectedDebugAndroidTest"

    if ./gradlew connectedDebugAndroidTest --info; then
        print_success "仪器测试通过"

        # 显示测试报告路径
        REPORT_PATH="$PROJECT_DIR/app/build/reports/androidTests/connected/index.html"
        if [ -f "$REPORT_PATH" ]; then
            echo ""
            echo "测试报告: file://$REPORT_PATH"
        fi
        return 0
    else
        print_error "仪器测试失败"
        return 1
    fi
}

# 检查后端服务
check_backend() {
    print_header "检查后端服务"

    BACKEND_URL="http://localhost:5001/api/health"

    if curl -s --connect-timeout 5 "$BACKEND_URL" > /dev/null 2>&1; then
        print_success "后端服务运行中"
        return 0
    else
        print_warning "后端服务未运行"
        echo "端到端测试需要后端服务支持"
        echo "请运行: cd castplay-server && python run.py"
        return 1
    fi
}

# 显示帮助
show_help() {
    echo "用法: $0 [unit|instrumented|all|help]"
    echo ""
    echo "选项:"
    echo "  unit         运行单元测试（JVM，无需设备）"
    echo "  instrumented 运行仪器测试（需要设备/模拟器）"
    echo "  all          运行全部测试"
    echo "  help         显示此帮助"
    echo ""
    echo "测试文件位置:"
    echo "  单元测试:   app/src/test/java/com/castplay/player/"
    echo "  仪器测试:   app/src/androidTest/java/com/castplay/player/"
}

# 主入口
main() {
    case "${1:-unit}" in
        unit)
            run_unit_tests
            ;;
        instrumented)
            check_backend || true
            run_instrumented_tests
            ;;
        all)
            check_backend || true
            run_unit_tests && run_instrumented_tests
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
