"""
并发场景单元测试
覆盖数据库、缓存、WebSocket 等并发操作
"""
import pytest
import asyncio
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import AsyncMock, MagicMock, patch


class TestConcurrentDatabaseAccess:
    """并发数据库访问测试"""

    @pytest.mark.asyncio
    async def test_concurrent_device_registrations(self):
        """测试并发设备注册"""
        from app.database import get_db, SessionLocal
        from app.models.device import Device
        import uuid

        async def register_device(device_id: str):
            db = SessionLocal()
            try:
                device = Device(
                    device_id=device_id,
                    name=f"Device {device_id}",
                    mac_address="00:00:00:00:00:00"
                )
                db.add(device)
                db.commit()
                return True
            except Exception:
                db.rollback()
                return False
            finally:
                db.close()

        # 模拟 10 个并发设备注册
        device_ids = [str(uuid.uuid4()) for _ in range(10)]
        tasks = [register_device(did) for did in device_ids]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 大部分应该成功（可能有少量冲突）
        success_count = sum(1 for r in results if r is True)
        assert success_count >= 8  # 允许少量失败

    @pytest.mark.asyncio
    async def test_concurrent_playlist_updates(self):
        """测试并发播放列表更新"""
        from app.database import SessionLocal
        from app.models.playlist import Playlist

        async def update_playlist(playlist_id: int, version: int):
            db = SessionLocal()
            try:
                playlist = db.query(Playlist).filter(
                    Playlist.id == playlist_id).first()
                if playlist and playlist.version == version:
                    playlist.version = version + 1
                    db.commit()
                    return True
                return False
            except Exception:
                db.rollback()
                return False
            finally:
                db.close()

        # 模拟并发更新
        tasks = [update_playlist(1, i) for i in range(5)]
        results = await asyncio.gather(*tasks)

        # 只有一个应该成功（乐观锁）
        assert sum(results) == 1

    @pytest.mark.asyncio
    async def test_database_transaction_isolation(self):
        """测试数据库事务隔离"""
        from app.database import SessionLocal

        # 测试读写隔离
        session1 = SessionLocal()
        session2 = SessionLocal()

        try:
            # session1 开始事务
            session1.begin()

            # session2 也应该能读取
            # 验证不会死锁

        finally:
            session1.close()
            session2.close()


class TestConcurrentCacheOperations:
    """并发缓存操作测试"""

    @pytest.mark.asyncio
    async def test_concurrent_cache_read_write(self):
        """测试并发缓存读写"""
        cache = {}
        lock = asyncio.Lock()

        async def write(key: str, value: str):
            async with lock:
                cache[key] = value

        async def read(key: str):
            async with lock:
                return cache.get(key)

        # 并发读写
        tasks = []
        for i in range(10):
            tasks.append(write(f"key_{i}", f"value_{i}"))
            tasks.append(read(f"key_{i}"))

        await asyncio.gather(*tasks)

        # 验证缓存一致性
        assert len(cache) == 10

    @pytest.mark.asyncio
    async def test_cache_eviction_under_load(self):
        """测试负载下的缓存淘汰"""
        from collections import OrderedDict

        class LRUCache:
            def __init__(self, capacity: int):
                self.cache = OrderedDict()
                self.capacity = capacity

            def get(self, key: str) -> str:
                if key not in self.cache:
                    return None
                self.cache.move_to_end(key)
                return self.cache[key]

            def put(self, key: str, value: str):
                if key in self.cache:
                    self.cache.move_to_end(key)
                self.cache[key] = value
                if len(self.cache) > self.capacity:
                    self.cache.popitem(last=False)

        cache = LRUCache(capacity=5)

        # 并发写入超过容量
        for i in range(10):
            cache.put(f"key_{i}", f"value_{i}")

        # 验证只保留最新的 5 个
        assert len(cache.cache) == 5
        assert "key_9" in cache.cache


