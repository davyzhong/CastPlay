"""
pytest 配置文件和通用 fixtures
"""
import os
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# 设置测试环境变量（必须在导入 app 之前）
os.environ["TESTING"] = "true"
os.environ["DATABASE_PATH"] = ":memory:"
os.environ["RATE_LIMIT_ENABLED"] = "false"  # 测试环境禁用速率限制

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# ============================================================================
# 测试数据库引擎
# ============================================================================
# 导入所有模型，确保它们都被注册到 Base.metadata
from app.models import (
    Base,
    User,
    Device,
    DeviceSchedule,
    CachedMedia,
    MediaFile,
    Playlist,
    PlaylistItem,
    DevicePlaylist,
    AlertConfig,
    AlertHistory,
    DeviceNotificationLog,
    PlaylistDownloadTask,
    PlaylistCleanupSchedule,
    PlaylistSchedule,
)

# 创建内存数据库引擎
TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)

# 创建所有表
Base.metadata.create_all(bind=TEST_ENGINE)

# 创建会话工厂
TestSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=TEST_ENGINE
)

# 替换 app.database 中的引擎
import app.database as db_module
db_module.engine = TEST_ENGINE
db_module.SessionLocal = TestSessionLocal


# ============================================================================
# 导入应用和模型
# ============================================================================
from app.database import get_db
from app.models.user import User
from app.models.device import Device, DeviceSchedule
from app.models.media import MediaFile
from app.models.playlist import Playlist, PlaylistItem, DevicePlaylist
from app.utils.security import get_password_hash


# ============================================================================
# 数据库 fixtures
# ============================================================================

@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """为每个测试函数创建独立的数据库会话"""
    # 清理所有表数据
    connection = TEST_ENGINE.connect()
    transaction = connection.begin()

    # 清理所有表
    for table in reversed(Base.metadata.sorted_tables):
        connection.execute(table.delete())

    session = TestSessionLocal(bind=connection)

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        transaction.rollback()
        connection.close()


# ============================================================================
# FastAPI 测试客户端
# ============================================================================

@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """创建 FastAPI 测试客户端"""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    # 创建测试应用
    app = FastAPI(title="Test App")

    # CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 覆盖数据库依赖
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # 注册路由
    from app.api import auth, devices, media, playlists, player, schedules
    app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
    app.include_router(devices.router, prefix="/api/devices", tags=["设备"])
    app.include_router(media.router, prefix="/api/media", tags=["媒体"])
    app.include_router(playlists.router, prefix="/api/playlists", tags=["播放列表"])
    app.include_router(player.router, prefix="/api/player", tags=["播放端"])
    app.include_router(schedules.router, prefix="/api/schedules", tags=["调度"])

    # 健康检查
    @app.get("/health")
    def health():
        return {"status": "ok"}

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c

    app.dependency_overrides.clear()


# ============================================================================
# 认证 fixtures
# ============================================================================

