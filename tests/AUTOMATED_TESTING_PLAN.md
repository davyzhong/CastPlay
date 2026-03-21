# CastPlay All-in-One 全自动化测试方案

## 目录
- [方案概述](#方案概述)
- [测试金字塔](#测试金字塔)
- [CI/CD 管道](#cicd-管道)
- [测试执行策略](#测试执行策略)
- [测试报告与质量门禁](#测试报告与质量门禁)
- [持续监控](#持续监控)

---

## 方案概述

### 目标
1. **全面覆盖** - 单元、集成、E2E、性能、安全
2. **自动化执行** - 每次提交自动运行测试
3. **快速反馈** - 分钟级测试反馈
4. **质量保证** - 代码覆盖率 > 80%，通过率 > 95%

### 测试工具栈

| 类型 | 工具 | 用途 |
|------|------|------|
| 单元测试 | pytest | Python 单元测试 |
| 集成测试 | pytest + pytest-asyncio | API 集成测试 |
| E2E 测试 | Playwright + Pytest | 端到端用户流程测试 |
| 性能测试 | Locust | 负载和压力测试 |
| 安全测试 | Bandit + Snyk | 静态安全扫描 |
| 代码质量 | Black, isort, mypy, pylint | 代码规范与类型检查 |
| API 测试 | Newman (Postman) | API 契约测试 |
| 覆盖率 | pytest-cov | 代码覆盖率统计 |

---

## 测试金字塔

```
         E2E 测试 (5%)
         ┌───────────┐
         │  10 个用例 │
         └───────────┘
              ↕
    集成测试 (20%)
    ┌─────────────────┐
    │   40 个用例   │
    └─────────────────┘
           ↕
  单元测试 (75%)
┌───────────────────────┐
│   150+ 个测试用例   │
└───────────────────────┘
```

### 测试分层职责

| 层级 | 范围 | 执行时间 | 维护成本 |
|------|------|-----------|----------|
| 单元测试 | 单个函数/方法 | < 1 分钟 | 低 |
| 集成测试 | API 端点 | < 5 分钟 | 中 |
| E2E 测试 | 完整用户流程 | < 15 分钟 | 高 |

---

## CI/CD 管道

### GitHub Actions 配置

```yaml
# .github/workflows/test.yml
name: CastPlay 测试管道

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

env:
  PYTHON_VERSION: '3.12'
  NODE_VERSION: '18'

jobs:
  # ==================== 后端测试 ====================
  backend-unit:
    name: 后端单元测试
    runs-on: ubuntu-latest
    timeout-minutes: 15

    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_DB: castplay_test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - name: 检出代码
        uses: actions/checkout@v4

      - name: 设置 Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'

      - name: 安装依赖
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio pytest-xdist

      - name: 运行单元测试
        run: |
          pytest tests/ -v --cov=app --cov-report=xml --cov-report=html \
            -m "unit" --tb=short

      - name: 上传覆盖率
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          flags: unit
          name: codecov-unit

      - name: 上传 HTML 报告
        uses: actions/upload-artifact@v3
        with:
          name: coverage-report-unit
          path: htmlcov

  backend-integration:
    name: 后端集成测试
    runs-on: ubuntu-latest
    timeout-minutes: 20

    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_DB: castplay_test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'

      - name: 安装依赖
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio

      - name: 运行集成测试
        run: |
          pytest tests/integration/ -v --cov=app --cov-append \
            --tb=short

      - name: 上传覆盖率
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          flags: integration
          name: codecov-integration

  # ==================== 前端测试 ====================
  frontend-unit:
    name: 前端单元测试
    runs-on: ubuntu-latest
    timeout-minutes: 15

    steps:
      - name: 检出代码
        uses: actions/checkout@v4

      - name: 设置 Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: 安装依赖
        working-directory: ./frontend
        run: npm ci

      - name: 运行单元测试
        working-directory: ./frontend
        run: npm run test:unit -- --coverage

      - name: 上传覆盖率
        uses: codecov/codecov-action@v3
        with:
          files: ./frontend/coverage/coverage-final.json
          flags: frontend-unit

  frontend-e2e:
    name: 前端 E2E 测试
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: 安装依赖
        working-directory: ./frontend
        run: npm ci

      - name: 安装 Playwright
        run: npx playwright install --with-deps

      - name: 运行 E2E 测试
        working-directory: ./frontend
        run: npm run test:e2e

      - name: 上传测试报告
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: frontend/playwright-report/

      - name: 上传测试截图
        uses: actions/upload-artifact@v3
        if: failure()
        with:
          name: playwright-screenshots
          path: frontend/test-results/

  # ==================== 代码质量检查 ====================
  code-quality:
    name: 代码质量检查
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'

      - name: 安装质量工具
        run: |
          pip install black isort mypy pylint bandit safety

      - name: Black 格式检查
        run: |
          black --check app/ tests/

      - name: isort 导入排序检查
        run: |
          isort --check-only app/ tests/

      - name: mypy 类型检查
        run: |
          mypy app/ --ignore-missing-imports

      - name: pylint 代码检查
        run: |
          pylint app/ --rcfile=.pylintrc --exit-zero

      - name: bandit 安全检查
        run: |
          bandit -r app/ -f json -o bandit-report.json

      - name: safety 依赖检查
        run: |
          safety check --json --output safety-report.json

  # ==================== 安全扫描 ====================
  security-scan:
    name: 安全扫描
    runs-on: ubuntu-latest
    timeout-minutes: 15

    steps:
      - uses: actions/checkout@v4

      - name: Snyk 安全扫描
        uses: snyk/actions/python@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}

  # ==================== API 契约测试 ====================
  api-contract:
    name: API 契约测试
    runs-on: ubuntu-latest
    timeout-minutes: 20

    steps:
      - uses: actions/checkout@v4

      - name: 启动测试服务器
        run: |
          pip install -r requirements.txt
          python scripts/run.py &
          sleep 10

      - name: 安装 Newman
        run: |
          npm install -g newman

      - name: 运行 API 测试
        run: |
          newman run tests/postman/castplay_collection.json \
            -e tests/postman/environments/test.json \
            --reporters cli,json,htmlextra \
            --reporter-cli-export tests/reports/api-test-report.html

      - name: 上传测试报告
        uses: actions/upload-artifact@v3
        with:
          name: api-test-report
          path: tests/reports/

  # ==================== 性能测试 ====================
  performance:
    name: 性能测试
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - uses: actions/checkout@v4

      - name: 设置 Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: 安装 Locust
        run: |
          pip install locust

      - name: 运行性能测试
        run: |
          locust -f tests/performance/locustfile.py \
            --host http://localhost:8000 \
            --users 100 \
            --spawn-rate 10 \
            --run-time 60s \
            --headless \
            --html tests/reports/performance-report.html

      - name: 上传性能报告
        uses: actions/upload-artifact@v3
        with:
          name: performance-report
          path: tests/reports/

  # ==================== 构建与部署 ====================
  build-and-deploy:
    name: 构建与部署
    runs-on: ubuntu-latest
    needs: [backend-unit, backend-integration, frontend-unit, frontend-e2e, code-quality]
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v4

      - name: 构建 Docker 镜像
        run: |
          docker build -t castplay:${{ github.sha }} .

      - name: 登录 Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: 推送镜像
        run: |
          docker push castplay:${{ github.sha }}
          docker tag castplay:${{ github.sha }} castplay:latest
          docker push castplay:latest

      - name: 部署到生产环境
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.DEPLOY_HOST }}
          username: ${{ secrets.DEPLOY_USER }}
          key: ${{ secrets.DEPLOY_KEY }}
          script: |
            docker pull castplay:latest
            docker stop castplay || true
            docker run -d --name castplay -p 8000:8000 \
              -v /data:/app/data castplay:latest
```

---

## 测试执行策略

### 分支策略

| 分支 | 触发 | 测试范围 |
|------|--------|---------|
| main | 每次 push | 全量测试 + 部署 |
| develop | 每次 push | 全量测试 |
| feature/* | 每次 push | 快速测试（单元 + 集成） |
| pull_request | 每次 PR | 全量测试 |

### 缓存策略

```yaml
# GitHub Actions 缓存配置
- name: 缓存 Python 依赖
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-

- name: 缓存 Node 依赖
  uses: actions/cache@v3
  with:
    path: frontend/node_modules
    key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-node-
```

### 并行执行

```yaml
# 关键测试并行运行
strategy:
  matrix:
    python-version: [3.10, 3.11, 3.12]
    os: [ubuntu-latest, macos-latest]
  fail-fast: false  # 一个失败不取消其他

# 或使用 pytest-xdist 并行
pytest tests/ -n auto --dist=loadscope
```

---

## 测试报告与质量门禁

### 质量门禁配置

```yaml
# 要求
quality_gate:
  unit_test_coverage: 80
  integration_test_coverage: 70
  e2e_test_pass_rate: 95
  code_quality_score: 8.0  # pylint 10分制
  security_issues: 0  # 不允许安全漏洞

# 执行条件
if: |
  github.event_name == 'pull_request' ||
  github.event_name == 'push' && github.ref == 'refs/heads/main'
```

### 测试报告仪表板

创建测试报告汇总页面 `tests/reports/dashboard.html`：

```html
<!DOCTYPE html>
<html>
<head>
  <title>CastPlay 测试仪表板</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    .dashboard { font-family: Arial, sans-serif; padding: 20px; }
    .metric { display: inline-block; margin: 10px; padding: 20px;
                border: 1px solid #ddd; border-radius: 8px; }
    .chart { width: 400px; height: 300px; display: inline-block; }
    .status-pass { color: #52c41a; }
    .status-fail { color: #f44336; }
    .status-pending { color: #f39c12; }
  </style>
</head>
<body>
  <div class="dashboard">
    <h1>CastPlay 测试报告</h1>

    <div class="metrics">
      <div class="metric">
        <h3>单元测试</h3>
        <p class="status-pass">✓ 142 / 150 通过</p>
        <p>覆盖率: 85%</p>
      </div>
      <div class="metric">
        <h3>集成测试</h3>
        <p class="status-pass">✓ 38 / 40 通过</p>
        <p>覆盖率: 72%</p>
      </div>
      <div class="metric">
        <h3>E2E 测试</h3>
        <p class="status-fail">✗ 8 / 10 通过</p>
        <p>通过率: 80%</p>
      </div>
      <div class="metric">
        <h3>性能测试</h3>
        <p class="status-pass">✓ 通过</p>
        <p>QPS: 1200</p>
      </div>
    </div>

    <div class="charts">
      <canvas id="coverageChart" class="chart"></canvas>
      <canvas id="trendChart" class="chart"></canvas>
    </div>

    <script>
      // 覆盖率趋势图
      const coverageCtx = document.getElementById('coverageChart').getContext('2d');
      new Chart(coverageCtx, {
        type: 'bar',
        data: {
          labels: ['Unit', 'Integration', 'E2E'],
          datasets: [{
            label: '覆盖率 %',
            data: [85, 72, 45],
            backgroundColor: ['#4caf50', '#2196f3', '#f44336']
          }]
        }
      }
      });

      // 测试趋势图
      const trendCtx = document.getElementById('trendChart').getContext('2d');
      new Chart(trendCtx, {
        type: 'line',
        data: {
          labels: ['周一', '周二', '周三', '周四', '周五'],
          datasets: [{
            label: '通过率',
            data: [95, 92, 88, 96, 94],
            borderColor: '#2196f3',
            tension: 0.4
          }]
        }
      }
      });
    </script>
  </div>
</body>
</html>
```

### 报告通知

```yaml
# 测试失败时发送通知
- name: 发送测试报告
  if: always()
  uses: actions/github-script@v6
  with:
    script: |
      const summary = `
      ## 测试结果

      | 类型 | 通过 | 失败 | 覆盖率 |
      |------|-------|--------|--------|
      | 单元测试 | 142 | 8 | 85% |
      | 集成测试 | 38 | 2 | 72% |
      | E2E 测试 | 8 | 2 | 45% |

      [查看详细报告](https://github.com/${{ github.repository }}/actions/runs/${{ github.run_id }})
      `;

      github.rest.issues.createComment({
        issue_number: context.issue.number,
        owner: context.repo.owner,
        repo: context.repo.repo,
        body: summary
      });
```

---

## 持续监控

### 测试环境管理

```yaml
# .github/workflows/nightly-tests.yml
name: 每日测试

on:
  schedule:
    - cron: '0 2 * * *'  # 每天凌晨 2 点
  workflow_dispatch:  # 手动触发

jobs:
  full-test-suite:
    runs-on: ubuntu-latest
    steps:
      - name: 运行完整测试套件
        run: |
          # 运行所有测试
          pytest tests/ --cov=app --cov-report=html

      - name: 上传报告
        uses: actions/upload-artifact@v3
        with:
          name: nightly-report-${{ github.run_number }}
          path: htmlcov

      - name: 存储到 S3
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_KEY }}
        run: |
          aws s3 sync htmlcov/ s3://castplay-test-reports/
```

### 测试结果历史

创建测试结果追踪系统：

```python
# scripts/test_tracker.py
from datetime import datetime
import json
from pathlib import Path

TEST_RESULTS_FILE = "data/test_results_history.json"

def save_test_results(results: dict) -> None:
    """保存测试结果到历史记录"""
    Path(TEST_RESULTS_FILE).parent.mkdir(parents=True, exist_ok=True)

    history = []
    if Path(TEST_RESULTS_FILE).exists():
        with open(TEST_RESULTS_FILE) as f:
            history = json.load(f)

    record = {
        "timestamp": datetime.now().isoformat(),
        "commit": results.get("commit"),
        "branch": results.get("branch"),
        "unit": results.get("unit"),
        "integration": results.get("integration"),
        "e2e": results.get("e2e"),
        "performance": results.get("performance"),
    }

    history.append(record)

    # 保留最近 100 条记录
    history = history[-100:]

    with open(TEST_RESULTS_FILE, "w") as f:
        json.dump(history, f, indent=2)

def get_test_trend(days: int = 7) -> dict:
    """获取最近 N 天的测试趋势"""
    with open(TEST_RESULTS_FILE) as f:
        history = json.load(f)

    recent = [r for r in history if r["timestamp"] >= (datetime.now() - timedelta(days=days)).isoformat()]

    return {
        "total_tests": len(recent),
        "avg_coverage": sum(r.get("coverage", 0) for r in recent) / len(recent),
        "pass_rate": sum(r.get("passed", 0) for r in recent) / sum(r.get("total", 1) for r in recent) * 100,
    }
```

### 测试环境隔离

```yaml
# 短命环境隔离
environments:
  test-pr:
    database: :memory:
    storage: /tmp/castplay-test

  test-main:
    database: postgresql://test:***@localhost:5432/castplay_test
    storage: /tmp/castplay-main
```

---

## 性能基准

### 性能指标

| 指标 | 目标值 | 告警阈值 |
|--------|---------|----------|
| API 响应时间 (P50) | < 100ms | > 200ms |
| API 响应时间 (P95) | < 300ms | > 500ms |
| API 响应时间 (P99) | < 500ms | > 1000ms |
| 数据库查询时间 | < 50ms | > 100ms |
| 并发用户数 (QPS) | > 1000 | < 500 |
| 内存使用 | < 2GB | > 3GB |
| CPU 使用率 | < 50% | > 80% |

### 性能回归检测

```python
# tests/performance/benchmark.py
import time
import statistics

class PerformanceBenchmark:
    """性能基准测试"""

    def __init__(self):
        self.baseline = self.load_baseline()

    def measure_api_response(self, endpoint: str, iterations: int = 100) -> dict:
        """测量 API 响应时间"""
        times = []
        for _ in range(iterations):
            start = time.time()
            # 执行请求
            response = requests.get(f"http://localhost:8000{endpoint}")
            times.append((time.time() - start) * 1000)  # 转换为毫秒

        return {
            "p50": statistics.quantiles(times, n=2)[0],  # 50分位
            "p95": statistics.quantiles(times, n=20)[0],  # 95分位
            "p99": statistics.quantiles(times, n=100)[0],  # 99分位
            "mean": statistics.mean(times),
            "max": max(times),
        }

    def check_regression(self, current: dict, threshold: float = 0.2) -> bool:
        """检查性能回归（允许阈值范围内浮动）"""
        baseline = self.baseline.get(current["endpoint"], {})
        return (
            current["p95"] > baseline.get("p95", 0) * (1 + threshold)
        )

    def update_baseline(self, results: dict) -> None:
        """更新基准值"""
        # 当所有测试通过且性能稳定时更新
        pass
```

---

## 安全测试

### 安全扫描清单

| 扫描类型 | 工具 | 频率 | 严重性级别 |
|----------|------|--------|------------|
| 代码静态分析 | Bandit | 每次 PR | High, Medium, Low |
| 依赖漏洞 | Snyk | 每天 | Critical, High, Medium |
| API 安全 | OWASP ZAP | 每周 | Critical, High |
| 容器扫描 | Trivy | 每次 Docker 构建 | Critical, High |

### 安全测试用例

```python
# tests/security/test_api_security.py
import pytest

class TestAPISecurity:
    """API 安全测试"""

    def test_sql_injection_protection(self, client):
        """测试 SQL 注入防护"""
        malicious_input = "' OR '1'='1"
        response = client.get(f"/api/devices?name={malicious_input}")
        assert response.status_code == 400  # 应该被拒绝

    def test_xss_prevention(self, client):
        """测试 XSS 防护"""
        xss_payload = "<script>alert('xss')</script>"
        response = client.post(
            "/api/playlists/",
            json={"name": xss_payload}
        )
        # 返回数据不应该包含未转义的脚本
        assert xss_payload not in response.text

    def test_rate_limiting(self, client):
        """测试速率限制"""
        for _ in range(100):  # 超过限制
            response = client.post("/api/auth/login", json={"username": "test", "password": "test"})
            if response.status_code == 429:
                return  # 成功检测到速率限制
        pytest.fail("Rate limiting not working")

    def test_auth_token_expiration(self, client, auth_headers):
        """测试 Token 过期"""
        # 模拟过期 Token
        expired_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
        response = client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {expired_token}"
        })
        assert response.status_code == 401

    def test_cors_headers(self, client):
        """测试 CORS 头"""
        response = client.options("/api/devices")
        assert response.headers.get("Access-Control-Allow-Origin") == "*"

    def test_sensitive_data_logging(self, client):
        """测试敏感数据不被记录"""
        # 访问不应该记录密码
        # 这个测试需要检查日志文件
        pass

    def test_file_upload_restrictions(self, client, auth_headers):
        """测试文件上传限制"""
        # 尝试上传恶意文件类型
        malicious_file = ("malicious.exe", b"fake exe content", "application/x-msdownload")
        response = client.post(
            "/api/media/upload",
            files={"file": malicious_file},
            headers=auth_headers
        )
        assert response.status_code == 400
```

---

## 测试数据管理

### 测试数据生成

```python
# tests/factories/test_data_factory.py
from faker import Faker
from datetime import datetime, timedelta
import random

fake = Faker('zh_CN')

class TestDataFactory:
    """测试数据工厂"""

    @staticmethod
    def create_user(**kwargs):
        """创建测试用户"""
        data = {
            "username": fake.user_name(),
            "email": fake.email(),
            "full_name": fake.name(),
            "password": fake.password(length=12),
        }
        data.update(kwargs)
        return data

    @staticmethod
    def create_device(**kwargs):
        """创建测试设备"""
        data = {
            "device_id": fake.uuid4(),
            "device_name": fake.word(),
            "timezone": random.choice(["Asia/Shanghai", "America/New_York", "Europe/London"]),
            "status": random.choice(["online", "offline"]),
            "last_online": fake.date_time_this_year(before_today=True, after_now=False).isoformat(),
        }
        data.update(kwargs)
        return data

    @staticmethod
    def create_playlist(**kwargs):
        """创建测试播放列表"""
        data = {
            "name": fake.sentence(nb_words=3),
            "description": fake.text(max_nb_chars=200),
        }
        data.update(kwargs)
        return data

    @staticmethod
    def create_media(**kwargs):
        """创建测试媒体"""
        data = {
            "file_name": fake.file_name(extension=random.choice(["jpg", "mp4", "pptx"])),
            "file_type": random.choice(["image", "video", "ppt"]),
            "file_size": random.randint(1024, 1024 * 1024 * 10),
            "status": "ready",
        }
        data.update(kwargs)
        return data

    @staticmethod
    def create_device_schedule(**kwargs):
        """创建测试定时配置"""
        data = {
            "power_on_time": fake.time(pattern="%H:%M"),
            "power_off_time": fake.time(pattern="%H:%M"),
            "is_enabled": True,
            "weekdays": sorted(random.sample(range(1, 8), random.randint(3, 7))),
        }
        data.update(kwargs)
        return data
```

### 测试数据清理

```python
# tests/conftest.py
import shutil
from pathlib import Path

@pytest.fixture(autouse=True)
def cleanup_test_data():
    """自动清理测试数据"""
    yield

    # 清理测试上传的文件
    test_upload_dir = Path("data/uploads/test_*")
    for item in test_upload_dir.glob("*"):
        if item.is_file():
            item.unlink()

    # 清理测试数据库
    if os.getenv("TESTING") == "true":
        reset_database()
```

---

## 故障测试

### 故障注入测试

```python
# tests/chaos/chaos_test.py
import pytest
import time
import signal
import subprocess

class ChaosTest:
    """故障测试"""

    def test_database_disconnect_during_request(self):
        """测试请求数据库断开"""
        # 模拟数据库断开
        process = subprocess.Popen(["docker", "stop", "castplay-db"])
        time.sleep(1)
        process = subprocess.Popen(["docker", "start", "castplay-db"])

        # API 应该优雅处理错误
        response = requests.get("http://localhost:8000/api/devices")
        assert response.status_code in [503, 504]

    def test_high_cpu_load(self):
        """测试高 CPU 负载"""
        # 启动 CPU 负载
        subprocess.Popen(["stress", "--cpu", "4", "--timeout", "30s"])

        # 系统应该仍然响应
        start = time.time()
        response = requests.get("http://localhost:8000/health")
        elapsed = (time.time() - start) * 1000

        assert elapsed < 5000  # 响应时间应该 < 5秒

    def test_memory_leak_detection(self):
        """测试内存泄漏"""
        import psutil
        import requests

        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        # 执行多个请求
        for _ in range(1000):
            requests.get("http://localhost:8000/api/devices")

        final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        # 内存增长应该 < 100MB
        memory_growth = final_memory - initial_memory
        assert memory_growth < 100
```

---

## 测试文档生成

### 自动化文档生成

```yaml
# .github/workflows/generate-docs.yml
name: 生成测试文档

on:
  schedule:
    - cron: '0 6 * * 1'  # 每周一早上 6 点
  workflow_dispatch:

jobs:
  generate-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: 生成测试覆盖率报告
        run: |
          pytest tests/ --cov=app --cov-report=html --cov-report=xml

      - name: 生成 API 文档
        run: |
          redocly bundle app/main.html -o docs/api-reference.html

      - name: 部署文档到 GitHub Pages
        uses: peaceiris/actions-publish-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs
```

---

## 实施步骤

### 第一阶段：基础建设（第 1-2 周）

- [ ] 配置 GitHub Actions
- [ ] 搭建测试基础设施
- [ ] 编写 50+ 个单元测试
- [ ] 配置代码覆盖率报告

### 第二阶段：完善测试（第 3-4 周）

- [ ] 编写 30+ 个集成测试
- [ ] 实现 10+ 个 E2E 测试
- [ ] 配置性能基准测试
- [ ] 集成安全扫描工具

### 第三阶段：自动化管道（第 5-6 周）

- [ ] 建立 CI/CD 完整管道
- [ ] 配置质量门禁
- [ ] 设置测试通知
- [ ] 配置测试环境

### 第四阶段：监控与优化（持续进行）

- [ ] 实施持续监控
- [ ] 定期回顾测试结果
- [ ] 优化测试执行速度
- [ ] 保持测试套件更新

---

## 关键指标 (KPIs)

| KPI | 目标 | 当前 | 状态 |
|-----|------|------|------|
| 测试覆盖率 | > 80% | 47% | ⚠️ |
| 单元测试数量 | > 150 | 24 | ⚠️ |
| 集成测试数量 | > 50 | 40 | ✅ |
| E2E 测试数量 | > 10 | 0 | ❌ |
| 测试执行时间 | < 15 分钟 | 2.5 分钟 | ✅ |
| CI 管道成功率 | > 95% | - | ⏳ |

---

## 工具与资源

### 推荐工具

```bash
# 安装所有测试工具
pip install pytest pytest-cov pytest-asyncio pytest-xdist
pip install black isort mypy pylint bandit safety
pip install locust

# 前端测试工具
npm install -D @playwright/test
npm install -D vitest @vitest/coverage-c8
```

### 有用资源

- [pytest 文档](https://docs.pytest.org/)
- [Playwright 文档](https://playwright.dev/)
- [Locust 文档](https://docs.locust.io/)
- [GitHub Actions 文档](https://docs.github.com/en/actions)

---

## 总结

本全自动化测试方案涵盖：

1. ✅ **多层测试** - 单元、集成、E2E、性能、安全
2. ✅ **CI/CD 管道** - GitHub Actions 自动化流程
3. ✅ **质量门禁** - 覆盖率、通过率、代码质量
4. ✅ **持续监控** - 每日测试、历史追踪、趋势分析
5. ✅ **快速反馈** - 分钟级测试反馈
6. ✅ **问题预防** - 静态分析、依赖扫描

实施此方案后，CastPlay 项目将具备企业级的自动化测试能力。
