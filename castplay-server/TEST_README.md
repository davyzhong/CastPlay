# CastPlay Server 测试指南

## 📋 目录

- [测试概述](#测试概述)
- [快速开始](#快速开始)
- [测试结构](#测试结构)
- [运行测试](#运行测试)
- [编写测试](#编写测试)
- [覆盖率报告](#覆盖率报告)

---

## 测试概述

CastPlay Server 使用 **pytest** 作为测试框架，包含以下测试类型：

- ✅ **单元测试（Unit Tests）**：测试独立模块和函数
- ✅ **集成测试（Integration Tests）**：测试 API 端点和组件交互
- ✅ **服务测试（Service Tests）**：测试业务逻辑和服务层

### 测试覆盖范围

| 模块         | 测试文件               | 覆盖内容                  |
| ------------ | ---------------------- | ------------------------- |
| Models       | `test_models.py`       | 数据模型、序列化、关系    |
| Device API   | `test_device_api.py`   | 设备注册、心跳、定时配置  |
| Playlist API | `test_playlist_api.py` | 播放列表 CRUD、分配、排序 |
| Media API    | `test_media_api.py`    | 媒体上传、列表、下载      |
| Converter    | `test_converter.py`    | PPT 转换、缩略图生成      |

---

## 快速开始

### 1. 安装依赖

```bash
cd castplay-server
pip install -r requirements.txt
pip install -r requirements-test.txt
```

### 2. 运行所有测试

```bash
# 方式 1: 使用测试脚本
python run_tests.py

# 方式 2: 直接使用 pytest
pytest
```

### 3. 查看覆盖率报告

测试完成后，打开浏览器访问：

```bash
open htmlcov/index.html
```

---

## 测试结构

```
tests/
├── __init__.py           # 测试包初始化
├── conftest.py           # Pytest 配置和 Fixtures
├── unit/                 # 单元测试
│   ├── __init__.py
│   ├── test_models.py    # 模型测试
│   └── test_converter.py # 转换器测试
└── integration/          # 集成测试
    ├── __init__.py
    ├── test_device_api.py   # 设备 API 测试
    ├── test_playlist_api.py # 播放列表 API 测试
    └── test_media_api.py    # 媒体 API 测试
```

---

## 运行测试

### 运行所有测试

```bash
pytest
```

### 只运行单元测试

```bash
pytest tests/unit/
# 或使用标记
pytest -m unit
```

### 只运行集成测试

```bash
pytest tests/integration/
# 或使用标记
pytest -m integration
```

### 运行特定测试文件

```bash
pytest tests/unit/test_models.py
```

### 运行特定测试类

```bash
pytest tests/unit/test_models.py::TestDeviceModel
```

### 运行特定测试方法

```bash
pytest tests/unit/test_models.py::TestDeviceModel::test_create_device
```

### 显示详细输出

```bash
pytest -v
```

### 显示打印输出

```bash
pytest -s
```

### 失败时停止

```bash
pytest -x
```

### 跳过慢速测试

```bash
pytest -m "not slow"
```

---

## 编写测试

### 1. 单元测试示例

```python
"""
tests/unit/test_example.py
"""
import pytest
from app.models import Device

class TestDevice:
    """测试设备模型"""

    def test_create_device(self, app):
        """测试创建设备"""
        with app.app_context():
            device = Device(
                device_id='test-001',
                device_name='Test Device'
            )
            db.session.add(device)
            db.session.commit()

            assert device.id is not None
            assert device.device_id == 'test-001'
```

### 2. API 测试示例

```python
"""
tests/integration/test_example_api.py
"""
import json

class TestExampleAPI:
    """测试示例 API"""

    def test_get_list(self, client):
        """测试获取列表"""
        response = client.get('/api/example')

        assert response.status_code == 200
        json_data = response.get_json()
        assert 'items' in json_data

    def test_create_item(self, client):
        """测试创建项目"""
        data = {'name': 'Test Item'}

        response = client.post('/api/example',
                              data=json.dumps(data),
                              content_type='application/json')

        assert response.status_code == 201
```

### 3. 使用 Fixtures

```python
def test_with_device(self, client, sample_device):
    """使用设备 fixture"""
    response = client.get(f'/api/devices/{sample_device.id}')

    assert response.status_code == 200
```

### 4. Mock 外部依赖

```python
from unittest.mock import patch, Mock

@patch('subprocess.run')
def test_conversion(self, mock_run):
    """测试转换（mock subprocess）"""
    mock_run.return_value = Mock(returncode=0)

    converter = PPTConverter()
    result = converter.convert_to_pdf('test.pptx', '/tmp')

    assert result is not None
    mock_run.assert_called_once()
```

---

## 覆盖率报告

### 生成覆盖率报告

```bash
pytest --cov=app --cov-report=html
```

### 查看终端覆盖率

```bash
pytest --cov=app --cov-report=term-missing
```

### 覆盖率目标

| 模块       | 目标覆盖率 |
| ---------- | ---------- |
| Models     | > 90%      |
| API Routes | > 85%      |
| Services   | > 80%      |
| Overall    | > 80%      |

---

## 测试配置

### pytest.ini 配置

```ini
[pytest]
testpaths = tests
addopts = -v --cov=app --cov-report=html
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
```

### 环境变量

测试使用独立的 SQLite 数据库，配置在 `conftest.py` 中自动创建和清理。

---

## Fixtures 说明

### 可用的 Fixtures

| Fixture           | 作用           | 使用示例                     |
| ----------------- | -------------- | ---------------------------- |
| `app`             | Flask 应用实例 | `app.config['TESTING']`      |
| `client`          | 测试客户端     | `client.get('/api/devices')` |
| `sample_device`   | 示例设备       | `sample_device.id`           |
| `sample_media`    | 示例媒体       | `sample_media.file_name`     |
| `sample_playlist` | 示例播放列表   | `sample_playlist.name`       |

### 自定义 Fixture

```python
@pytest.fixture
def custom_fixture(app):
    """自定义 fixture"""
    with app.app_context():
        # 设置
        yield data
        # 清理
```

---

## 持续集成

### GitHub Actions 配置示例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt

      - name: Run tests
        run: pytest --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

---

## 常见问题

### Q: 测试数据库如何清理？

A: 每个测试后自动清理，使用 `_db_session` fixture 实现。

### Q: 如何跳过某个测试？

```python
@pytest.mark.skip(reason="暂时跳过")
def test_something():
    pass
```

### Q: 如何标记慢速测试？

```python
@pytest.mark.slow
def test_slow_operation():
    pass
```

运行时跳过：`pytest -m "not slow"`

---

## 测试最佳实践

1. ✅ **每个测试独立**：不依赖其他测试的执行顺序
2. ✅ **清晰的命名**：`test_<操作>_<预期结果>`
3. ✅ **单一职责**：每个测试只验证一个功能点
4. ✅ **使用 Fixtures**：复用测试数据和设置
5. ✅ **Mock 外部依赖**：避免依赖外部服务
6. ✅ **断言具体**：使用明确的断言消息
7. ✅ **测试边界条件**：包括异常情况

---

## 测试报告示例

运行测试后的输出：

```
================================ test session starts =================================
platform darwin -- Python 3.9.13, pytest-7.4.3, pluggy-1.3.0
cachedir: .pytest_cache
rootdir: /path/to/castplay-server
plugins: cov-4.1.0, flask-1.3.0
collected 87 items

tests/unit/test_models.py::TestDeviceModel::test_create_device PASSED        [  1%]
tests/unit/test_models.py::TestDeviceModel::test_device_to_dict PASSED       [  2%]
...
tests/integration/test_device_api.py::TestDeviceRegistration::test_register_new_device PASSED [ 85%]
...

---------- coverage: platform darwin, python 3.9.13-final-0 -----------
Name                              Stmts   Miss  Cover   Missing
---------------------------------------------------------------
app/__init__.py                      45      2    96%   78-79
app/models/device.py                 67      3    96%   45, 89-90
app/api/device.py                   142      8    94%   156-163, 201-208
app/services/converter.py           197     15    92%   ...
---------------------------------------------------------------
TOTAL                              1247     68    95%

================================= 87 passed in 12.45s =================================
```

---

## 联系方式

如有问题，请联系开发团队或提交 Issue。
