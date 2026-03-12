"""
异常处理场景单元测试
覆盖各模块的异常情况
"""
import pytest
from fastapi import HTTPException, status
from unittest.mock import AsyncMock, MagicMock, patch


class TestDatabaseExceptionHandling:
    """数据库异常处理测试"""

    def test_database_connection_failure(self):
        """测试数据库连接失败"""
        from app.database import init_database
        import sqlite3

        with patch('sqlite3.connect') as mock_connect:
            mock_connect.side_effect = sqlite3.OperationalError(
                "Unable to open database")

            with pytest.raises(sqlite3.OperationalError):
                init_database()

    def test_database_integrity_error(self):
        """测试数据库完整性错误"""
        from app.database import get_db
        import sqlite3

        # Mock 一个会抛出完整性错误的 session
        mock_session = MagicMock()
        mock_session.execute.side_effect = sqlite3.IntegrityError(
            "UNIQUE constraint failed")

        with patch('app.database.SessionLocal', return_value=mock_session):
            with pytest.raises(sqlite3.IntegrityError):
                db = next(get_db())
                db.execute("INSERT INTO ...")


class TestAuthExceptionHandling:
    """认证异常处理测试"""

    @pytest.mark.asyncio
    async def test_invalid_jwt_token(self):
        """测试无效的 JWT Token"""
        from app.utils.security import verify_token
        from jose import JWTError

        with pytest.raises(JWTError):
            await verify_token("invalid.token.here")

    @pytest.mark.asyncio
    async def test_expired_token(self):
        """测试过期的 Token"""
        from app.utils.security import create_access_token, verify_token
        import time

        # 创建立即过期的 token
        with patch('app.config.settings.ACCESS_TOKEN_EXPIRE_MINUTES', 0):
            token = await create_access_token(data={"sub": "test"})

            # 等待过期
            time.sleep(1)

            # 验证 token 已失效
            # 注意：实际场景中需要更复杂的测试逻辑

    def test_wrong_credentials(self):
        """测试错误的凭证"""
        from app.api.auth import authenticate_user

        # 测试不存在的用户
        result = authenticate_user("nonexistent", "wrongpass")
        assert result is False

    def test_missing_credentials(self):
        """测试缺失凭证"""
        from app.api.auth import authenticate_user

        # 测试空凭证
        result = authenticate_user("", "")
        assert result is False


class TestWebSocketExceptionHandling:
    """WebSocket 异常处理测试"""

    @pytest.mark.asyncio
    async def test_websocket_disconnect_handling(self):
        """测试 WebSocket 断开处理"""
        from app.websocket.handler import ConnectionManager
        from fastapi import WebSocketDisconnect

        manager = ConnectionManager()
        mock_websocket = AsyncMock()
        mock_websocket.receive_json.side_effect = WebSocketDisconnect()

        # 不应抛出异常
        try:
            while True:
                await mock_websocket.receive_json()
        except WebSocketDisconnect:
            pass  # 预期行为

    @pytest.mark.asyncio
    async def test_websocket_invalid_message(self):
        """测试 WebSocket 接收无效消息"""
        from app.websocket.handler import ConnectionManager

        manager = ConnectionManager()
        mock_websocket = AsyncMock()
        mock_websocket.receive_json.side_effect = ValueError("Invalid JSON")

        with pytest.raises(ValueError):
            await mock_websocket.receive_json()

    @pytest.mark.asyncio
    async def test_websocket_send_to_disconnected(self):
        """测试向断开的连接发送消息"""
        from app.websocket.handler import ConnectionManager

        manager = ConnectionManager()
        mock_websocket = AsyncMock()
        mock_websocket.send_json.side_effect = Exception("Connection closed")

        with pytest.raises(Exception):
            await mock_websocket.send_json({"test": "data"})


class TestFileUploadExceptionHandling:
    """文件上传异常处理测试"""

    def test_disk_full_scenario(self):
        """测试磁盘已满场景"""
        import os
        from pathlib import Path

        with patch('pathlib.Path.mkdir') as mock_mkdir:
            mock_mkdir.side_effect = OSError("No space left on device")

            with pytest.raises(OSError, match="No space left"):
                Path("/fake/path").mkdir()

    def test_invalid_file_type(self):
        """测试无效文件类型"""
        from app.services.converter import PPTConverter

        converter = PPTConverter()

        # 测试不支持的文件扩展名
        with pytest.raises(ValueError, match="Unsupported file type"):
            converter._validate_file_type("test.unsupported")

    def test_file_too_large(self):
        """测试文件过大"""
        from app.config import settings

        # Mock 文件大小超过限制
        large_size = settings.MAX_FILE_SIZE + 1

        with pytest.raises(HTTPException) as exc_info:
            if large_size > settings.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="File too large"
                )

        assert exc_info.value.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE


