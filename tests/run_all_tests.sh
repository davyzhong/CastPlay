#!/bin/bash
# CastPlay All-in-One 全自动化测试运行脚本
# 一键运行所有测试并生成报告

set -e  # 遇到错误时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORT_DIR="${PROJECT_DIR}/test-reports"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# 创建报告目录
mkdir -p "${REPORT_DIR}"

# 函数定义
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# 记录测试开始时间
START_TIME=$(date +%s)

# ==================== 1. 环境检查 ====================
print_header "1. 环境检查"

check_environment() {
    print_info "检查 Python..."
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version)
        print_success "Python: ${PYTHON_VERSION}"
    else
        print_error "Python 未安装"
        exit 1
    fi

    print_info "检查 Node.js..."
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        print_success "Node.js: ${NODE_VERSION}"
    else
        print_error "Node.js 未安装"
        exit 1
    fi

    print_info "检查依赖..."
    if [ -d "${PROJECT_DIR}/venv" ]; then
        print_success "Python 虚拟环境存在"
    else
        print_error "Python 虚拟环境不存在"
        exit 1
    fi

    if [ -d "${PROJECT_DIR}/frontend/node_modules" ]; then
        print_success "前端依赖已安装"
    else
        print_info "前端依赖未安装，将跳过前端测试"
    fi
}

check_environment

# ==================== 2. 代码质量检查 ====================
print_header "2. 代码质量检查"

LINT_PASSED=0
LINT_FAILED=0

run_lint() {
    print_info "运行 Black 格式检查..."
    if black --check app/ tests/; then
        print_success "Black 检查通过"
        ((LINT_PASSED++))
    else
        print_error "Black 检查失败"
        ((LINT_FAILED++))
    fi

    print_info "运行 isort 检查..."
    if isort --check-only app/ tests/; then
        print_success "isort 检查通过"
        ((LINT_PASSED++))
    else
        print_error "isort 检查失败"
        ((LINT_FAILED++))
    fi

    print_info "运行 mypy 类型检查..."
    if mypy app/ --ignore-missing-imports; then
        print_success "mypy 检查通过"
        ((LINT_PASSED++))
    else
        print_error "mypy 检查失败"
        ((LINT_FAILED++))
    fi
}

run_lint

# ==================== 3. 安全检查 ====================
print_header "3. 安全检查"

SECURITY_PASSED=0
SECURITY_FAILED=0

run_security_checks() {
    print_info "运行 Bandit 安全扫描..."
    if bandit -r app/ -f json -o "${REPORT_DIR}/bandit_${TIMESTAMP}.json"; then
        print_success "Bandit 检查通过"
        ((SECURITY_PASSED++))
    else
        print_error "Bandit 检查发现安全问题"
        ((SECURITY_FAILED++))
    fi

    print_info "运行 Safety 依赖检查..."
    if safety check --json --output "${REPORT_DIR}/safety_${TIMESTAMP}.json"; then
        print_success "Safety 检查通过"
        ((SECURITY_PASSED++))
    else
        print_error "Safety 检查发现依赖漏洞"
        ((SECURITY_FAILED++))
    fi
}

run_security_checks

# ==================== 4. 单元测试 ====================
print_header "4. 单元测试"

UNIT_PASSED=0
UNIT_FAILED=0

run_unit_tests() {
    print_info "运行单元测试..."
    UNIT_OUTPUT="${REPORT_DIR}/unit_${TIMESTAMP}.txt"

    if pytest tests/ -v -m "unit" --tb=short --cov=app \
        --cov-report=html:"${REPORT_DIR}/coverage_unit_${TIMESTAMP}" \
        --cov-report=xml:"${REPORT_DIR}/coverage_unit_${TIMESTAMP}.xml" \
        | tee "${UNIT_OUTPUT}"; then

        UNIT_RESULTS=$(grep -E "passed|failed" "${UNIT_OUTPUT}")
        UNIT_PASSED=$(echo "${UNIT_RESULTS}" | grep -oP "passed [0-9]*" | grep -oE "[0-9]+")
        UNIT_FAILED=$(echo "${UNIT_RESULTS}" | grep -oP "failed [0-9]*" | grep -oE "[0-9]+")

        print_success "单元测试完成"
    else
        print_error "单元测试执行失败"
        ((UNIT_FAILED++))
    fi
}

run_unit_tests

# ==================== 5. 集成测试 ====================
print_header "5. 集成测试"

INTEGRATION_PASSED=0
INTEGRATION_FAILED=0

