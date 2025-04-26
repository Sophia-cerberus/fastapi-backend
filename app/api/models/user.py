import uuid

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel


class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = None
    language: str = Field(default="en-US")


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str


class UserRegister(SQLModel):
    email: EmailStr
    password: str
    full_name: str | None = None


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = None  # type: ignore
    password: str | None = None


class UserUpdateMe(SQLModel):
    full_name: str | None = None
    email: EmailStr | None = None


class UpdatePassword(SQLModel):
    current_password: str
    new_password: str


class UpdateLanguageMe(SQLModel):
    language: str = Field(default="en-US")


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID | None = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    hashed_password: str
    language: str = Field(default="en-US")


# Properties to return via API, id is always required
class UserOut(UserBase):
    id: uuid.UUID