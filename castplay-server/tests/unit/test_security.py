"""
安全模块单元测试
"""
import pytest
from datetime import timedelta
from unittest.mock import patch, MagicMock

from app.core.security import TokenData


class TestPasswordHashing:
    """密码哈希测试"""

    def test_hash_password_creates_hash(self):
        """测试密码哈希创建"""
        from app.core.security import get_password_hash
        password = "test123"

        with patch('app.core.security.pwd_context') as mock_pwd:
            mock_pwd.hash.return_value = "hashed_password"
            hashed = get_password_hash(password)

            assert hashed == "hashed_password"
            mock_pwd.hash.assert_called_once_with(password)

    def test_verify_password_correct(self):
        """测试正确密码验证"""
        from app.core.security import verify_password

        with patch('app.core.security.pwd_context') as mock_pwd:
            mock_pwd.verify.return_value = True
            result = verify_password("test", "hashed")

            assert result is True

    def test_verify_password_incorrect(self):
        """测试错误密码验证"""
        from app.core.security import verify_password

        with patch('app.core.security.pwd_context') as mock_pwd:
            mock_pwd.verify.return_value = False
            result = verify_password("wrong", "hashed")

            assert result is False


class TestJWTToken:
    """JWT Token 测试"""

    def test_create_access_token(self):
        """测试创建访问令牌"""
        from app.core.security import create_access_token

        with patch('app.core.security.jwt') as mock_jwt:
            mock_jwt.encode.return_value = "mock_token"
            token = create_access_token(1, "test_user")

            assert token == "mock_token"
            mock_jwt.encode.assert_called_once()

    def test_create_token_pair(self):
        """测试创建 Token 对"""
        from app.core.security import create_token_pair

        with patch('app.core.security.create_token') as mock_create:
            mock_create.return_value = "mock_token"
            token_pair = create_token_pair(1, "test_user")

            assert token_pair.access_token == "mock_token"
            assert token_pair.refresh_token == "mock_token"
            assert token_pair.token_type == "bearer"

    def test_verify_valid_token(self):
        """测试验证有效令牌"""
        from app.core.security import verify_token

        mock_payload = {
            "sub": "1",
            "username": "test_user",
            "type": "access"
        }

        with patch('app.core.security.jwt') as mock_jwt:
            mock_jwt.decode.return_value = mock_payload
            token_data = verify_token("valid_token", "access")

            assert token_data is not None
            assert token_data.user_id == 1
            assert token_data.username == "test_user"

    def test_verify_invalid_token(self):
        """测试验证无效令牌"""
        from app.core.security import verify_token
        from jose import JWTError

        with patch('app.core.security.jwt') as mock_jwt:
            mock_jwt.decode.side_effect = JWTError("Invalid token")
            token_data = verify_token("invalid_token")

            assert token_data is None


class TestTokenData:
    """TokenData 模型测试"""

    def test_token_data_defaults(self):
        """测试 TokenData 默认值"""
        token_data = TokenData()

        assert token_data.user_id is None
        assert token_data.username is None
        assert token_data.token_type == "access"

    def test_token_data_with_values(self):
        """测试 TokenData 赋值"""
        token_data = TokenData(
            user_id=1,
            username="test_user",
            token_type="refresh"
        )

        assert token_data.user_id == 1
        assert token_data.username == "test_user"
        assert token_data.token_type == "refresh"