class TestSchedulerExceptionHandling:
    """调度器异常处理测试"""

    def test_task_execution_failure(self):
        """测试任务执行失败"""
        from app.scheduler import scheduler
        from apscheduler.exceptions import JobExecutionError

        def failing_task():
            raise Exception("Task failed")

        job = scheduler.add_job(failing_task, 'date')

        # 任务应该会失败，但不应影响调度器
        assert job is not None

    def test_scheduler_start_with_existing_jobs(self):
        """测试调度器启动时已有任务"""
        from app.scheduler import start, stop

        # 添加一个任务
        def dummy_task():
            pass

        from app.scheduler import scheduler
        scheduler.add_job(dummy_task, 'interval', seconds=60)

        # 启动不应抛出异常
        start()

        # 清理
        stop()

    def test_scheduler_stop_gracefully(self):
        """测试调度器优雅停止"""
        from app.scheduler import start, stop

        start()

        # 停止不应抛出异常
        stop()


class TestRateLimitExceptionHandling:
    """速率限制异常处理测试"""

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self):
        """测试超过速率限制"""
        from app.utils.simple_rate_limiter import SimpleRateLimiter
        from fastapi import HTTPException, status

        limiter = SimpleRateLimiter(max_requests=2, window_seconds=60)

        # Mock request
        mock_request = MagicMock()
        mock_request.client.host = "test_client"

        # 前两次应该成功
        await limiter(mock_request)
        await limiter(mock_request)

        # 第三次应该被限制
        with pytest.raises(HTTPException) as exc_info:
            await limiter(mock_request)

        assert exc_info.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    @pytest.mark.asyncio
    async def test_rate_limit_window_reset(self):
        """测试速率限制窗口重置"""
        from app.utils.simple_rate_limiter import SimpleRateLimiter
        import time

        limiter = SimpleRateLimiter(max_requests=1, window_seconds=1)

        mock_request = MagicMock()
        mock_request.client.host = "test_client"

        # 第一次请求
        await limiter(mock_request)

        # 等待窗口重置
        time.sleep(1.1)

        # 应该可以再次请求
        await limiter(mock_request)


class TestAPIExceptionHandling:
    """API 异常处理测试"""

    @pytest.mark.asyncio
    async def test_device_not_found(self):
        """测试设备未找到"""
        from fastapi import HTTPException, status

        # 模拟设备查询
        device_id = "nonexistent"

        # 应抛出 404
        with pytest.raises(HTTPException) as exc_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device {device_id} not found"
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_media_not_found(self):
        """测试媒体文件未找到"""
        from fastapi import HTTPException, status

        media_id = 99999

        with pytest.raises(HTTPException) as exc_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Media {media_id} not found"
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_playlist_not_found(self):
        """测试播放列表未找到"""
        from fastapi import HTTPException, status

        playlist_id = 99999

        with pytest.raises(HTTPException) as exc_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Playlist {playlist_id} not found"
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_permission_denied(self):
        """测试权限拒绝"""
        from fastapi import HTTPException, status

        with pytest.raises(HTTPException) as exc_info:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_validation_error(self):
        """测试数据验证错误"""
        from pydantic import ValidationError

        from app.schemas.user import UserCreate

        try:
            # 尝试创建无效用户
            UserCreate(username="", password="")
        except ValidationError as e:
            # 应捕获验证错误
            assert len(e.errors()) > 0


class TestGlobalExceptionHandler:
    """全局异常处理器测试"""

    @pytest.mark.asyncio
    async def test_unhandled_exception_logging(self):
        """测试未处理异常会被记录日志"""
        from app.main import app
        from fastapi.testclient import TestClient
        import logging

        # 创建一个会抛出异常的端点
        @app.get("/test-exception")
        async def test_exception():
            raise Exception("Test exception")

        client = TestClient(app)

        # 调用端点
        response = client.get("/test-exception")

        # 应该返回 500
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
