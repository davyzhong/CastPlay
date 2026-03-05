"""
pytest 配置文件和通用 fixtures
"""
import os
import sys
import tempfile
import uuid
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient

# 设置测试环境变量（必须在导入 app 之前）
os.environ["TESTING"] = "true"
os.environ["DATABASE_PATH"] = ":memory:"

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# ============================================================================
# 测试数据库引擎
# ============================================================================
from app.models import Base

# 创建内存数据库引擎
TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)

# 为每个连接创建新表（确保隔离）
@event.listens_for(TEST_ENGINE, "connect")
def receive_connect(dbapi_connection, connection_record):
    """为每个新连接创建所有表"""
    Base.metadata.create_all(TEST_ENGINE)


# 替换 app.database 中的引擎
import app.database as db_module
db_module.engine = TEST_ENGINE
db_module.SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=TEST_ENGINE
)


# ============================================================================
# 导入应用和模型
# ============================================================================
from app.database import get_db
from app.models.user import User
from app.models.device import Device
from app.models.media import MediaFile
from app.models.playlist import Playlist, PlaylistItem, DevicePlaylist
from app.utils.security import get_password_hash


# ============================================================================
# 数据库 fixtures
# ============================================================================

@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """
    为每个测试函数创建独立的数据库会话
    使用事务回滚确保测试隔离
    """
    # 创建连接和事务
    connection = TEST_ENGINE.connect()
    transaction = connection.begin()

    # 创建会话
    session = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=connection
    )()

    try:
        yield session
    finally:
        # 回滚事务，清理所有更改
        session.close()
        transaction.rollback()
        connection.close()


# ============================================================================
# FastAPI 测试客户端
# ============================================================================

@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    创建 FastAPI 测试客户端
    使用测试数据库会话
    """
    from app.main import app as main_app

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    main_app.dependency_overrides[get_db] = override_get_db

    with TestClient(main_app, raise_server_exceptions=True) as test_client:
        yield test_client

    main_app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def async_client(db_session: Session) -> AsyncGenerator[AsyncClient, None]:
    """
    创建异步 HTTP 客户端
    """
    from app.main import app as main_app

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    main_app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=main_app, base_url="http://test") as ac:
        yield ac

    main_app.dependency_overrides.clear()


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
    """创建测试管理员用户"""
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
    """获取测试用户的认证头"""
    response = client.post(
        "/api/auth/login",
        json={"username": test_user.username, "password": "testpass123"}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def admin_headers(client: TestClient, test_admin: User) -> dict:
    """获取管理员的认证头"""
    response = client.post(
        "/api/auth/login",
        json={"username": test_admin.username, "password": "admin123"}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
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
            device_name=f"Test Device {i+1}",
            timezone="Asia/Shanghai",
            status="online"
        )
        db_session.add(device)
        devices.append(device)
    db_session.commit()
    for device in devices:
        db_session.refresh(device)
    return devices


# ============================================================================
# 媒体文件 fixtures
# ============================================================================

@pytest.fixture(scope="function")
def test_media(db_session: Session) -> MediaFile:
    """创建测试媒体文件记录"""
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
def test_video_media(db_session: Session) -> MediaFile:
    """创建测试视频媒体文件记录"""
    media = MediaFile(
        file_name="test_video.mp4",
        file_type="video",
        file_path="/tmp/test_video.mp4",
        file_size=10485760,
        thumbnail_path="/tmp/thumb_test_video.jpg",
        md5_hash="5d41402abc4b2a76b9719d911017c592",
        status="ready"
    )
    db_session.add(media)
    db_session.commit()
    db_session.refresh(media)
    return media


@pytest.fixture(scope="function")
def test_ppt_media(db_session: Session) -> MediaFile:
    """创建测试 PPT 媒体文件记录"""
    media = MediaFile(
        file_name="test_presentation.pptx",
        file_type="ppt",
        file_path="/tmp/test_presentation.pptx",
        file_size=5242880,
        thumbnail_path="/tmp/thumb_test_ppt.jpg",
        converted_path="/tmp/test_presentation.mp4",
        md5_hash="7d793037a0760186574b0282f2f435e7",
        status="ready"
    )
    db_session.add(media)
    db_session.commit()
    db_session.refresh(media)
    return media


@pytest.fixture(scope="function")
def multiple_test_media(db_session: Session) -> list[MediaFile]:
    """创建多个测试媒体文件"""
    media_list = []
    types = ["image", "video", "ppt"]
    for i in range(5):
        file_type = types[i % len(types)]
        ext = 'jpg' if file_type == 'image' else 'mp4' if file_type == 'video' else 'pptx'
        media = MediaFile(
            file_name=f"test_{file_type}_{i}.{ext}",
            file_type=file_type,
            file_path=f"/tmp/test_{file_type}_{i}.{ext}",
            file_size=102400 * (i + 1),
            thumbnail_path=f"/tmp/thumb_test_{file_type}_{i}.jpg" if file_type != "ppt" else None,
            md5_hash=f"hash_{i}",
            status="ready"
        )
        db_session.add(media)
        media_list.append(media)
    db_session.commit()
    for media in media_list:
        db_session.refresh(media)
    return media_list


# ============================================================================
# 播放列表 fixtures
# ============================================================================

@pytest.fixture(scope="function")
def test_playlist(db_session: Session) -> Playlist:
    """创建测试播放列表"""
    playlist = Playlist(
        name="Test Playlist",
        description="A test playlist for testing purposes"
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
) -> Playlist:
    """创建包含媒体项的测试播放列表"""
    for i, media in enumerate(multiple_test_media):
        item = PlaylistItem(
            playlist_id=test_playlist.id,
            media_id=media.id,
            display_order=i,
            display_duration=10
        )
        db_session.add(item)
    db_session.commit()
    return test_playlist


@pytest.fixture(scope="function")
def device_playlist_assignment(
    db_session: Session,
    test_device: Device,
    test_playlist: Playlist
) -> DevicePlaylist:
    """创建设备播放列表关联"""
    assignment = DevicePlaylist(
        device_id=test_device.id,
        playlist_id=test_playlist.id,
        is_active=1
    )
    db_session.add(assignment)
    db_session.commit()
    db_session.refresh(assignment)
    return assignment


# ============================================================================
# 文件系统 fixtures
# ============================================================================

@pytest.fixture(scope="function")
def temp_upload_dir() -> Generator[Path, None, None]:
    """创建临时上传目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        upload_dir = Path(tmpdir) / "uploads"
        upload_dir.mkdir(parents=True)
        yield upload_dir


