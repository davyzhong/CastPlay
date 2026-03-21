"""
CLI 配置管理

管理服务器地址、认证令牌等配置信息
配置存储在 ~/.castplay/config.json

注意：认证令牌使用系统密钥环安全存储（如果可用）
"""
import json
import logging
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, ConfigDict

from secure_storage import store_token, get_token, delete_token, is_secure_storage_available

logger = logging.getLogger(__name__)


class CLIConfig(BaseModel):
    """CLI 配置模型"""
    model_config = ConfigDict(extra="ignore")

    server_url: str = "http://localhost:8000"
    # Note: token is stored securely in keyring, not in this model
    timeout: int = 30  # 请求超时时间（秒）


class ConfigManager:
    """配置管理器"""

    def __init__(self):
        self.config_dir = Path.home() / ".castplay"
        self.config_file = self.config_dir / "config.json"
        self._config: Optional[CLIConfig] = None
        self._token: Optional[str] = None

    @property
    def config(self) -> CLIConfig:
        """获取配置（懒加载）"""
        if self._config is None:
            self._config = self._load_config()
        return self._config

    def _load_config(self) -> CLIConfig:
        """加载配置文件"""
        if not self.config_file.exists():
            return CLIConfig()

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Migrate legacy plain-text token to secure storage
            legacy_token = data.pop("token", None)
            if legacy_token and is_secure_storage_available():
                store_token(legacy_token)
                logger.info("Migrated token from config file to secure storage")
                # Save config without token
                self._save_config_data(data)

            return CLIConfig(**data)
        except Exception:
            return CLIConfig()

    def _save_config_data(self, data: dict):
        """Save config data to file"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        # Ensure no token in file
        data.pop("token", None)
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _save_config(self):
        """保存配置文件（不包含敏感令牌）"""
        self._save_config_data(self.config.model_dump(exclude_none=True))

    def set_server(self, server_url: str):
        """设置服务器地址"""
        self.config.server_url = server_url.rstrip("/")
        self._save_config()

    def set_token(self, token: Optional[str]):
        """
        设置认证令牌

        令牌将安全存储在系统密钥环中（如果可用）
        如果密钥环不可用，将显示警告
        """
        if token:
            if store_token(token):
                self._token = token
                logger.info("Token stored securely")
            else:
                # Fallback: store in memory only for this session
                self._token = token
                logger.warning(
                    "Token stored in memory only (not persistent). "
                    "Install 'keyring' package for secure persistent storage."
                )
        else:
            delete_token()
            self._token = None

    def set_timeout(self, timeout: int):
        """设置请求超时时间"""
        self.config.timeout = timeout
        self._save_config()

    def clear_token(self):
        """清除认证令牌"""
        delete_token()
        self._token = None

    def get_config_path(self) -> Path:
        """获取配置文件路径"""
        return self.config_file

    @property
    def server_url(self) -> str:
        """获取服务器地址"""
        return self.config.server_url

    @property
    def token(self) -> Optional[str]:
        """
        获取认证令牌

        优先从内存缓存获取，然后从安全存储获取
        """
        if self._token is not None:
            return self._token

        self._token = get_token()
        return self._token

    @property
    def timeout(self) -> int:
        """获取超时时间"""
        return self.config.timeout

    def get_storage_info(self) -> dict:
        """获取存储信息"""
        from secure_storage import get_storage_info
        return get_storage_info()


# 全局配置管理器实例
config_manager = ConfigManager()
