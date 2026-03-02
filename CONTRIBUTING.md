# CastPlay 开发规范

## 📋 目录

- [代码风格](#代码风格)
- [命名规范](#命名规范)
- [注释规范](#注释规范)
- [Git 工作流](#git-工作流)
- [测试规范](#测试规范)
- [PR 规范](#pr-规范)

---

## 代码风格

### Python (后端)

遵循 **PEP 8** 规范

**格式化工具**：

- **Black** - 代码格式化
- **isort** - import 排序
- **flake8** - 代码检查

**安装**：

```bash
pip install black isort flake8
```

**使用**：

```bash
# 格式化代码
black app/

# 排序 imports
isort app/

# 检查代码
flake8 app/
```

**配置示例** (`.flake8`):

```ini
[flake8]
max-line-length = 100
exclude = .git,__pycache__,migrations
ignore = E203,W503
```

---

### TypeScript/JavaScript (前端)

遵循 **Airbnb Style Guide**

**格式化工具**：

- **Prettier** - 代码格式化
- **ESLint** - 代码检查

**配置示例** (`.prettierrc`):

```json
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100
}
```

---

### Java (Android)

遵循 **Google Java Style Guide**

**格式化工具**：

- Android Studio 自带格式化
- **Checkstyle** - 代码检查

**配置**：

```
Settings → Editor → Code Style → Java
→ Scheme → Google Style
```

---

## 命名规范

### 文件和目录命名

#### Python

```
模块：lowercase_with_underscores.py
包：lowercase
类文件：按类名命名（snake_case）
```

#### TypeScript/JavaScript

```
组件：PascalCase.tsx
Hook：use + PascalCase.ts
工具：camelCase.ts
类型：PascalCase.types.ts
```

#### Java

```
类：PascalCase.java
接口：I + PascalCase.java
Activity：xxxActivity.java
Fragment：xxxFragment.java
```

### 变量命名

#### Python

```python
# 变量和函数：snake_case
user_name = "Alice"
def get_user_info():
    pass

# 类名：PascalCase
class UserService:
    pass

# 常量：UPPER_CASE
MAX_UPLOAD_SIZE = 500 * 1024 * 1024

# 私有变量：_leading_underscore
_internal_cache = {}
```

#### TypeScript/JavaScript

```typescript
// 变量和函数：camelCase
const userName = "Alice";
function getUserInfo() {}

// 类和接口：PascalCase
class UserService {}
interface IUser {}

// 常量：UPPER_CASE
const MAX_UPLOAD_SIZE = 500 * 1024 * 1024;

// 类型：PascalCase + Type 后缀
type UserType = {
  id: number;
  name: string;
};
```

#### Java

```java
// 变量和方法：camelCase
String userName = "Alice";
public void getUserInfo() {}

// 类和接口：PascalCase
public class UserService {}
public interface IUserService {}

// 常量：UPPER_CASE
public static final int MAX_UPLOAD_SIZE = 500 * 1024 * 1024;

// 包名：lowercase
package com.castplay.player;
```

---

## 注释规范

### Python Docstring

使用 **Google Style** Docstring

```python
def create_user(name: str, age: int) -> dict:
    """创建新用户

    Args:
        name: 用户名，不能为空
        age: 用户年龄，必须 >= 18

    Returns:
        包含用户信息的字典

    Raises:
        ValueError: 当 name 为空或 age < 18 时

    Example:
        >>> user = create_user("Alice", 25)
        >>> print(user['name'])
        Alice
    """
    if not name:
        raise ValueError("Name cannot be empty")
    if age < 18:
        raise ValueError("Age must be >= 18")

    return {'name': name, 'age': age}


class Device(db.Model):
    """设备模型

    Attributes:
        id: 主键 ID
        device_id: 设备唯一标识（UUID）
        device_name: 设备名称
        status: 设备状态（online/offline）

    Note:
        设备注册后默认状态为 offline，需要心跳维持在线
    """
    pass
```

---

### JSDoc

```typescript
/**
 * 获取用户信息
 *
 * @param {number} userId - 用户 ID
 * @returns {Promise<User>} 用户对象
 * @throws {Error} 当用户不存在时抛出错误
 *
 * @example
 * const user = await getUserInfo(123);
 * console.log(user.name);
 */
async function getUserInfo(userId: number): Promise<User> {
  // ...
}

/**
 * 设备信息接口
 *
 * @interface
 * @property {number} id - 设备 ID
 * @property {string} deviceName - 设备名称
 * @property {string} status - 设备状态
 */
interface Device {
  id: number;
  deviceName: string;
  status: "online" | "offline";
}
```

---

### Java Javadoc

```java
/**
 * 同步管理器
 *
 * <p>负责从服务器同步播放列表和下载媒体文件，支持 MD5 校验和断点续传</p>
 *
 * @author CastPlay Team
 * @version 1.0
 * @since 2026-01-29
 */
public class SyncManager {

    /**
     * 执行完整同步
     *
     * @param callback 同步完成后的回调接口
     * @throws IOException 当网络请求失败时
     *
     * @see SyncCallback
     */
    public void performFullSync(SyncCallback callback) throws IOException {
        // ...
    }
}
```

---

### 行内注释

**何时添加**：

- 复杂逻辑
- 非显而易见的代码
- 临时解决方案（TODO/FIXME）
- 性能优化说明

**示例**：

```python
# 使用二分查找提升性能（数据量 > 10000）
result = binary_search(sorted_list, target)

# TODO(username): 实现缓存机制以提升性能
data = fetch_from_database()

# FIXME: 当文件大于 500MB 时会导致内存溢出
process_large_file(file_path)

# NOTE: 这里必须使用同步 IO，因为 LibreOffice 不支持异步
output = subprocess.run(['soffice', '--convert-to', 'pdf', input_file])
```

---

## Git 工作流

### 分支策略

```
main            - 生产环境（受保护）
  ↑
develop         - 开发环境（受保护）
  ↑
feature/xxx     - 功能开发分支
bugfix/xxx      - Bug 修复分支
hotfix/xxx      - 紧急修复分支
```

### 分支命名

```
feature/user-login          # 功能：用户登录
feature/ppt-conversion      # 功能：PPT 转换
bugfix/websocket-reconnect  # 修复：WebSocket 重连
hotfix/security-patch       # 紧急：安全补丁
```

### 提交信息规范

遵循 **Conventional Commits** 规范

**格式**：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type 类型**：

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建/工具链相关
- `revert`: 回滚提交

**示例**：

```
feat(api): 添加设备批量导入接口

- 支持 CSV 和 Excel 格式
- 自动去重和校验
- 异步任务处理大文件

Closes #123
```

```
fix(android): 修复 WebSocket 断线重连失败

当网络切换时，WebSocket 无法自动重连。
修改重连逻辑，增加网络状态监听。

Fixes #456
```

```
docs: 更新 API 文档

添加新增接口的文档说明
```

### 工作流程

1. **创建分支**

```bash
git checkout develop
git pull origin develop
git checkout -b feature/my-feature
```

2. **开发和提交**

```bash
git add .
git commit -m "feat(scope): description"
```

3. **推送分支**

```bash
git push origin feature/my-feature
```

4. **创建 PR**

- 在 GitHub/GitLab 创建 Pull Request
- 目标分支：`develop`
- 填写 PR 模板

5. **Code Review**

- 至少 1 人 Review
- 通过 CI/CD 测试
- 解决所有评论

6. **合并**

```bash
# Squash Merge（推荐）
git merge --squash feature/my-feature
```

7. **删除分支**

```bash
git branch -d feature/my-feature
git push origin --delete feature/my-feature
```

---

## 测试规范

### 测试分类

1. **单元测试**：测试单个函数/方法
2. **集成测试**：测试多个模块交互
3. **端到端测试**：测试完整业务流程

### Python 测试

**框架**：pytest

**目录结构**：

```
tests/
├── unit/           # 单元测试
│   ├── test_models.py
│   └── test_services.py
├── integration/    # 集成测试
│   └── test_api.py
└── conftest.py     # pytest 配置
```

**示例**：

```python
# tests/unit/test_models.py
import pytest
from app.models import Device

def test_device_creation():
    """测试设备创建"""
    device = Device(
        device_id='test-123',
        device_name='Test Device'
    )
    assert device.device_id == 'test-123'
    assert device.device_name == 'Test Device'
    assert device.status == 'offline'

def test_device_to_dict():
    """测试设备序列化"""
    device = Device(device_id='test-123')
    data = device.to_dict()
    assert 'id' in data
    assert 'device_id' in data
    assert data['device_id'] == 'test-123'
```

**运行**：

```bash
# 运行所有测试
pytest

# 运行指定文件
pytest tests/unit/test_models.py

# 显示覆盖率
pytest --cov=app
```

---

### TypeScript 测试

**框架**：Vitest + React Testing Library

**示例**：

```typescript
// src/components/__tests__/DeviceList.test.tsx
import { render, screen } from "@testing-library/react";
import DeviceList from "../DeviceList";

describe("DeviceList", () => {
  it("renders device list", () => {
    render(<DeviceList />);
    expect(screen.getByText("设备管理")).toBeInTheDocument();
  });

  it("displays devices correctly", async () => {
    const devices = [
      { id: 1, deviceName: "Device 1", status: "online" },
      { id: 2, deviceName: "Device 2", status: "offline" },
    ];

    render(<DeviceList devices={devices} />);
    expect(screen.getByText("Device 1")).toBeInTheDocument();
    expect(screen.getByText("Device 2")).toBeInTheDocument();
  });
});
```

---

### Java 测试

**框架**：JUnit 4 + Mockito

**示例**：

```java
// SyncManagerTest.java
@RunWith(MockitoJUnitRunner.class)
public class SyncManagerTest {

    @Mock
    private ApiService apiService;

    @Mock
    private AppDatabase database;

    private SyncManager syncManager;

    @Before
    public void setUp() {
        syncManager = new SyncManager(context, "test-device-id");
    }

    @Test
    public void testPerformFullSync_Success() {
        // Given
        InitResponse response = createMockResponse();
        when(apiService.playerInit(any())).thenReturn(response);

        // When
        syncManager.performFullSync(callback);

        // Then
        verify(callback).onSyncSuccess(any());
    }
}
```

---

## PR 规范

### PR 模板

```markdown
## 描述

简要描述此 PR 的目的和改动内容

## 类型

- [ ] 新功能 (feat)
- [ ] Bug 修复 (fix)
- [ ] 文档 (docs)
- [ ] 重构 (refactor)
- [ ] 性能优化 (perf)
- [ ] 测试 (test)

## 改动内容

- 添加了 xxx 功能
- 修复了 xxx 问题
- 优化了 xxx 性能

## 测试

- [ ] 单元测试已通过
- [ ] 集成测试已通过
- [ ] 手动测试已完成

## 截图（如适用）

[添加截图]

## 相关 Issue

Closes #123
Fixes #456

## Checklist

- [ ] 代码符合项目规范
- [ ] 添加了必要注释
- [ ] 更新了相关文档
- [ ] 添加了测试用例
- [ ] 所有测试通过
- [ ] 无安全隐患
```

### Code Review 清单

**功能性**：

- [ ] 实现了所有需求
- [ ] 边界情况处理完善
- [ ] 错误处理正确

**代码质量**：

- [ ] 代码清晰易读
- [ ] 命名规范
- [ ] 无重复代码
- [ ] 适当的抽象

**测试**：

- [ ] 单元测试覆盖
- [ ] 测试用例充分
- [ ] 无测试失败

**文档**：

- [ ] 代码注释完整
- [ ] API 文档更新
- [ ] README 更新

**性能**：

- [ ] 无性能瓶颈
- [ ] 数据库查询优化
- [ ] 内存使用合理

**安全**：

- [ ] 无 SQL 注入
- [ ] 无 XSS 漏洞
- [ ] 敏感信息加密

---

## 开发环境配置

### VSCode 推荐插件

**Python**：

- Python
- Pylance
- Python Docstring Generator

**TypeScript/React**：

- ESLint
- Prettier
- ES7+ React/Redux/React-Native snippets

**Java/Android**：

- Java Extension Pack
- Android Studio

### EditorConfig

```ini
# .editorconfig
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.py]
indent_style = space
indent_size = 4

[*.{js,ts,tsx,json}]
indent_style = space
indent_size = 2

[*.java]
indent_style = space
indent_size = 4

[*.md]
trim_trailing_whitespace = false
```

---

## 发布流程

### 版本号管理

遵循 **Semantic Versioning 2.0.0**

格式：`MAJOR.MINOR.PATCH`

- **MAJOR**：不兼容的 API 变更
- **MINOR**：向下兼容的功能新增
- **PATCH**：向下兼容的 Bug 修复

### Release 流程

1. **创建 Release 分支**

```bash
git checkout -b release/v1.1.0 develop
```

2. **更新版本号**

```bash
# Python
echo "__version__ = '1.1.0'" > app/__version__.py

# Node.js
npm version 1.1.0

# Android
# 修改 build.gradle 中的 versionName 和 versionCode
```

3. **更新 CHANGELOG**

```markdown
# Changelog

## [1.1.0] - 2026-01-29

### Added

- 设备批量导入功能
- PPT 转换进度显示

### Fixed

- WebSocket 断线重连问题
- 文件上传大小限制

### Changed

- 优化数据库查询性能
```

4. **合并到 main**

```bash
git checkout main
git merge --no-ff release/v1.1.0
git tag -a v1.1.0 -m "Release version 1.1.0"
git push origin main --tags
```

5. **合并回 develop**

```bash
git checkout develop
git merge --no-ff release/v1.1.0
git push origin develop
```

---

**文档版本**：v1.0
**最后更新**：2026-01-29
**维护者**：CastPlay 开发团队