@pytest.fixture(scope="function")
def temp_test_image(temp_upload_dir: Path) -> Path:
    """创建临时测试图片文件"""
    from PIL import Image

    image_path = temp_upload_dir / "test_image.jpg"
    img = Image.new("RGB", (100, 100), color="red")
    img.save(image_path)
    return image_path


@pytest.fixture(scope="function")
def temp_test_video(temp_upload_dir: Path) -> Path:
    """创建临时测试视频文件"""
    video_path = temp_upload_dir / "test_video.mp4"
    # 创建一个最小化的 MP4 文件头
    with open(video_path, "wb") as f:
        f.write(b"ftypmp42\x00\x00\x00\x00mp42isom")
        f.write(b"\x00" * 1000)
    return video_path


# ============================================================================
# Mock fixtures
# ============================================================================

@pytest.fixture(scope="function")
def mock_file_utils():
    """Mock 文件工具函数"""
    with patch("app.api.media.generate_thumbnail") as mock_thumb:
        mock_thumb.return_value = "/tmp/thumb.jpg"
        yield mock_thumb


@pytest.fixture(scope="function")
def mock_convert_ppt():
    """Mock PPT 转换服务"""
    with patch("app.services.converter.convert_ppt_to_video") as mock_convert:
        mock_convert.return_value = "/tmp/converted.mp4"
        yield mock_convert


# ============================================================================
# 性能测试 fixtures
# ============================================================================

@pytest.fixture(scope="function")
def performance_threshold():
    """性能测试阈值配置"""
    return {
        "api_response_time_ms": 500,
        "concurrent_requests": 10,
        "success_rate": 0.95
    }


# ============================================================================
# 辅助函数
# ============================================================================

def create_test_jwt_token(user_id: int, username: str) -> str:
    """创建测试用 JWT token"""
    from app.utils.security import create_access_token
    return create_access_token(data={"sub": str(user_id), "username": username})


def get_test_auth_headers(client: TestClient, username: str, password: str) -> dict:
    """辅助函数：获取认证头"""
    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": password}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
