"""
Pytest Configuration and Fixtures
"""
from app.models import Device, DeviceSchedule, MediaFile, Playlist, PlaylistItem, DevicePlaylist
from app import create_app, db
import pytest
import os
import tempfile

# 设置测试环境标志
os.environ['TESTING'] = 'true'


@pytest.fixture(scope='session')
def app():
    """创建测试应用实例"""
    # 创建临时数据库文件
    db_fd, db_path = tempfile.mkstemp()

    # 创建测试应用
    app = create_app('testing')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['TESTING'] = True

    # 创建数据库表
    with app.app_context():
        db.create_all()

    yield app

    # 清理
    with app.app_context():
        db.drop_all()

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """创建 CLI 测试运行器"""
    return app.test_cli_runner()


@pytest.fixture(autouse=True)
def _db_session(app):
    """为每个测试创建新的数据库会话"""
    with app.app_context():
        # 清空所有表
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()

        yield db.session

        # 测试后回滚
        db.session.rollback()


@pytest.fixture
def sample_device(app):
    """创建示例设备"""
    with app.app_context():
        device = Device(
            device_id='test-device-001',
            device_name='Test Device',
            timezone='Asia/Shanghai',
            status='online'
        )
        db.session.add(device)
        db.session.commit()

        # 返回 device.id 而不是对象，避免 session 问题
        device_id = device.id

    # 重新查询以在新 session 中获取
    with app.app_context():
        return Device.query.get(device_id)


@pytest.fixture
def sample_media(app):
    """创建示例媒体文件"""
    with app.app_context():
        media = MediaFile(
            file_name='test_image.jpg',
            file_type='image',
            file_path='/storage/uploads/test_image.jpg',
            file_size=1024000,
            status='ready'
        )
        db.session.add(media)
        db.session.commit()

        media_id = media.id

    with app.app_context():
        return MediaFile.query.get(media_id)


@pytest.fixture
def sample_playlist(app, sample_media):
    """创建示例播放列表"""
    with app.app_context():
        playlist = Playlist(
            name='Test Playlist',
            description='A test playlist'
        )
        db.session.add(playlist)
        db.session.commit()

        # 添加播放项
        item = PlaylistItem(
            playlist_id=playlist.id,
            media_id=sample_media.id,
            display_order=1,
            display_duration=5
        )
        db.session.add(item)
        db.session.commit()

        playlist_id = playlist.id

    with app.app_context():
        return Playlist.query.get(playlist_id)


@pytest.fixture
def auth_headers():
    """返回认证头（预留 JWT）"""
    return {
        'Content-Type': 'application/json'
    }


@pytest.fixture(autouse=True)
def mock_socketio(monkeypatch):
    """Mock Flask-SocketIO 以避免 Redis 依赖"""
    from unittest.mock import Mock

    # Mock socketio emit 方法
    mock_socketio_instance = Mock()
    mock_socketio_instance.emit = Mock()

    # 替换 websocket handler 中的 socketio
    try:
        monkeypatch.setattr('app.websocket.handler.socketio',
                            mock_socketio_instance)
    except Exception:
        pass  # 如果模块未导入，跳过

    return mock_socketio_instance


@pytest.fixture(autouse=True)
def mock_celery(monkeypatch):
    """Mock Celery 任务"""
    from unittest.mock import Mock

    try:
        # Mock convert_ppt_to_video 任务
        mock_task = Mock()
        mock_task.delay = Mock(return_value=Mock(id='test-task-id'))
        monkeypatch.setattr(
            'app.tasks.convert.convert_ppt_to_video', mock_task)
    except Exception:
        pass  # 如果模块未导入，跳过

    return mock_task
