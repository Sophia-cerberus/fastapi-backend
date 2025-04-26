import uuid
from datetime import datetime
from enum import IntEnum
from typing import Dict
from pydantic import EmailStr
from sqlmodel import Field, SQLModel, UniqueConstraint
from app.api.utils.models import StatusTypes, BaseModel


class RoleTypes(IntEnum):
    MEMBER = 0      # 普通成员
    MODERATOR = 1   # 管理员
    ADMIN = 2       # 超级管理员
    OWNER = 3       # 拥有者

    @property
    def description(self) -> str:
        return self._descriptions()[self]

    @classmethod
    def _descriptions(cls) -> Dict['RoleTypes', str]:
        return {
            cls.MEMBER: "普通成员",
            cls.MODERATOR: "管理员",
            cls.ADMIN: "超级管理员", 
            cls.OWNER: "拥有者"
        }

    def __str__(self) -> str:
        return self.description

    def __repr__(self):
        return f"{self.__class__.__name__}.{self.name}"

    @classmethod
    def _missing_(cls, value):
        try:
            return cls(int(value))
        except (ValueError, TypeError):
            return None


class UserBase(BaseModel):
    email: EmailStr = Field(unique=True, index=True)
    phone: str = Field(unique=True, index=True)
    avatar: str = Field(default="https://www.gravatar.com/avatar/default?d=mp")

    status: StatusTypes = Field(default=StatusTypes.ENABLE)

    is_superuser: bool = False
    full_name: str | None = None
    language: str = Field(default="en-US")
    dictionaries: uuid.UUID | None = Field(default=None, foreign_key="dictionaries.id")

    # New business-related fields
    corporate_name: str | None = Field(default=None)
    industry_affiliation: str | None = Field(default=None)
    business_scenarios: str | None = Field(default=None)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str


class UserRegister(SQLModel):
    email: EmailStr
    phone: str | None = None
    password: str
    full_name: str | None = None


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = None  # type: ignore
    phone: str | None = None
    password: str | None = None


class UserUpdateMe(SQLModel):
    full_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    avatar: str | None = None

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


class InviteCodes(SQLModel, table=True):
    __tablename__ = "invite_codes"
    __table_args__ = (
        UniqueConstraint("code", name="unique_invite_code"),
    )

    id: uuid.UUID | None = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    code: str = Field(unique=True)
    expires_at: datetime | None = Field(default=None)
    status: StatusTypes = Field(default=StatusTypes.ENABLE)


class TeamUserJoin(SQLModel, table=True):
    __tablename__ = "team_user_join"
    __table_args__ = (
        UniqueConstraint("team_id", "user_id", name="unique_team_user"),
    )
    
    id: uuid.UUID | None = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    team_id: uuid.UUID = Field(foreign_key="team.id", index=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    role: RoleTypes = Field(default=RoleTypes.MEMBER)
    status: StatusTypes = Field(default=StatusTypes.ENABLE)
    invite_by: uuid.UUID = Field(foreign_key="user.id", description="The ID of the user who sent the invitation")
    invite_code: uuid.UUID = Field(foreign_key="invite_codes.id")

    # Additional team-specific settings
    notifications_enabled: bool = Field(default=True)
    is_visible: bool = Field(default=True)
    custom_title: str | None = Field(default=None)

