# CastPlay All-in-One 开发者文档

## 目录
- [项目结构](#项目结构)
- [技术栈](#技术栈)
- [开发环境搭建](#开发环境搭建)
- [API 开发](#api-开发)
- [数据库操作](#数据库操作)
- [测试](#测试)
- [代码规范](#代码规范)

---

## 项目结构

```
castplay-allinone/
├── app/                      # 后端应用
│   ├── api/                 # API 路由
│   │   ├── auth.py         # 认证相关
│   │   ├── devices.py      # 设备管理
│   │   ├── media.py        # 媒体管理
│   │   ├── playlists.py    # 播放列表管理
│   │   └── player.py       # 播放端接口
│   ├── models/              # SQLAlchemy 数据模型
│   ├── schemas/             # Pydantic 数据验证模式
│   ├── services/            # 业务逻辑服务
│   ├── workers/             # 后台任务队列
│   ├── websocket/           # WebSocket 连接管理
│   ├── middleware/          # 中间件
│   ├── utils/               # 工具函数
│   ├── config.py            # 配置管理
│   ├── database.py          # 数据库连接
│   └── main.py              # FastAPI 应用入口
├── frontend/                # 前端应用
│   ├── src/
│   │   ├── api/           # API 客户端
│   │   ├── components/    # React 组件
│   │   ├── pages/         # 页面组件
│   │   ├── store/         # Zustand 状态管理
│   │   ├── types/         # TypeScript 类型定义
│   │   └── utils/         # 工具函数
│   ├── package.json
│   └── vite.config.ts
├── data/                   # 数据目录
│   ├── uploads/            # 上传的原始文件
│   ├── converted/          # 转换后的文件
│   └── thumbnails/         # 缩略图
├── tests/                  # 测试文件
├── scripts/                # 实用脚本
├── requirements.txt         # Python 依赖
├── Dockerfile              # Docker 镜像
├── docker-compose.yml      # Docker Compose 配置
└── README.md               # 项目说明
```

---

## 技术栈

### 后端
- **框架**: FastAPI 0.110.0
- **ASGI 服务器**: Uvicorn 0.27.1
- **ORM**: SQLAlchemy 2.0.25
- **数据库**: SQLite (生产环境可切换 PostgreSQL)
- **认证**: JWT (python-jose) + bcrypt
- **验证**: Pydantic 2.6.0
- **日志**: Loguru 0.7.2
- **后台任务**: threading.Queue (可切换 Celery)

### 前端
- **框架**: React 18.2.0
- **语言**: TypeScript 5.2.2
- **构建工具**: Vite 5.0.10
- **UI 库**: Ant Design 5.12.0
- **状态管理**: Zustand 5.0.11
- **HTTP 客户端**: Axios 1.6.5
- **WebSocket**: Socket.IO Client 4.6.1

---

## 开发环境搭建

### 1. 克隆仓库

```bash
git clone <repository-url>
cd castplay-allinone
```

### 2. 后端开发环境

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 安装开发依赖
pip install pytest pytest-cov pytest-asyncio black isort mypy

# 初始化数据库
python scripts/init_db.py

# 启动开发服务器
python scripts/run.py
```

### 3. 前端开发环境

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

---

## API 开发

### 创建新的 API 端点

1. 在 `app/api/` 下创建或编辑文件

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.example import ExampleCreate, ExampleResponse

router = APIRouter(prefix="/example", tags=["示例"])

@router.post("/", response_model=ExampleResponse)
def create_example(
    data: ExampleCreate,
    db: Session = Depends(get_db)
):
    """创建示例"""
    # 业务逻辑
    return result
```

2. 注册路由到主应用

```python
# app/main.py
from app.api.example import router as example_router

app.include_router(example_router)
```

### Pydantic Schema 定义

```python
# app/schemas/example.py
from pydantic import BaseModel, Field
from typing import Optional

class ExampleBase(BaseModel):
    name: str = Field(..., description="名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="描述")

class ExampleCreate(ExampleBase):
    pass

class ExampleUpdate(ExampleBase):
    pass

class ExampleResponse(ExampleBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2
```

### 依赖注入

```python
# 获取当前用户
from fastapi import Depends, HTTPException, status
from jose import JWTError
from app.utils.security import decode_access_token
from app.database import get_db

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """获取当前认证用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user = db.query(User).filter(User.id == payload.get("user_id")).first()
    if user is None:
        raise credentials_exception
    return user
```

---

## 数据库操作

### 创建新模型

```python
# app/models/example.py
from sqlalchemy import Column, Integer, String
from app.models.base import Base, TimestampMixin

class Example(Base, TimestampMixin):
    """示例模型"""
    __tablename__ = "examples"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
```

### 数据库查询

```python
from sqlalchemy.orm import Session
from app.models.user import User

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """按用户名获取用户"""
    return db.query(User).filter(User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    """获取用户列表"""
    return db.query(User).offset(skip).limit(limit).all()

def create_user(db: Session, user_data: dict) -> User:
    """创建用户"""
    db_user = User(**user_data)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user: User, update_data: dict) -> User:
    """更新用户"""
    for field, value in update_data.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, user: User) -> None:
    """删除用户"""
    db.delete(user)
    db.commit()
```

---

## 测试

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定文件
pytest tests/test_auth.py

# 运行特定测试
pytest tests/test_auth.py::TestAuthAPI::test_login

# 查看覆盖率
pytest --cov=app --cov-report=html
```

### 编写测试

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_example(client: TestClient):
    """测试示例"""
    response = client.get("/example")
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
```

### Fixtures

```python
# tests/conftest.py
@pytest.fixture
def test_db():
    """测试数据库"""
    # 创建测试数据库
    db = create_test_db()
    yield db
    # 清理
    db.drop_all()

@pytest.fixture
def client(test_db):
    """测试客户端"""
    def override_get_db():
        yield test_db
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

---

## 代码规范

### Python 代码格式化

```bash
# 使用 Black 格式化
black app/ tests/

# 使用 isort 排序导入
isort app/ tests/
```

### 类型检查

```bash
# 使用 mypy 检查类型
mypy app/
```

### 前端代码格式化

```bash
# 使用 ESLint
npm run lint

# 使用 Prettier
npm run format
```

---

## WebSocket 开发

### 连接管理

```python
from fastapi import WebSocket, WebSocketDisconnect
from app.websocket.handler import connection_manager

@app.websocket("/ws/{device_id}")
async def websocket_endpoint(websocket: WebSocket, device_id: int):
    await connection_manager.connect(device_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # 处理消息
    except WebSocketDisconnect:
        connection_manager.disconnect(device_id)
```

### 发送通知

```python
# 发送到特定设备
await connection_manager.send_to_device(device_id, message)

# 广播消息
await connection_manager.broadcast(message)
```

---

## 后台任务

### 注册任务处理器

```python
from app.workers.task_queue import task_manager

def my_task_handler(task_data: dict):
    """任务处理函数"""
    # 任务逻辑
    pass

# 注册处理器
task_manager.register_handler("my_task", my_task_handler)
```

### 提交任务

```python
task_data = {"param1": "value1"}
task_manager.submit_task("my_task", task_data)
```

---

## 故障排除

### 常见问题

1. **导入错误**
   ```bash
   # 确保虚拟环境已激活
   source venv/bin/activate
   ```

2. **数据库错误**
   ```bash
   # 重新初始化数据库
   rm data/castplay.db
   python scripts/init_db.py
   ```

3. **端口冲突**
   ```bash
   # 使用不同的端口
   export PORT=8001
   python scripts/run.py
   ```

---

## 贡献指南

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 提交信息规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

Type 类型:
- feat: 新功能
- fix: 修复 bug
- docs: 文档更新
- style: 代码格式
- refactor: 重构
- test: 测试相关
- chore: 构建/工具相关

---

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。
