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
    """

    KEY_PREFIX = "castplay:devices:connected"
    EXPIRE_SECONDS = 300  # 5分钟过期

    def __init__(self):
        # 内存 fallback 存储
        self._local_cache: Dict[int, Dict[str, Any]] = {}

    @property
    def redis(self):
        """获取 Redis 客户端（每次调用时检查）"""
        return get_redis()

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
                self.redis.hset(self.KEY_PREFIX, str(
                    device_id), json.dumps(data))
                self.redis.expire(self.KEY_PREFIX, self.EXPIRE_SECONDS)
                return
            except Exception as e:
                logger.error(f"Redis set_connected failed: {e}")

        # Fallback 到内存
        self._local_cache[device_id] = data

    def remove_connected(self, device_id: int):
        """移除设备连接"""
        if self.redis:
            try:
                self.redis.hdel(self.KEY_PREFIX, str(device_id))
                return
            except Exception as e:
                logger.error(f"Redis remove_connected failed: {e}")

        self._local_cache.pop(device_id, None)

    def is_connected(self, device_id: int) -> bool:
        """检查设备是否连接"""
        if self.redis:
            try:
                return self.redis.hexists(self.KEY_PREFIX, str(device_id))
            except Exception as e:
                logger.error(f"Redis is_connected failed: {e}")

        return device_id in self._local_cache

    def get_session_id(self, device_id: int) -> Optional[str]:
        """获取设备会话 ID"""
        if self.redis:
            try:
                data = self.redis.hget(self.KEY_PREFIX, str(device_id))
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
                all_data = self.redis.hgetall(self.KEY_PREFIX)
                return {int(k): json.loads(v)["sid"] for k, v in all_data.items()}
            except Exception as e:
                logger.error(f"Redis get_all_connected failed: {e}")

        return {k: v["sid"] for k, v in self._local_cache.items()}

    def refresh_heartbeat(self, device_id: int):
        """刷新心跳时间"""
        if self.redis:
            try:
                data = self.redis.hget(self.KEY_PREFIX, str(device_id))
                if data:
                    info = json.loads(data)
                    info["ts"] = int(time.time())
                    self.redis.hset(self.KEY_PREFIX, str(
                        device_id), json.dumps(info))
                    self.redis.expire(self.KEY_PREFIX, self.EXPIRE_SECONDS)
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
        all_devices = self.get_all_connected()
        for device_id, sid in all_devices.items():
            if sid == session_id:
                return device_id
        return None

    def cleanup_stale_connections(self, max_age_seconds: int = 300):
        """
        清理过期连接

        Args:
            max_age_seconds: 最大连接年龄（秒）
        """
        current_time = int(time.time())
        stale_devices = []

        if self.redis:
            try:
                all_data = self.redis.hgetall(self.KEY_PREFIX)
                for device_id_str, data_str in all_data.items():
                    info = json.loads(data_str)
                    if current_time - info.get("ts", 0) > max_age_seconds:
                        stale_devices.append(device_id_str)

                for device_id_str in stale_devices:
                    self.redis.hdel(self.KEY_PREFIX, device_id_str)
                    logger.info(
                        f"Cleaned up stale connection for device {device_id_str}")
                return
            except Exception as e:
                logger.error(f"Redis cleanup_stale_connections failed: {e}")

        # 内存清理
        for device_id, info in list(self._local_cache.items()):
            if current_time - info.get("ts", 0) > max_age_seconds:
                del self._local_cache[device_id]
                logger.info(
                    f"Cleaned up stale connection for device {device_id}")


# 全局单例
device_store = DeviceConnectionStore()


__all__ = ['device_store', 'get_redis', 'DeviceConnectionStore']
