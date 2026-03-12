# CastPlay All-in-One 测试文档

## 概述

本项目使用 `pytest` 作为测试框架，提供完整的单元测试、集成测试、端到端测试和性能测试。

## 测试结构

```
tests/
├── conftest.py                  # pytest 配置和全局 fixtures
├── pytest.ini                   # pytest 配置文件
├── run_tests.py                 # 测试运行脚本
├── unit/                        # 单元测试
│   ├── test_models.py          # 数据模型测试
│   ├── test_schemas.py         # Pydantic Schema 测试
│   ├── test_utils.py           # 工具函数测试
│   └── test_security.py        # 安全工具测试
├── integration/                # 集成测试
│   ├── test_auth_api.py        # 认证 API 测试
│   ├── test_devices_api.py     # 设备 API 测试
│   ├── test_media_api.py       # 媒体 API 测试
│   ├── test_playlists_api.py    # 播放列表 API 测试
│   └── test_player_api.py      # 播放端 API 测试
├── e2e/                        # 端到端测试
│   ├── test_media_flow.py      # 媒体完整流程测试
│   ├── test_device_flow.py     # 设备完整流程测试
│   └── test_playlist_flow.py   # 播放列表完整流程测试
├── performance/                # 性能测试
│   ├── test_api_performance.py # API 性能测试
│   └── test_concurrent.py     # 并发测试
└── fixtures/                   # 测试数据 fixtures
    └── media_fixtures.py      # 媒体文件生成器
```

## 快速开始

### 安装测试依赖

```bash
cd castplay-allinone
pip install -r requirements.txt
```

### 运行所有测试

```bash
# 使用脚本
python tests/run_tests.py all

# 或直接使用 pytest
pytest tests/
```

### 运行特定类型的测试

```bash
# 单元测试
python tests/run_tests.py unit

# 集成测试
python tests/run_tests.py integration

# 端到端测试
python tests/run_tests.py e2e

# 性能测试
python tests/run_tests.py performance
```

### 运行特定测试文件

```bash
# 使用脚本
python tests/run_tests.py tests/unit/test_models.py

# 或直接使用 pytest
pytest tests/unit/test_models.py -v
```

### 运行特定测试用例

```bash
# 运行特定的测试函数
pytest tests/unit/test_models.py::TestUserModel::test_user_creation -v

# 运行特定类的所有测试
pytest tests/unit/test_models.py::TestUserModel -v
```

## 测试命令

### 基础命令

| 命令 | 说明 |
|------|------|
| `python tests/run_tests.py all` | 运行所有测试 |
| `python tests/run_tests.py unit` | 运行单元测试 |
| `python tests/run_tests.py integration` | 运行集成测试 |
| `python tests/run_tests.py e2e` | 运行端到端测试 |
| `python tests/run_tests.py performance` | 运行性能测试 |
| `python tests/run_tests.py slow` | 运行慢速测试 |
| `python tests/run_tests.py fast` | 只运行快速测试 |

### 高级命令

| 命令 | 说明 |
|------|------|
| `python tests/run_tests.py coverage` | 运行测试并生成覆盖率报告 |
| `python tests/run_tests.py parallel -w 8` | 使用 8 个线程并行运行 |
| `python tests/run_tests.py all -v` | 显示详细输出 |

### pytest 直接命令

```bash
# 运行所有测试
pytest tests/

# 显示详细输出
pytest tests/ -v

# 显示本地变量
pytest tests/ --showlocals

# 生成覆盖率报告
pytest tests/ --cov=app --cov-report=html

# 并行运行
pytest tests/ -n auto

# 运行带特定标记的测试
pytest tests/ -m unit
pytest tests/ -m "not slow"

# 停止在第一个失败
pytest tests/ -x

# 在 N 个失败后停止
pytest tests/ --maxfail=3
```

## 测试标记

