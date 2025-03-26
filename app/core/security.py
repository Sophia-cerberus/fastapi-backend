from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


ALGORITHM = "HS256"


class TokenGenerator(ABC):
    
    @abstractmethod
    def access_token(self) -> str:
        raise NotImplementedError("Method not implemented!")

    @abstractmethod
    def refresh_token(self) -> str:
        raise NotImplementedError("Method not implemented!")


class JWTTokenGenerator(TokenGenerator):
    def __init__(self, to_encode: dict[str, Any]):
        self.to_encode: dict[str, Any] = to_encode

    def refresh_token(self):
        payload = self.to_encode.copy()
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        payload["exp"] = (
            datetime.now(timezone.utc) + refresh_token_expires
        ).timestamp()
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)

    def access_token(self) -> str:
        payload = self.to_encode.copy()
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        payload["exp"] = (datetime.now(timezone.utc) + access_token_expires).timestamp()
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_token(
    subject: str | Any, token_generator: TokenGenerator | None = None
) -> TokenGenerator:
    to_encode = {"sub": str(subject)}
    if token_generator is None:
        token_generator = JWTTokenGenerator(to_encode)
    return token_generator


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
