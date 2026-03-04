"""
Redis 客户端封装

提供设备连接状态的 Redis 存储，支持多实例部署
当 Redis 不可用时自动降级到内存存储
"""
import json
import time
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# 延迟导入 Redis，避免未安装时启动失败
_redis_client = None
_redis_available = None


def _init_redis():
    """初始化 Redis 连接（懒加载）"""
    global _redis_client, _redis_available

    if _redis_available is not None:
        return _redis_available

    try:
        import redis
        from flask import current_app

        redis_url = current_app.config.get('REDIS_URL')
        if redis_url:
            _redis_client = redis.from_url(redis_url, decode_responses=True)
            # 测试连接
            _redis_client.ping()
            _redis_available = True
            logger.info("Redis connection established")
        else:
            _redis_available = False
            logger.info("Redis URL not configured, using in-memory storage")
    except ImportError:
        _redis_available = False
        logger.warning("redis package not installed, using in-memory storage")
    except Exception as e:
        _redis_available = False
        logger.warning(
            f"Redis connection failed: {e}, using in-memory storage")

    return _redis_available


def get_redis():
    """获取 Redis 客户端"""
    if _init_redis():
        return _redis_client
    return None


class DeviceConnectionStore:
    """
    设备连接状态存储

    支持 Redis 持久化存储，当 Redis 不可用时自动降级到内存存储

    改进：使用独立 key 存储每个设备，让每个设备有独立的 TTL
    """

    KEY_PREFIX = "castplay:device:connected"
    SESSION_PREFIX = "castplay:device:session"
    EXPIRE_SECONDS = 300  # 5分钟过期

    def __init__(self):
        # 内存 fallback 存储
        self._local_cache: Dict[int, Dict[str, Any]] = {}
        self._session_map: Dict[str, int] = {}  # session_id -> device_id 映射

    @property
    def redis(self):
        """获取 Redis 客户端（每次调用时检查）"""
        return get_redis()

    def _device_key(self, device_id: int) -> str:
        """生成设备状态 key"""
        return f"{self.KEY_PREFIX}:{device_id}"

    def _session_key(self, session_id: str) -> str:
        """生成会话映射 key"""
        return f"{self.SESSION_PREFIX}:{session_id}"

    def set_connected(self, device_id: int, session_id: str, server_id: str = "default"):
        """
        记录设备连接

        Args:
            device_id: 设备数据库 ID
            session_id: WebSocket 会话 ID
            server_id: 服务器实例 ID（多实例部署时使用）
        """
        data = {
            "sid": session_id,
            "server": server_id,
            "ts": int(time.time())
        }

        if self.redis:
            try:
                # 使用独立 key，每个设备有独立的 TTL
                device_key = self._device_key(device_id)
                session_key = self._session_key(session_id)

                # 设置设备状态（带 TTL）
                self.redis.setex(
                    device_key, self.EXPIRE_SECONDS, json.dumps(data))
                # 设置会话到设备的映射（带相同 TTL）
                self.redis.setex(
                    session_key, self.EXPIRE_SECONDS, str(device_id))
                return
            except Exception as e:
                logger.error(f"Redis set_connected failed: {e}")

        # Fallback 到内存
        self._local_cache[device_id] = data
        self._session_map[session_id] = device_id

    def remove_connected(self, device_id: int):
        """移除设备连接"""
        if self.redis:
            try:
                # 先获取 session_id
                device_key = self._device_key(device_id)
                data = self.redis.get(device_key)
                if data:
                    info = json.loads(data)
                    session_id = info.get("sid")
                    if session_id:
                        self.redis.delete(self._session_key(session_id))
                self.redis.delete(device_key)
                return
            except Exception as e:
                logger.error(f"Redis remove_connected failed: {e}")

        # Fallback 清理
        if device_id in self._local_cache:
            session_id = self._local_cache[device_id].get("sid")
            if session_id:
                self._session_map.pop(session_id, None)
            del self._local_cache[device_id]

    def is_connected(self, device_id: int) -> bool:
        """检查设备是否连接"""
        if self.redis:
            try:
                return self.redis.exists(self._device_key(device_id)) > 0
            except Exception as e:
                logger.error(f"Redis is_connected failed: {e}")

        return device_id in self._local_cache

    def get_session_id(self, device_id: int) -> Optional[str]:
        """获取设备会话 ID"""
        if self.redis:
            try:
                data = self.redis.get(self._device_key(device_id))
                if data:
                    return json.loads(data).get("sid")
                return None
            except Exception as e:
                logger.error(f"Redis get_session_id failed: {e}")

        info = self._local_cache.get(device_id)
        return info.get("sid") if info else None

    def get_all_connected(self) -> Dict[int, str]:
        """
        获取所有连接的设备

        Returns:
            {device_id: session_id, ...}
        """
        if self.redis:
            try:
                # 使用 SCAN 查找所有设备 key
                result = {}
                cursor = 0
                while True:
                    cursor, keys = self.redis.scan(
                        cursor, match=f"{self.KEY_PREFIX}:*")
                    for key in keys:
                        data = self.redis.get(key)
                        if data:
                            device_id = int(key.split(":")[-1])
                            result[device_id] = json.loads(data)["sid"]
                    if cursor == 0:
                        break
                return result
            except Exception as e:
                logger.error(f"Redis get_all_connected failed: {e}")

        return {k: v["sid"] for k, v in self._local_cache.items()}

    def refresh_heartbeat(self, device_id: int):
        """
        刷新心跳时间

        重置设备的 TTL，确保设备保持在线状态
        """
        if self.redis:
            try:
                device_key = self._device_key(device_id)
                data = self.redis.get(device_key)
                if data:
                    info = json.loads(data)
                    info["ts"] = int(time.time())
                    # 重新设置并刷新 TTL
                    self.redis.setex(
                        device_key, self.EXPIRE_SECONDS, json.dumps(info))

                    # 同时刷新 session 映射的 TTL
                    session_id = info.get("sid")
                    if session_id:
                        self.redis.expire(self._session_key(
                            session_id), self.EXPIRE_SECONDS)
                return
            except Exception as e:
                logger.error(f"Redis refresh_heartbeat failed: {e}")

        if device_id in self._local_cache:
            self._local_cache[device_id]["ts"] = int(time.time())

    def find_device_by_session(self, session_id: str) -> Optional[int]:
        """
        根据会话 ID 查找设备 ID

        Args:
            session_id: WebSocket 会话 ID

        Returns:
            设备 ID 或 None
        """
        if self.redis:
            try:
                # 使用会话映射 key 直接查找，O(1) 复杂度
                device_id = self.redis.get(self._session_key(session_id))
                if device_id:
                    return int(device_id)
                return None
            except Exception as e:
                logger.error(f"Redis find_device_by_session failed: {e}")

        return self._session_map.get(session_id)

    def cleanup_stale_connections(self, max_age_seconds: int = 300):
        """
        清理过期连接

        注意：使用独立 key 并设置 TTL 后，Redis 会自动清理过期 key
        此方法主要用于内存 fallback 模式

        Args:
            max_age_seconds: 最大连接年龄（秒）
        """
        current_time = int(time.time())

        # 内存清理（Redis 会自动清理过期 key）
        stale_devices = []
        for device_id, info in list(self._local_cache.items()):
            if current_time - info.get("ts", 0) > max_age_seconds:
                stale_devices.append(device_id)

        for device_id in stale_devices:
            session_id = self._local_cache[device_id].get("sid")
            if session_id:
                self._session_map.pop(session_id, None)
            del self._local_cache[device_id]
            logger.info(f"Cleaned up stale connection for device {device_id}")


# 全局单例
device_store = DeviceConnectionStore()


__all__ = ['device_store', 'get_redis', 'DeviceConnectionStore']
