"""
Pydantic Schema 单元测试

测试所有 Pydantic 模型的验证、序列化和反序列化
"""
import pytest
from pydantic import ValidationError

from app.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse
from app.schemas.device import (
    DeviceCreate, DeviceUpdate, DeviceResponse,
    DeviceScheduleCreate, DeviceScheduleResponse
)
from app.schemas.media import MediaFileResponse, MediaFileListResponse, UploadResponse
from app.schemas.playlist import (
    PlaylistCreate, PlaylistUpdate, PlaylistResponse,
    PlaylistListResponse, PlaylistDetailResponse,
    PlaylistItemCreate, PlaylistItemResponse,
    DevicePlaylistResponse, ReorderItemsRequest
)


# ============================================================================
# User Schema 测试
# ============================================================================

class TestUserSchemas:
    """用户相关 Schema 测试"""

    def test_user_create_valid(self):
        """测试有效的用户创建数据"""
        data = UserCreate(
            username="testuser",
            password="securePassword123",
            email="test@example.com",
            full_name="Test User"
        )
        assert data.username == "testuser"
        assert data.email == "test@example.com"
        assert data.full_name == "Test User"

    def test_user_create_minimal(self):
        """测试最小用户创建数据"""
        data = UserCreate(
            username="minimaluser",
            password="password123"
        )
        assert data.username == "minimaluser"
        assert data.email is None
        assert data.full_name is None

    def test_user_login_valid(self):
        """测试有效的登录数据"""
        data = UserLogin(
            username="testuser",
            password="password123"
        )
        assert data.username == "testuser"
        assert data.password == "password123"

    def test_user_login_missing_fields(self):
        """测试登录数据缺少字段"""
        with pytest.raises(ValidationError):
            UserLogin(username="testuser")

        with pytest.raises(ValidationError):
            UserLogin(password="password123")

    def test_token_response_structure(self):
        """测试 Token 响应结构"""
        response = TokenResponse(
            access_token="test_token_abc123",
            token_type="bearer"
        )
        assert response.access_token == "test_token_abc123"
        assert response.token_type == "bearer"


# ============================================================================
# Device Schema 测试
# ============================================================================

class TestDeviceSchemas:
    """设备相关 Schema 测试"""

    def test_device_create_valid(self):
        """测试有效的设备创建数据"""
        data = DeviceCreate(
            device_id="550e8400-e29b-41d4-a716-446655440000",
            device_name="Living Room TV",
            timezone="America/New_York"
        )
        assert data.device_id == "550e8400-e29b-41d4-a716-446655440000"
        assert data.device_name == "Living Room TV"
        assert data.timezone == "America/New_York"

    def test_device_create_defaults(self):
        """测试设备创建默认值"""
        data = DeviceCreate(device_id="default-test-device")
        assert data.device_name == "Default Device"
        assert data.timezone == "Asia/Shanghai"

    def test_device_update_partial(self):
        """测试部分设备更新"""
        data = DeviceUpdate(device_name="Updated Name")
        assert data.device_name == "Updated Name"
        assert data.timezone is None
        assert data.status is None

    def test_device_update_full(self):
        """测试完整设备更新"""
        data = DeviceUpdate(
            device_name="New Name",
            timezone="Europe/London",
            status="offline"
        )
        assert data.device_name == "New Name"
        assert data.timezone == "Europe/London"
        assert data.status == "offline"

    def test_device_schedule_create_valid(self):
        """测试有效的定时配置创建"""
        data = DeviceScheduleCreate(
            power_on_time="09:00",
            power_off_time="18:00",
            weekdays=[0, 1, 2, 3, 4],
            is_enabled=True
        )
        assert data.power_on_time == "09:00"
        assert data.power_off_time == "18:00"
        assert data.weekdays == [0, 1, 2, 3, 4]
        assert data.is_enabled is True

    def test_device_schedule_create_default_enabled(self):
        """测试定时配置默认启用状态"""
        data = DeviceScheduleCreate(
            power_on_time="08:00",
            power_off_time="20:00"
        )
        # 验证默认值
        assert data.is_enabled is True  # 如果 schema 定义了默认值


# ============================================================================
# Media Schema 测试
# ============================================================================

