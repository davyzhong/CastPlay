"""
Pytest Configuration for Flask Tests

Flask 同步测试配置，提供 app、client、db 等核心 fixtures
每个测试函数执行后自动清理数据库，确保测试隔离
"""
import os
import sys
import uuid
import tempfile
from typing import Generator

import pytest

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def app():
    """
    创建 Flask 测试应用实例

    使用 testing 配置，SQLite 内存数据库
    """
    from app import create_app, db as _db

    # 创建临时数据库文件
    db_fd, db_path = tempfile.mkstemp(suffix='.db')

    # 创建测试应用
    test_app = create_app('testing')
    test_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
        'SERVER_NAME': 'localhost',
    })

    # 创建应用上下文并初始化数据库
    with test_app.app_context():
        _db.create_all()

    yield test_app

    # 清理
    with test_app.app_context():
        _db.drop_all()

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope="function")
def db(app):
    """
    提供数据库会话 fixture

    每个测试函数后自动清理所有表数据，确保测试隔离
    """
    from app import db as _db

    with app.app_context():
        yield _db
        # 测试结束后清理所有表数据
        for table in reversed(_db.metadata.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()


@pytest.fixture(scope="function")
def client(app, db):
    """
    创建 Flask 测试客户端

    依赖 db fixture 确保每次测试后数据被清理
    """
    return app.test_client()


@pytest.fixture(scope="function")
def runner(app):
    """
    创建 CLI 测试运行器
    """
    return app.test_cli_runner()


@pytest.fixture(scope="function")
def auth_headers(client, db):
    """
    获取认证 headers

    创建测试用户并返回带 token 的 headers
    """
    from app.models import User

    # 检查是否有 User 模型
    try:
        user = User(username='testuser', email='test@example.com')
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()

        # 登录获取 token
        response = client.post('/api/v1/auth/login', json={
            'username': 'testuser',
            'password': 'testpass123'
        })

        if response.status_code == 200:
            token = response.get_json().get('access_token')
            return {'Authorization': f'Bearer {token}'}
    except Exception:
        pass

    return {}


def _generate_unique_id() -> str:
    """生成唯一 ID 后缀"""
    return str(uuid.uuid4())[:8]


@pytest.fixture(scope="function")
def sample_device(app, db):
    """
    创建示例设备

    使用唯一 device_id 避免冲突
    """
    from app.models import Device

    unique_id = _generate_unique_id()
    device = Device(
        device_id=f'test-device-{unique_id}',
        device_name='Test Device',
        timezone='Asia/Shanghai',
        status='offline'
    )
    db.session.add(device)
    db.session.commit()
    db.session.refresh(device)
    return device


@pytest.fixture(scope="function")
def sample_media(app, db):
    """
    创建示例媒体文件（不带真实文件，仅数据库记录）

    使用绝对路径确保通过路径安全检查
    """
    from app.models import MediaFile

    unique_id = _generate_unique_id()
    upload_folder = app.config.get('UPLOAD_FOLDER')

    media = MediaFile(
        file_name=f'test_image_{unique_id}.jpg',
        file_type='image',
        file_path=f'{upload_folder}/test_image_{unique_id}.jpg',
        file_size=1024,
        status='ready'
    )
    db.session.add(media)
    db.session.commit()
    db.session.refresh(media)
    return media


@pytest.fixture(scope="function")
def sample_playlist(app, db):
    """
    创建示例播放列表
    """
    from app.models import Playlist

    unique_id = _generate_unique_id()
    playlist = Playlist(
        name=f'Test Playlist {unique_id}',
        description='A test playlist'
    )
    db.session.add(playlist)
    db.session.commit()
    db.session.refresh(playlist)
    return playlist


@pytest.fixture(scope="function")
def sample_device_with_playlist(app, db, sample_device, sample_playlist):
    """
    创建带播放列表的示例设备
    """
    from app.models import DevicePlaylist

    device_playlist = DevicePlaylist(
        device_id=sample_device.id,
        playlist_id=sample_playlist.id,
        is_active=True
    )
    db.session.add(device_playlist)
    db.session.commit()
    return sample_device, sample_playlist


@pytest.fixture(scope="function")
def sample_media_with_file(app, db):
    """
    创建带真实文件的媒体记录

    使用 app 配置的 UPLOAD_FOLDER 路径，确保通过路径安全检查
    """
    from app.models import MediaFile

    unique_id = _generate_unique_id()
    upload_folder = app.config.get('UPLOAD_FOLDER')
    os.makedirs(upload_folder, exist_ok=True)

    # 创建真实测试文件
    file_name = f'test_image_{unique_id}.jpg'
    file_path = os.path.join(upload_folder, file_name)

    # 写入一些测试数据（简单的二进制内容）
    with open(file_path, 'wb') as f:
        f.write(b'\xff\xd8\xff\xe0' + b'\x00' * 100)  # 简单的 JPEG 头

    media = MediaFile(
        file_name=file_name,
        file_type='image',
        file_path=file_path,
        file_size=os.path.getsize(file_path),
        status='ready'
    )
    db.session.add(media)
    db.session.commit()
    db.session.refresh(media)

    yield media

    # 清理文件
    if os.path.exists(file_path):
        os.remove(file_path)


@pytest.fixture(scope="function")
def sample_media_with_converted(app, db):
    """
    创建带转换文件的 PPT 媒体记录
    """
    from app.models import MediaFile

    unique_id = _generate_unique_id()
    upload_folder = app.config.get('UPLOAD_FOLDER')
    converted_folder = app.config.get('CONVERTED_FOLDER')
    os.makedirs(upload_folder, exist_ok=True)
    os.makedirs(converted_folder, exist_ok=True)

    # 创建原始 PPT 文件
    ppt_name = f'test_ppt_{unique_id}.pptx'
    ppt_path = os.path.join(upload_folder, ppt_name)
    with open(ppt_path, 'wb') as f:
        f.write(b'PK' + b'\x00' * 100)  # 简单的 PPTX 头

    # 创建转换后的视频文件
    video_name = f'converted_{unique_id}.mp4'
    video_path = os.path.join(converted_folder, video_name)
    with open(video_path, 'wb') as f:
        f.write(b'\x00\x00\x00\x1cftyp' + b'\x00' * 100)  # 简单的 MP4 头

    media = MediaFile(
        file_name=ppt_name,
        file_type='ppt',
        file_path=ppt_path,
        converted_path=video_path,
        file_size=os.path.getsize(ppt_path),
        status='ready'
    )
    db.session.add(media)
    db.session.commit()
    db.session.refresh(media)

    yield media

    # 清理文件
    for path in [ppt_path, video_path]:
        if os.path.exists(path):
            os.remove(path)


@pytest.fixture(scope="function")
def sample_media_with_thumbnail(app, db):
    """
    创建带缩略图的媒体记录
    """
    from app.models import MediaFile

    unique_id = _generate_unique_id()
    upload_folder = app.config.get('UPLOAD_FOLDER')
    thumbnail_folder = app.config.get('THUMBNAIL_FOLDER')
    os.makedirs(upload_folder, exist_ok=True)
    os.makedirs(thumbnail_folder, exist_ok=True)

    # 创建原始文件
    file_name = f'test_video_{unique_id}.mp4'
    file_path = os.path.join(upload_folder, file_name)
    with open(file_path, 'wb') as f:
        f.write(b'\x00\x00\x00\x1cftyp' + b'\x00' * 100)

    # 创建缩略图
    thumb_name = f'thumb_{unique_id}.jpg'
    thumb_path = os.path.join(thumbnail_folder, thumb_name)
    with open(thumb_path, 'wb') as f:
        f.write(b'\xff\xd8\xff\xe0' + b'\x00' * 100)

    media = MediaFile(
        file_name=file_name,
        file_type='video',
        file_path=file_path,
        thumbnail_path=thumb_path,
        file_size=os.path.getsize(file_path),
        status='ready'
    )
    db.session.add(media)
    db.session.commit()
    db.session.refresh(media)

    yield media

    # 清理文件
    for path in [file_path, thumb_path]:
        if os.path.exists(path):
            os.remove(path)


@pytest.fixture(scope="function")
def sample_playlist_with_item(app, db, sample_media_with_file):
    """
    创建带 PlaylistItem 的播放列表
    """
    from app.models import Playlist, PlaylistItem

    unique_id = _generate_unique_id()
    playlist = Playlist(
        name=f'Test Playlist {unique_id}',
        description='A test playlist with items'
    )
    db.session.add(playlist)
    db.session.commit()

    # 添加播放列表项
    item = PlaylistItem(
        playlist_id=playlist.id,
        media_id=sample_media_with_file.id,
        display_order=1,
        display_duration=10
    )
    db.session.add(item)
    db.session.commit()
    db.session.refresh(playlist)

    return playlist, sample_media_with_file, item


# ============================================
# pytest 配置钩子
# ============================================

def pytest_configure(config):
    """配置 pytest markers"""
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )


def pytest_collection_modifyitems(config, items):
    """自动添加 markers"""
    for item in items:
        # 集成测试目录下的测试自动标记
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
