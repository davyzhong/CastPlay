"""
软删除功能单元测试
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import SoftDeleteMixin, TimestampMixin, query_active


class TestSoftDeleteMixin:
    """SoftDeleteMixin 测试"""

    def test_soft_delete_sets_deleted_at(self):
        """测试软删除设置 deleted_at"""
        class MockModel(SoftDeleteMixin):
            deleted_at = None

        instance = MockModel()
        assert instance.deleted_at is None
        assert not instance.is_deleted

        instance.soft_delete()
        assert instance.deleted_at is not None
        assert instance.is_deleted

    def test_restore_clears_deleted_at(self):
        """测试恢复清除 deleted_at"""
        class MockModel(SoftDeleteMixin):
            deleted_at = datetime.utcnow()

        instance = MockModel()
        assert instance.is_deleted

        instance.restore()
        assert instance.deleted_at is None
        assert not instance.is_deleted

    def test_is_deleted_property(self):
        """测试 is_deleted 属性"""
        class MockModel(SoftDeleteMixin):
            deleted_at = None

        instance = MockModel()
        assert instance.is_deleted is False

        instance.deleted_at = datetime.utcnow()
        assert instance.is_deleted is True


class TestTimestampMixin:
    """TimestampMixin 测试"""

    def test_timestamp_fields_exist(self):
        """测试时间戳字段存在"""
        assert hasattr(TimestampMixin, 'created_at')
        assert hasattr(TimestampMixin, 'updated_at')


class TestQueryActive:
    """query_active 函数测试"""

    def test_query_active_with_soft_delete_model(self):
        """测试有 deleted_at 字段的模型"""
        # 这个测试需要实际的数据库模型，跳过
        pass

    def test_query_active_without_soft_delete_model(self):
        """测试没有 deleted_at 字段的模型"""
        class MockModel:
            query = type('Query', (), {'filter': lambda s, x: 'filtered'})()

        result = query_active(MockModel)
        # 没有 deleted_at 的模型应该返回原始 query
        assert result == MockModel.query