| 标记 | 说明 |
|------|------|
| `@pytest.mark.unit` | 单元测试 |
| `@pytest.mark.integration` | 集成测试 |
| `@pytest.mark.e2e` | 端到端测试 |
| `@pytest.mark.performance` | 性能测试 |
| `@pytest.mark.slow` | 慢速测试 |
| `@pytest.mark.api` | API 测试 |
| `@pytest.mark.auth` | 认证相关测试 |
| `@pytest.mark.device` | 设备相关测试 |
| `@pytest.mark.media` | 媒体相关测试 |
| `@pytest.mark.playlist` | 播放列表相关测试 |
| `@pytest.mark.player` | 播放端相关测试 |

## Fixtures

### 全局 Fixtures (conftest.py)

| Fixture | 说明 |
|---------|------|
| `test_db` | 测试数据库会话（每个测试独立） |
| `client` | FastAPI 测试客户端 |
| `async_client` | 异步 HTTP 客户端 |
| `test_user` | 测试普通用户 |
| `test_admin` | 测试管理员用户 |
| `auth_headers` | 普通用户认证头 |
| `admin_headers` | 管理员认证头 |
| `test_device` | 测试设备 |
| `multiple_test_devices` | 多个测试设备 |
| `test_media` | 测试媒体文件 |
| `test_video_media` | 测试视频媒体 |
| `test_ppt_media` | 测试 PPT 媒体 |
| `multiple_test_media` | 多个测试媒体 |
| `test_playlist` | 测试播放列表 |
| `test_playlist_with_items` | 包含媒体的播放列表 |
| `device_playlist_assignment` | 设备播放列表关联 |

## 代码覆盖率

### 生成覆盖率报告

```bash
python tests/run_tests.py coverage
```

报告将生成在 `htmlcov/` 目录中。

### 在浏览器中查看

```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### 覆盖率目标

- 总体覆盖率：≥ 80%
- 核心模块覆盖率：≥ 90%

## CI/CD 集成

### GitHub Actions 示例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          cd castplay-allinone
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd castplay-allinone
          python tests/run_tests.py all
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## 调试测试

### 在测试中设置断点

```python
def test_example(test_db):
    # 设置断点，需要 pytest -s 或使用 pdb
    import pdb; pdb.set_trace()
    # 或者使用 ipdb
    import ipdb; ipdb.set_trace()
```

### 运行测试并进入调试器

```bash
# 使用 pdb
pytest tests/ --pdb

# 使用 ipdb
pytest tests/ --pdb -p ipdb

# 在第一次失败时停止并进入调试器
pytest tests/ -x --pdb
```

### 打印输出

```bash
# 允许打印
pytest tests/ -s

# 捕获打印但仍然显示
pytest tests/ --capture=no
```

## 性能基准

### 性能目标

| 指标 | 目标值 |
|------|--------|
| API 响应时间 | < 500ms |
| 并发成功率 | ≥ 95% |
| 数据库查询时间 | < 100ms |
| 内存泄漏测试 | 对象增长 < 10,000 |

## 故障排除

### 测试失败

1. **数据库锁定错误**：确保每个测试使用独立的数据库会话
2. **认证失败**：检查 token 是否有效且未过期
3. **文件不存在**：使用 mock 文件或创建临时文件

### 覆盖率不足

1. 运行未覆盖的代码路径
2. 检查是否遗漏了测试场景
3. 确保所有分支都被测试

### 性能测试失败

1. 确保在性能测试前运行数据库迁移
2. 检查是否有资源泄漏
3. 考虑调整性能阈值

## 最佳实践

1. **测试命名**：使用描述性的测试名称
2. **AAA 模式**：Arrange（准备）、Act（执行）、Assert（断言）
3. **独立性**：每个测试应该独立运行
4. **可读性**：测试应该像文档一样易读
5. **单一职责**：每个测试只测试一个功能
6. **使用 fixtures**：复用测试设置代码
7. **避免硬编码**：使用参数化测试
8. **清理资源**：使用 teardown 清理测试数据

## 添加新测试

1. 确定测试类型（单元/集成/E2E/性能）
2. 选择合适的文件或创建新文件
3. 使用现有的 fixtures
4. 遵循测试命名约定
5. 添加适当的标记
6. 运行测试验证

## 参考资源

- [pytest 文档](https://docs.pytest.org/)
- [FastAPI 测试文档](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy 测试文档](https://docs.sqlalchemy.org/en/14/orm/session_basics.html#session-faq-external-transaction)
