from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any
import secrets

import jwt
from cryptography.fernet import Fernet
from passlib.context import CryptContext

from app.core.config import settings


class TokenGenerator(ABC):
    
    @abstractmethod
    def access_token(self) -> str:
        pass

    @abstractmethod
    def refresh_token(self) -> str:
        pass


ALGORITHM = "HS256"

class TokenType(Enum):
    ACCESS_TOKEN = "access"
    REFRESH_TOKEN = "refresh"


class JWTTokenGenerator(TokenGenerator):

    def __init__(self, payload: dict[str, Any], algorithm: str):
        self.payload: dict[str, Any] = payload
        self.algorithm = algorithm

    def refresh_token(self):
        payload = self.payload.copy()
        payload.update({
            "exp": (
                datetime.now(timezone.utc) + timedelta(
                    days=settings.REFRESH_TOKEN_EXPIRE_DAYS
                )
            ).timestamp(),
            "type": TokenType.REFRESH_TOKEN.value
        })

        return jwt.encode(payload, settings.SECRET_KEY, algorithm=self.algorithm)

    def access_token(self) -> str:
        payload = self.payload.copy()
        payload.update({
            "exp": (
                datetime.now(timezone.utc) + timedelta(
                    minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
                )
            ).timestamp(),
            "type": TokenType.ACCESS_TOKEN.value
        })
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=self.algorithm)
    

class SecurityManager:

    def __init__(self):
        # 密码加密上下文
        self.pwd_context = CryptContext(
            schemes=["argon2", "bcrypt"], 
            deprecated="auto",
            argon2__time_cost=3,
            argon2__memory_cost=65536,
            argon2__parallelism=4,
            argon2__hash_len=32,
            argon2__salt_len=16
        )
        # Fernet加密配置（确保密钥持久化）
        self._fernet = Fernet(
            settings.MODEL_PROVIDER_ENCRYPTION_KEY or Fernet.generate_key().decode()
        )

    def create_token(
        self, subject: str | Any, token_generator: TokenGenerator | None = None
    ) -> TokenGenerator:
        payload = {"sub": str(subject)}
        if token_generator is None:
            token_generator = JWTTokenGenerator(payload, ALGORITHM)
        return token_generator
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """获取密码哈希值"""
        return self.pwd_context.hash(password)

    def generate_apikey(self) -> str:
        """生成API密钥"""
        return secrets.token_urlsafe(32)

    def generate_short_apikey(self, key: str) -> str:
        """生成短格式API密钥"""
        return f"{key[:4]}...{key[-4:]}"

    def encrypt_api_key(self, data: str) -> str:
        """加密API密钥"""
        if not data:
            return data
        return self._fernet.encrypt(data.encode()).decode()

    def decrypt_api_key(self, encrypted_data: str) -> str:
        """解密API密钥"""
        if not encrypted_data:
            return encrypted_data
        try:
            return self._fernet.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            raise ValueError("Decryption failed,Invalid API key Token") from e


# 创建单例实例
security_manager = SecurityManager()

generate_token = security_manager.create_token
verify_password = security_manager.verify_password
get_password_hash = security_manager.get_password_hash
generate_apikey = security_manager.generate_apikey
generate_short_apikey = security_manager.generate_short_apikey