"""
播放列表批量添加功能单元测试

测试批量添加 API 和 Schema
"""
import pytest
from pydantic import ValidationError


class TestPlaylistItemBatchCreate:
    """测试批量添加 Schema"""

    def test_batch_create_valid(self):
        """测试有效的批量添加请求"""
        from app.schemas.playlist import PlaylistItemBatchCreate

        batch = PlaylistItemBatchCreate(
            media_ids=[1, 2, 3],
            display_duration=10
        )
        assert batch.media_ids == [1, 2, 3]
        assert batch.display_duration == 10

    def test_batch_create_default_duration(self):
        """测试默认显示时长"""
        from app.schemas.playlist import PlaylistItemBatchCreate

        batch = PlaylistItemBatchCreate(media_ids=[1, 2])
        assert batch.display_duration == 5  # 默认值

    def test_batch_create_single_media(self):
        """测试单个媒体"""
        from app.schemas.playlist import PlaylistItemBatchCreate

        batch = PlaylistItemBatchCreate(media_ids=[1])
        assert len(batch.media_ids) == 1

    def test_batch_create_max_media_count(self):
        """测试最大媒体数量"""
        from app.schemas.playlist import PlaylistItemBatchCreate

        # 50 个媒体是最大值
        batch = PlaylistItemBatchCreate(media_ids=list(range(1, 51)))
        assert len(batch.media_ids) == 50

    def test_batch_create_exceed_max_media_count(self):
        """测试超过最大媒体数量"""
        from app.schemas.playlist import PlaylistItemBatchCreate

        with pytest.raises(ValidationError):
            PlaylistItemBatchCreate(media_ids=list(range(1, 52)))  # 51 个

    def test_batch_create_empty_media_ids(self):
        """测试空媒体列表"""
        from app.schemas.playlist import PlaylistItemBatchCreate

        with pytest.raises(ValidationError):
            PlaylistItemBatchCreate(media_ids=[])

    def test_batch_create_display_duration_min(self):
        """测试最小显示时长"""
        from app.schemas.playlist import PlaylistItemBatchCreate

        batch = PlaylistItemBatchCreate(
            media_ids=[1],
            display_duration=1
        )
        assert batch.display_duration == 1

    def test_batch_create_display_duration_max(self):
        """测试最大显示时长"""
        from app.schemas.playlist import PlaylistItemBatchCreate

        batch = PlaylistItemBatchCreate(
            media_ids=[1],
            display_duration=3600
        )
        assert batch.display_duration == 3600

    def test_batch_create_display_duration_too_small(self):
        """测试显示时长太小"""
        from app.schemas.playlist import PlaylistItemBatchCreate

        with pytest.raises(ValidationError):
            PlaylistItemBatchCreate(
                media_ids=[1],
                display_duration=0
            )

    def test_batch_create_display_duration_too_large(self):
        """测试显示时长太大"""
        from app.schemas.playlist import PlaylistItemBatchCreate

        with pytest.raises(ValidationError):
            PlaylistItemBatchCreate(
                media_ids=[1],
                display_duration=3601
            )


class TestPlaylistItemBatchResponse:
    """测试批量添加响应 Schema"""

    def test_batch_response_valid(self):
        """测试有效的批量响应"""
        from app.schemas.playlist import (
            PlaylistItemBatchResponse,
            PlaylistItemResponse
        )
        from datetime import datetime

        items = [
            PlaylistItemResponse(
                id=1,
                media_id=1,
                file_name="test.jpg",
                file_type="image",
                display_order=0,
                display_duration=5,
                created_at=datetime.utcnow()
            )
        ]

        response = PlaylistItemBatchResponse(
            added_count=1,
            items=items,
            failed_media_ids=[]
        )
        assert response.added_count == 1
        assert len(response.items) == 1
        assert response.failed_media_ids == []

    def test_batch_response_with_failures(self):
        """测试包含失败项的响应"""
        from app.schemas.playlist import (
            PlaylistItemBatchResponse,
            PlaylistItemResponse
        )
        from datetime import datetime

        items = [
            PlaylistItemResponse(
                id=1,
                media_id=1,
                file_name="test1.jpg",
                file_type="image",
                display_order=0,
                display_duration=5,
                created_at=datetime.utcnow()
            ),
            PlaylistItemResponse(
                id=2,
                media_id=2,
                file_name="test2.jpg",
                file_type="image",
                display_order=1,
                display_duration=5,
                created_at=datetime.utcnow()
            )
        ]

        response = PlaylistItemBatchResponse(
            added_count=2,
            items=items,
            failed_media_ids=[99, 100]
        )
        assert response.added_count == 2
        assert len(response.failed_media_ids) == 2


class TestBatchAddAPI:
    """测试批量添加 API 端点"""

    @pytest.fixture
    def test_db(self, db_session):
        """数据库会话别名"""
        return db_session

    def test_batch_add_endpoint_exists(self):
        """测试批量添加端点存在"""
        from app.api.playlists import router

        # 检查路由是否存在
        routes = [route.path for route in router.routes]
        assert '/{playlist_id}/items/batch' in routes

    def test_batch_add_schema_imported(self):
        """测试批量添加 Schema 已导入"""
        from app.api import playlists
        import inspect

        source = inspect.getsource(playlists)
        assert 'PlaylistItemBatchCreate' in source
        assert 'PlaylistItemBatchResponse' in source


class TestReorderAPI:
    """测试重排序 API"""

    def test_reorder_endpoint_exists(self):
        """测试重排序端点存在"""
        from app.api.playlists import router

        routes = [route.path for route in router.routes]
        assert '/{playlist_id}/items/reorder' in routes

    def test_reorder_schema_exists(self):
        """测试重排序 Schema 存在"""
        from app.schemas.playlist import ReorderItemsRequest

        reorder = ReorderItemsRequest(
            items=[
                {"id": 1, "order": 0},
                {"id": 2, "order": 1}
            ]
        )
        assert len(reorder.items) == 2


if __name__ == "__main__":
    pytest.main()
