import uuid
from enum import IntEnum
from typing import Dict

from sqlmodel import Field, SQLModel
from app.api.utils.models import BaseModel, StatusTypes


class TenantPlan(IntEnum):
    FREE = 0
    BASIC = 1
    PROFESSIONAL = 2
    ENTERPRISE = 3

    @property
    def description(self) -> str:
        return self._descriptions()[self]

    @classmethod
    def _descriptions(cls) -> Dict['TenantPlan', str]:
        return {
            cls.FREE: "免费版",
            cls.BASIC: "基础版",
            cls.PROFESSIONAL: "专业版",
            cls.ENTERPRISE: "企业版"
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


class TenantBase(BaseModel):
    name: str = Field(unique=True, index=True, nullable=False)
    plan: TenantPlan = Field(default=TenantPlan.FREE)
    status: StatusTypes = Field(default=StatusTypes.ENABLE)
    dictionaries: uuid.UUID | None = Field(default=None, foreign_key="dictionaries.id")
    description: str | None = Field(default=None, max_length=256)
    max_users: int = Field(default=5)
    max_teams: int = Field(default=1)
    max_storage_gb: float = Field(default=1.0)


class TenantCreate(TenantBase):
    pass


class TenantUpdate(SQLModel):
    name: str | None = None
    plan: TenantPlan | None = None
    status: StatusTypes | None = None
    description: str | None = None
    max_users: int | None = None
    max_teams: int | None = None
    max_storage_gb: float | None = None


class Tenant(TenantBase, table=True):
    id: uuid.UUID | None = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )

# Properties to return via API
class TenantOut(TenantBase):
    id: uuid.UUID

