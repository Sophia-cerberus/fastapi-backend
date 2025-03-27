from typing import Optional
from .user import (
    User, UserBase, UpdatePassword, UserCreate, UserPublic, UserRegister,
    UserUpdate, UserUpdateMe
)
from .item import (
    Item, ItemBase, ItemCreate, ItemPublic, ItemUpdate
)
from sqlmodel import Field, SQLModel


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class AccessToken(SQLModel):
    access_token: str
    token_type: str = "bearer"


# JSON payload containing access token & refresh token
class Token(AccessToken):
    refresh_token: str


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None
    exp: float | None = None
    type: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)