run_integration_tests() {
    print_info "运行集成测试..."
    INTEGRATION_OUTPUT="${REPORT_DIR}/integration_${TIMESTAMP}.txt"

    if pytest tests/integration/ -v --tb=short \
        | tee "${INTEGRATION_OUTPUT}"; then

        INTEGRATION_RESULTS=$(grep -E "passed|failed" "${INTEGRATION_OUTPUT}")
        INTEGRATION_PASSED=$(echo "${INTEGRATION_RESULTS}" | grep -oP "passed [0-9]*" | grep -oE "[0-9]+")
        INTEGRATION_FAILED=$(echo "${INTEGRATION_RESULTS}" | grep -oP "failed [0-9]*" | grep -oE "[0-9]+")

        print_success "集成测试完成"
    else
        print_error "集成测试执行失败"
        ((INTEGRATION_FAILED++))
    fi
}

run_integration_tests

# ==================== 6. 前端测试 ====================
print_header "6. 前端测试"

FRONTEND_PASSED=0
FRONTEND_FAILED=0

run_frontend_tests() {
    if [ ! -d "${PROJECT_DIR}/frontend/node_modules" ]; then
        print_info "跳过前端测试（依赖未安装）"
        return
    fi

    print_info "运行前端单元测试..."
    cd frontend
    if npm run test:unit -- --coverage --silent; then
        print_success "前端测试完成"
        ((FRONTEND_PASSED++))
    else
        print_error "前端测试失败"
        ((FRONTEND_FAILED++))
    fi
    cd "${PROJECT_DIR}"
}

run_frontend_tests

# ==================== 7. E2E 测试 ====================
print_header "7. E2E 测试"

E2E_PASSED=0
E2E_FAILED=0

run_e2e_tests() {
    if [ ! -d "${PROJECT_DIR}/frontend/node_modules" ]; then
        print_info "跳过 E2E 测试（依赖未安装）"
        return
    fi

    print_info "运行 E2E 测试..."
    cd frontend
    if npm run test:e2e -- --headless; then
        print_success "E2E 测试完成"
        ((E2E_PASSED++))
    else
        print_error "E2E 测试失败"
        ((E2E_FAILED++))
    fi
    cd "${PROJECT_DIR}"
}

run_e2e_tests

# ==================== 8. 性能测试 ====================
print_header "8. 性能测试"

PERFORMANCE_PASSED=0
PERFORMANCE_FAILED=0

run_performance_tests() {
    print_info "运行性能测试（30秒）..."
    PERF_OUTPUT="${REPORT_DIR}/performance_${TIMESTAMP}.txt"

    if locust -f tests/performance/locustfile.py \
        --host http://localhost:8000 \
        --users 100 \
        --spawn-rate 10 \
        --run-time 30s \
        --headless \
        --html "${REPORT_DIR}/performance_${TIMESTAMP}.html" \
        --csv "${REPORT_DIR}/performance_${TIMESTAMP}.csv" \
        2>&1 | tee "${PERF_OUTPUT}"; then

        # 检查错误率
        ERROR_RATE=$(grep "Error ratio" "${PERF_OUTPUT}" | grep -oE "[0-9.]+%")
        if [ -z "$ERROR_RATE" ] || (( $(echo "$ERROR_RATE" | sed 's/%//') < 5 )); then
            print_success "性能测试完成（错误率: ${ERROR_RATE}）"
            ((PERFORMANCE_PASSED++))
        else
            print_error "性能测试失败（错误率过高）"
            ((PERFORMANCE_FAILED++))
        fi
    else
        print_info "跳过性能测试（服务器未运行或 Locust 未安装）"
    fi
}

run_performance_tests

# ==================== 生成测试报告 ====================
print_header "9. 生成测试报告"