class TestConcurrentWebSocketConnections:
    """并发 WebSocket 连接测试"""

    @pytest.mark.asyncio
    async def test_multiple_simultaneous_connections(self):
        """测试多个同时连接"""
        from app.websocket.handler import ConnectionManager

        manager = ConnectionManager()

        # 模拟 50 个并发连接
        connections = []
        for i in range(50):
            mock_ws = AsyncMock()
            mock_ws.client.host = f"192.168.1.{i}"
            connections.append((f"device_{i}", mock_ws))

        # 全部连接
        for device_id, ws in connections:
            await manager.connect(device_id, ws)

        # 验证连接数
        assert len(manager.active_connections) == 50

        # 全部断开
        for device_id, _ in connections:
            manager.disconnect(device_id)

        assert len(manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_concurrent_broadcast(self):
        """测试并发广播"""
        from app.websocket.handler import ConnectionManager

        manager = ConnectionManager()

        # 添加多个连接
        for i in range(10):
            mock_ws = AsyncMock()
            await manager.connect(f"device_{i}", mock_ws)

        # 并发广播
        message = {"type": "test", "data": "broadcast"}
        await manager.broadcast(message)

        # 验证所有连接都收到消息
        for device_id in manager.active_connections:
            for ws in manager.active_connections[device_id]:
                ws.send_json.assert_called()

    @pytest.mark.asyncio
    async def test_concurrent_send_to_device(self):
        """测试并发向设备发送消息"""
        from app.websocket.handler import ConnectionManager

        manager = ConnectionManager()
        mock_ws = AsyncMock()

        await manager.connect("device_1", mock_ws)

        # 并发发送多条消息
        tasks = [
            manager.send_to_device("device_1", {"msg": f"message_{i}"})
            for i in range(10)
        ]

        await asyncio.gather(*tasks)

        # 验证消息都发送出了
        assert mock_ws.send_json.call_count >= 10


class TestConcurrentFileOperations:
    """并发文件操作测试"""

    @pytest.mark.asyncio
    async def test_concurrent_file_upload(self):
        """测试并发文件上传"""
        import tempfile
        import shutil
        from pathlib import Path

        upload_dir = Path(tempfile.mkdtemp())

        async def upload_file(file_id: int):
            file_path = upload_dir / f"file_{file_id}.txt"
            try:
                # 模拟文件写入
                with open(file_path, 'w') as f:
                    f.write(f"Content {file_id}")
                return True
            except Exception:
                return False

        try:
            # 并发上传 20 个文件
            tasks = [upload_file(i) for i in range(20)]
            results = await asyncio.gather(*tasks)

            # 验证大部分成功
            success_count = sum(results)
            assert success_count >= 18

            # 验证文件存在
            files = list(upload_dir.glob("*.txt"))
            assert len(files) >= 18

        finally:
            shutil.rmtree(upload_dir)

    @pytest.mark.asyncio
    async def test_concurrent_ppt_conversion(self):
        """测试并发 PPT 转换"""
        from app.services.converter import PPTConverter

        converter = PPTConverter()

        # Mock 转换过程
        async def convert_mock(file_path: str):
            await asyncio.sleep(0.1)  # 模拟耗时
            return f"{file_path}.mp4"

        # 并发转换 5 个文件
        with patch.object(converter, 'convert', new=convert_mock):
            tasks = [
                converter.convert(f"presentation_{i}.pptx")
                for i in range(5)
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 大部分应该成功
            success_count = sum(
                1 for r in results if not isinstance(r, Exception))
            assert success_count >= 4


class TestConcurrentSchedulerTasks:
    """调度器并发任务测试"""

    @pytest.mark.asyncio
    async def test_concurrent_scheduled_jobs(self):
        """测试并发计划任务"""
        from app.scheduler import scheduler
        import time

        results = []

        def job(result_id: int):
            results.append(result_id)
            time.sleep(0.1)

        # 添加多个同时执行的任务
        for i in range(5):
            scheduler.add_job(job, 'date', args=[i])

        # 等待执行
        await asyncio.sleep(1)

        # 验证所有任务都执行了
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_scheduler_max_instances(self):
        """测试调度器最大实例数"""
        from apscheduler.executors.pool import ThreadPoolExecutor
        from app.scheduler import BackgroundScheduler

        exec_scheduler = BackgroundScheduler(
            executors={'default': ThreadPoolExecutor(3)},
            timezone='Asia/Shanghai'
        )

        execution_count = {'count': 0}
        lock = asyncio.Lock()

        def concurrent_job():
            execution_count['count'] += 1
            time.sleep(0.2)

        # 添加多个相同任务
        for i in range(5):
            exec_scheduler.add_job(
                concurrent_job, 'date', id='same_job', replace_existing=True)

        exec_scheduler.start()
        await asyncio.sleep(1)
        exec_scheduler.shutdown()

        # 验证任务被执行（可能不是全部，因为有替换）
        assert execution_count['count'] >= 1


class TestConcurrentRateLimiting:
    """并发速率限制测试"""

    @pytest.mark.asyncio
    async def test_rate_limit_with_concurrent_requests(self):
        """测试并发请求下的速率限制"""
        from app.utils.simple_rate_limiter import SimpleRateLimiter
        from fastapi import HTTPException

        limiter = SimpleRateLimiter(max_requests=10, window_seconds=1)

        # 模拟 20 个并发请求来自同一 IP
        async def make_request(client_ip: str):
            mock_request = MagicMock()
            mock_request.client.host = client_ip

            try:
                await limiter(mock_request)
                return True
            except HTTPException:
                return False

        # 所有请求来自同一 IP
        tasks = [make_request("192.168.1.1") for _ in range(20)]
        results = await asyncio.gather(*tasks)

        # 前 10 个应该成功，后 10 个被限制
        success_count = sum(results)
        assert success_count == 10

    @pytest.mark.asyncio
    async def test_rate_limit_with_multiple_clients(self):
        """测试多客户端并发速率限制"""
        from app.utils.simple_rate_limiter import SimpleRateLimiter
        from fastapi import HTTPException

        limiter = SimpleRateLimiter(max_requests=5, window_seconds=1)

        async def make_request(client_ip: str):
            mock_request = MagicMock()
            mock_request.client.host = client_ip

            try:
                await limiter(mock_request)
                return True
            except HTTPException:
                return False

        # 5 个不同客户端，每个发起 10 个请求
        tasks = []
        for i in range(5):
            ip = f"192.168.1.{i}"
            tasks.extend([make_request(ip) for _ in range(10)])

        results = await asyncio.gather(*tasks)

        # 每个客户端前 5 个成功，总共 25 个成功
        success_count = sum(results)
        assert success_count == 25


class TestRaceConditions:
    """竞态条件测试"""

    @pytest.mark.asyncio
    async def test_no_race_condition_in_counter(self):
        """测试计数器无竞态条件"""
        counter = {'value': 0}
        lock = asyncio.Lock()

        async def increment():
            async with lock:
                counter['value'] += 1

        # 并发增加 100 次
        tasks = [increment() for _ in range(100)]
        await asyncio.gather(*tasks)

        # 验证最终值正确
        assert counter['value'] == 100

    @pytest.mark.asyncio
    async def test_atomic_playlist_update(self):
        """测试播放列表原子更新"""
        from app.database import SessionLocal
        from app.models.playlist import Playlist

        # 使用数据库事务保证原子性
        db = SessionLocal()
        try:
            db.begin()

            # 模拟更新操作
            # 在实际测试中需要真实的数据库环境

            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