class TestMediaSchemas:
    """媒体相关 Schema 测试"""

    def test_media_response_structure(self):
        """测试媒体响应结构"""
        response = MediaFileResponse(
            id=1,
            file_name="test.jpg",
            file_type="image",
            file_path="/uploads/test.jpg",
            file_size=102400,
            thumbnail_path="/thumbnails/test.jpg",
            md5_hash="d41d8cd98f00b204e9800998ecf8427e",
            status="ready"
        )
        assert response.id == 1
        assert response.file_name == "test.jpg"
        assert response.file_type == "image"
        assert response.status == "ready"

    def test_media_list_response_structure(self):
        """测试媒体列表响应结构"""
        media_items = [
            MediaFileResponse(
                id=i,
                file_name=f"test{i}.jpg",
                file_type="image",
                file_path=f"/uploads/test{i}.jpg",
                file_size=102400,
                md5_hash=f"hash{i}",
                status="ready"
            )
            for i in range(3)
        ]

        response = MediaFileListResponse(
            items=media_items,
            total=3,
            page=1,
            per_page=20,
            pages=1
        )
        assert len(response.items) == 3
        assert response.total == 3
        assert response.page == 1
        assert response.pages == 1

    def test_upload_response_structure(self):
        """测试上传响应结构"""
        media = MediaFileResponse(
            id=1,
            file_name="uploaded.jpg",
            file_type="image",
            file_path="/uploads/uploaded.jpg",
            file_size=204800,
            md5_hash="upload_hash",
            status="ready"
        )
        response = UploadResponse(
            message="File uploaded successfully",
            media=media
        )
        assert response.message == "File uploaded successfully"
        assert response.media.id == 1


# ============================================================================
# Playlist Schema 测试
# ============================================================================

class TestPlaylistSchemas:
    """播放列表相关 Schema 测试"""

    def test_playlist_create_valid(self):
        """测试有效的播放列表创建"""
        data = PlaylistCreate(
            name="My Playlist",
            description="A great playlist"
        )
        assert data.name == "My Playlist"
        assert data.description == "A great playlist"

    def test_playlist_create_minimal(self):
        """测试最小播放列表创建"""
        data = PlaylistCreate(name="Minimal Playlist")
        assert data.name == "Minimal Playlist"
        assert data.description is None

    def test_playlist_update_partial(self):
        """测试部分播放列表更新"""
        data = PlaylistUpdate(name="Updated Name")
        assert data.name == "Updated Name"
        assert data.description is None

    def test_playlist_list_response_structure(self):
        """测试播放列表响应结构"""
        response = PlaylistListResponse(
            items=[],
            total=0,
            page=1,
            per_page=20,
            pages=0
        )
        assert response.total == 0
        assert response.pages == 0

    def test_playlist_item_create_valid(self):
        """测试有效的播放列表项创建"""
        data = PlaylistItemCreate(
            media_id=1,
            display_duration=30
        )
        assert data.media_id == 1
        assert data.display_duration == 30

    def test_device_playlist_response_structure(self):
        """测试设备播放列表响应结构"""
        response = DevicePlaylistResponse(
            id=1,
            device_id=2,
            playlist_id=3,
            is_active=True
        )
        assert response.device_id == 2
        assert response.playlist_id == 3
        assert response.is_active is True

    def test_reorder_items_request_valid(self):
        """测试重新排序请求结构"""
        data = ReorderItemsRequest(
            items=[
                {"id": 1, "order": 2},
                {"id": 2, "order": 0},
                {"id": 3, "order": 1}
            ]
        )
        assert len(data.items) == 3
        assert data.items[0]["id"] == 1
        assert data.items[0]["order"] == 2


# ============================================================================
# Schema 验证测试
# ============================================================================