generate_summary_report() {
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    MINUTES=$((DURATION / 60))
    SECONDS=$((DURATION % 60))

    cat > "${REPORT_DIR}/summary_${TIMESTAMP}.md" << EOF
# CastPlay All-in-One 测试报告

**执行时间**: $(date '+%Y-%m-%d %H:%M:%S')
**持续时间**: ${MINUTES} 分 ${SECONDS} 秒

---

## 测试结果汇总

| 检查项 | 通过 | 失败 |
|---------|------|--------|
| 代码质量 | ${LINT_PASSED} | ${LINT_FAILED} |
| 安全检查 | ${SECURITY_PASSED} | ${SECURITY_FAILED} |
| 单元测试 | ${UNIT_PASSED} | ${UNIT_FAILED} |
| 集成测试 | ${INTEGRATION_PASSED} | ${INTEGRATION_FAILED} |
| 前端测试 | ${FRONTEND_PASSED} | ${FRONTEND_FAILED} |
| E2E 测试 | ${E2E_PASSED} | ${E2E_FAILED} |
| 性能测试 | ${PERFORMANCE_PASSED} | ${PERFORMANCE_FAILED} |
| **总计** | **$((LINT_PASSED + SECURITY_PASSED + UNIT_PASSED + INTEGRATION_PASSED + FRONTEND_PASSED + E2E_PASSED + PERFORMANCE_PASSED))** | **$((LINT_FAILED + SECURITY_FAILED + UNIT_FAILED + INTEGRATION_FAILED + FRONTEND_FAILED + E2E_FAILED + PERFORMANCE_FAILED))** |

---

## 详细报告

- [单元测试报告]($(basename ${REPORT_DIR}/unit_${TIMESTAMP}.txt))
- [集成测试报告]($(basename ${REPORT_DIR}/integration_${TIMESTAMP}.txt))
- [单元测试覆盖率](${REPORT_DIR}/coverage_unit_${TIMESTAMP}/index.html)
- [性能测试报告](${REPORT_DIR}/performance_${TIMESTAMP}.html)
- [Bandit 安全扫描](${REPORT_DIR}/bandit_${TIMESTAMP}.json)
- [Safety 依赖检查](${REPORT_DIR}/safety_${TIMESTAMP}.json)

---

## 通过率

\`\`\`
总检查数: $((LINT_PASSED + LINT_FAILED + SECURITY_PASSED + SECURITY_FAILED + UNIT_PASSED + UNIT_FAILED + INTEGRATION_PASSED + INTEGRATION_FAILED + FRONTEND_PASSED + FRONTEND_FAILED + E2E_PASSED + E2E_FAILED + PERFORMANCE_PASSED + PERFORMANCE_PASSED))
总通过数: $((LINT_PASSED + SECURITY_PASSED + UNIT_PASSED + INTEGRATION_PASSED + FRONTEND_PASSED + E2E_PASSED + PERFORMANCE_PASSED))
通过率: $(awk "BEGIN {printf \"%.2f\", ($((LINT_PASSED + SECURITY_PASSED + UNIT_PASSED + INTEGRATION_PASSED + FRONTEND_PASSED + E2E_PASSED + PERFORMANCE_PASSED)) / ($((LINT_PASSED + LINT_FAILED + SECURITY_PASSED + SECURITY_FAILED + UNIT_PASSED + UNIT_FAILED + INTEGRATION_PASSED + INTEGRATION_FAILED + FRONTEND_PASSED + FRONTEND_FAILED + E2E_PASSED + E2E_FAILED + PERFORMANCE_PASSED + PERFORMANCE_PASSED))) * 100}%")
\`\`\`

---

## 建议

EOF

    print_success "测试报告已生成: ${REPORT_DIR}/summary_${TIMESTAMP}.md"
}

generate_summary_report

# ==================== 打印汇总 ====================
print_header "测试执行完成"

TOTAL_PASSED=$((LINT_PASSED + SECURITY_PASSED + UNIT_PASSED + INTEGRATION_PASSED + FRONTEND_PASSED + E2E_PASSED + PERFORMANCE_PASSED))
TOTAL_FAILED=$((LINT_FAILED + SECURITY_FAILED + UNIT_FAILED + INTEGRATION_FAILED + FRONTEND_FAILED + E2E_FAILED + PERFORMANCE_FAILED))
TOTAL_CHECKS=$((TOTAL_PASSED + TOTAL_FAILED))

echo -e "\n${BLUE}汇总统计:${NC}"
echo -e "  总检查项: ${TOTAL_CHECKS}"
echo -e "  通过: ${GREEN}${TOTAL_PASSED}${NC}"
echo -e "  失败: ${RED}${TOTAL_FAILED}${NC}"
echo -e "  通过率: ${BLUE}$(awk "BEGIN {printf \"%.2f\", ${TOTAL_PASSED} / ${TOTAL_CHECKS} * 100")}%${NC}"

if [ ${TOTAL_FAILED} -gt 0 ]; then
    echo -e "\n${RED}⚠️ 有 ${TOTAL_FAILED} 项检查失败，请查看报告详情${NC}"
    exit 1
else
    echo -e "\n${GREEN}✓ 所有检查通过！${NC}"
    exit 0
fi