@pytest.fixture(scope="function")
def test_user(db_session: Session) -> User:
    """创建测试用户"""
    user = User(
        username="testuser",
        password_hash=get_password_hash("testpass123"),
        email="test@example.com",
        full_name="Test User",
        is_active=True,
        is_superuser=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_admin(db_session: Session) -> User:
    """创建测试管理员"""
    admin = User(
        username="admin",
        password_hash=get_password_hash("admin123"),
        email="admin@example.com",
        full_name="Admin User",
        is_active=True,
        is_superuser=True
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture(scope="function")
def auth_headers(client: TestClient, test_user: User) -> dict:
    """获取认证头"""
    response = client.post(
        "/api/auth/login",
        json={"username": test_user.username, "password": "testpass123"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def admin_headers(client: TestClient, test_admin: User) -> dict:
    """获取管理员认证头"""
    response = client.post(
        "/api/auth/login",
        json={"username": test_admin.username, "password": "admin123"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# 设备 fixtures
# ============================================================================

@pytest.fixture(scope="function")
def test_device(db_session: Session) -> Device:
    """创建测试设备"""
    device = Device(
        device_id=str(uuid.uuid4()),
        device_name="Test Device",
        timezone="Asia/Shanghai",
        status="online"
    )
    db_session.add(device)
    db_session.commit()
    db_session.refresh(device)
    return device


@pytest.fixture(scope="function")
def multiple_test_devices(db_session: Session) -> list[Device]:
    """创建多个测试设备"""
    devices = []
    for i in range(3):
        device = Device(
            device_id=str(uuid.uuid4()),
            device_name=f"Test Device {i}",
            timezone="Asia/Shanghai",
            status="online" if i % 2 == 0 else "offline"
        )
        db_session.add(device)
        devices.append(device)
    db_session.commit()
    for device in devices:
        db_session.refresh(device)
    return devices


# ============================================================================
# 媒体 fixtures
# ============================================================================

@pytest.fixture(scope="function")
def test_media(db_session: Session) -> MediaFile:
    """创建测试媒体文件"""
    media = MediaFile(
        file_name="test_image.jpg",
        file_type="image",
        file_path="/tmp/test_image.jpg",
        file_size=102400,
        thumbnail_path="/tmp/thumb_test_image.jpg",
        md5_hash="d41d8cd98f00b204e9800998ecf8427e",
        status="ready"
    )
    db_session.add(media)
    db_session.commit()
    db_session.refresh(media)
    return media


@pytest.fixture(scope="function")
def multiple_test_media(db_session: Session) -> list[MediaFile]:
    """创建多个测试媒体文件"""
    media_files = []
    for i in range(3):
        media = MediaFile(
            file_name=f"test_image_{i}.jpg",
            file_type="image",
            file_path=f"/tmp/test_image_{i}.jpg",
            file_size=102400,
            md5_hash=f"hash{i}",
            status="ready"
        )
        db_session.add(media)
        media_files.append(media)
    db_session.commit()
    for media in media_files:
        db_session.refresh(media)
    return media_files


@pytest.fixture(scope="function")
def test_video_media(db_session: Session) -> MediaFile:
    """创建测试视频媒体文件"""
    media = MediaFile(
        file_name="test_video.mp4",
        file_type="video",
        file_path="/tmp/test_video.mp4",
        file_size=10485760,  # 10MB
        thumbnail_path="/tmp/thumb_test_video.jpg",
        md5_hash="video_hash_abc123",
        status="ready"
    )
    db_session.add(media)
    db_session.commit()
    db_session.refresh(media)
    return media


@pytest.fixture(scope="function")
def test_ppt_media(db_session: Session) -> MediaFile:
    """创建测试 PPT 媒体文件"""
    media = MediaFile(
        file_name="test_presentation.pptx",
        file_type="ppt",
        file_path="/tmp/test_presentation.pptx",
        file_size=2097152,  # 2MB
        thumbnail_path="/tmp/thumb_test_ppt.jpg",
        converted_path="/tmp/converted/test_presentation.mp4",
        md5_hash="ppt_hash_def456",
        status="ready"
    )
    db_session.add(media)
    db_session.commit()
    db_session.refresh(media)
    return media


# ============================================================================
# 播放列表 fixtures
# ============================================================================

@pytest.fixture(scope="function")
def test_playlist(db_session: Session) -> Playlist:
    """创建测试播放列表"""
    playlist = Playlist(
        name="Test Playlist",
        description="Test playlist"
    )
    db_session.add(playlist)
    db_session.commit()
    db_session.refresh(playlist)
    return playlist


@pytest.fixture(scope="function")
def test_playlist_with_items(
    db_session: Session,
    test_playlist: Playlist,
    multiple_test_media: list[MediaFile]
) -> tuple[Playlist, list[PlaylistItem]]:
    """创建带媒体项的测试播放列表"""
    items = []
    for i, media in enumerate(multiple_test_media):
        item = PlaylistItem(
            playlist_id=test_playlist.id,
            media_id=media.id,
            display_order=i,
            display_duration=10
        )
        db_session.add(item)
        items.append(item)
    db_session.commit()
    for item in items:
        db_session.refresh(item)
    db_session.refresh(test_playlist)
    return test_playlist, items


@pytest.fixture(scope="function")
def device_playlist_assignment(
    db_session: Session,
    test_device: Device,
    test_playlist: Playlist
) -> DevicePlaylist:
    """创建设备播放列表分配"""
    assignment = DevicePlaylist(
        device_id=test_device.id,
        playlist_id=test_playlist.id
    )
    db_session.add(assignment)
    db_session.commit()
    db_session.refresh(assignment)
    return assignment


# ============================================================================
# 辅助函数
# ============================================================================

def create_test_jwt_token(user_id: int, username: str) -> str:
    """创建测试用 JWT token"""
    from app.utils.security import create_access_token
    return create_access_token(data={"sub": str(user_id), "username": username})


# ============================================================================
# 兼容性别名 fixtures
# ============================================================================

@pytest.fixture(scope="function")
def test_db(db_session: Session) -> Session:
    """数据库会话别名，保持向后兼容"""
    return db_session


# ============================================================================
# 性能测试 fixtures
# ============================================================================

@pytest.fixture(scope="function")
def performance_threshold() -> dict:
    """性能测试阈值配置"""
    return {
        "api_response_time_ms": 200,      # API 响应时间阈值（毫秒）
        "success_rate": 0.95,             # 成功率阈值（95%）
        "max_concurrent_users": 100,       # 最大并发用户数
        "min_throughput": 10,              # 最小吞吐量（请求/秒）
        "max_error_rate": 0.05,            # 最大错误率（5%）
        "db_query_time_ms": 100,           # 数据库查询时间阈值
        "file_upload_time_ms": 5000,       # 文件上传时间阈值
    }


# ============================================================================
# Mock fixtures
# ============================================================================

@pytest.fixture(scope="function")
def mock_file_utils():
    """Mock 文件工具函数"""
    from unittest.mock import MagicMock, patch

    mocks = {}
    with patch('app.utils.file_utils.calculate_md5') as mock_md5, \
         patch('app.utils.file_utils.generate_thumbnail') as mock_thumb, \
         patch('app.utils.file_utils.get_unique_filename') as mock_unique:
        mock_md5.return_value = "mocked_md5_hash"
        mock_thumb.return_value = "/tmp/mock_thumbnail.jpg"
        mock_unique.return_value = "unique_filename.jpg"

        mocks['calculate_md5'] = mock_md5
        mocks['generate_thumbnail'] = mock_thumb
        mocks['get_unique_filename'] = mock_unique
        yield mocks


# ============================================================================
# 临时文件 fixtures
# ============================================================================

@pytest.fixture(scope="function")
def temp_test_image():
    """创建临时测试图片文件"""
    import struct
    import imghdr

    # 创建一个最小的有效 JPEG 文件
    # JPEG 文件头
    jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
    # JPEG 文件尾
    jpeg_footer = b'\xff\xd9'
    # 最小化图像数据
    jpeg_data = jpeg_header + b'\x00' * 100 + jpeg_footer

    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        f.write(jpeg_data)
        temp_path = f.name

    yield temp_path

    # 清理
    if os.path.exists(temp_path):
        os.remove(temp_path)


@pytest.fixture(scope="function")
def temp_test_video():
    """创建临时测试视频文件（空文件用于测试）"""
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
        # 写入最小的 MP4 头部（仅用于测试文件存在性）
        f.write(b'\x00' * 1024)
        temp_path = f.name

    yield temp_path

    # 清理
    if os.path.exists(temp_path):
        os.remove(temp_path)


@pytest.fixture(scope="function")
def temp_test_ppt():
    """创建临时测试 PPT 文件"""
    import zipfile

    with tempfile.NamedTemporaryFile(suffix='.pptx', delete=False) as f:
        # PPTX 是一个 ZIP 文件，创建最小的有效结构
        with zipfile.ZipFile(f, 'w') as zf:
            zf.writestr('[Content_Types].xml', '<?xml version="1.0"?><Types></Types>')
        temp_path = f.name

    yield temp_path

    # 清理
    if os.path.exists(temp_path):
        os.remove(temp_path)


# ============================================================================
# 过期 Token fixture
# ============================================================================

@pytest.fixture(scope="function")
def expired_token(test_user: User) -> str:
    """创建已过期的 JWT token（用于测试过期场景）"""
    from datetime import datetime, timedelta
    import jwt
    from app.config import settings

    # 创建一个已经过期的 token
    expire = datetime.utcnow() - timedelta(hours=1)  # 1小时前过期

    to_encode = {
        "sub": str(test_user.id),
        "username": test_user.username,
        "exp": expire,
        "iat": datetime.utcnow() - timedelta(hours=2)
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


# ============================================================================
# Pytest 配置
# ============================================================================

def pytest_configure(config):
    """Pytest 配置钩子"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "security: marks tests as security tests"
    )