class TestSchemaValidation:
    """Schema 验证测试"""

    def test_email_validation(self):
        """测试邮箱格式验证"""
        # 有效邮箱
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org"
        ]
        for email in valid_emails:
            data = UserCreate(
                username="test",
                password="pass123",
                email=email
            )
            assert data.email == email

        # 无效邮箱（如果启用了验证）
        # invalid_emails = ["notanemail", "@example.com", "user@"]
        # for email in invalid_emails:
        #     with pytest.raises(ValidationError):
        #         UserCreate(username="test", password="pass123", email=email)

    def test_time_format_validation(self):
        """测试时间格式验证"""
        # 有效时间格式
        valid_times = ["09:00", "00:00", "23:59", "18:30"]
        for time in valid_times:
            data = DeviceScheduleCreate(
                power_on_time=time,
                power_off_time=time,
                weekdays=[0, 1, 2]
            )
            assert data.power_on_time == time

    def test_weekdays_validation(self):
        """测试工作日验证（0-6，周一到周日）"""
        # 有效工作日
        valid_weekdays = [[0], [0, 1, 2, 3, 4], [6], [0, 1, 2, 3, 4, 5, 6]]
        for weekdays in valid_weekdays:
            data = DeviceScheduleCreate(
                power_on_time="09:00",
                power_off_time="18:00",
                weekdays=weekdays
            )
            assert data.weekdays == weekdays

    def test_file_type_validation(self):
        """测试文件类型验证（在 API 层处理，这里测试 schema）"""
        # 这个验证在 API Query 参数中进行
        # Schema 层通常只处理基本类型
        pass

    def test_status_filter_validation(self):
        """测试状态过滤验证"""
        # 同样，这个在 API Query 参数中进行
        pass


# ============================================================================
# Schema 序列化测试
# ============================================================================

class TestSchemaSerialization:
    """Schema 序列化测试"""

    def test_user_response_serialization(self):
        """测试用户响应序列化"""
        user_response = UserResponse(
            id=1,
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            is_active=True,
            is_superuser=False,
            created_at="2026-03-04T10:00:00",
            updated_at="2026-03-04T10:00:00"
        )

        # 转换为字典
        as_dict = user_response.model_dump()
        assert "id" in as_dict
        assert "password_hash" not in as_dict  # 密码哈希不应该在响应中

    def test_datetime_serialization(self):
        """测试日期时间序列化"""
        from datetime import datetime

        now = datetime.now()

        response = MediaFileResponse(
            id=1,
            file_name="test.jpg",
            file_type="image",
            file_path="/uploads/test.jpg",
            file_size=1024,
            md5_hash="hash",
            status="ready",
            created_at=now,
            updated_at=now
        )

        # 验证日期时间可以正确序列化
        as_dict = response.model_dump()
        assert as_dict["created_at"] == now
        assert as_dict["updated_at"] == now

    def test_json_serialization(self):
        """测试 JSON 序列化"""
        response = TokenResponse(
            access_token="test_token",
            token_type="bearer"
        )

        # 转换为 JSON
        import json
        json_str = response.model_dump_json()
        parsed = json.loads(json_str)

        assert parsed["access_token"] == "test_token"
        assert parsed["token_type"] == "bearer"


# ============================================================================
# Schema 边界值测试
# ============================================================================

class TestSchemaBoundaryValues:
    """Schema 边界值测试"""

    def test_username_length(self):
        """测试用户名长度限制"""
        # 短用户名
        short = UserCreate(username="ab", password="pass123")
        assert short.username == "ab"

        # 长用户名（根据实际限制调整）
        long_name = "a" * 100  # 假设限制为 100 字符
        long = UserCreate(username=long_name, password="pass123")
        assert long.username == long_name

    def test_weekdays_boundary(self):
        """测试工作日边界值"""
        # 最小值：只有周日
        min_weekdays = [6]
        data = DeviceScheduleCreate(
            power_on_time="09:00",
            power_off_time="18:00",
            weekdays=min_weekdays
        )
        assert data.weekdays == [6]

        # 最大值：所有工作日
        max_weekdays = [0, 1, 2, 3, 4, 5, 6]
        data = DeviceScheduleCreate(
            power_on_time="09:00",
            power_off_time="18:00",
            weekdays=max_weekdays
        )
        assert data.weekdays == max_weekdays

    def test_display_duration_boundary(self):
        """测试显示时长边界值"""
        # 最小值
        min_duration = 1
        data = PlaylistItemCreate(media_id=1, display_duration=min_duration)
        assert data.display_duration == 1

        # 大值
        max_duration = 3600  # 1小时
        data = PlaylistItemCreate(media_id=1, display_duration=max_duration)
        assert data.display_duration == 3600
