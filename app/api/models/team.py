import uuid

from sqlmodel import Field
from app.api.utils.models import BaseModel


class TeamBase(BaseModel):
    name: str = Field(regex=r"^[a-zA-Z0-9_-]{1,64}$")
    description: str | None = None
    # 增加team的图标
    icon: str | None = None


class TeamCreate(TeamBase):
    pass


class TeamUpdate(TeamBase):
    name: str | None = Field(regex=r"^[a-zA-Z0-9_-]{1,64}$", default=None)  # type: ignore[assignment]
    remark: str | None = None


class Team(TeamBase, table=True):
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    name: str = Field(regex=r"^[a-zA-Z0-9_-]{1,64}$", unique=True)
    tenant_id: uuid.UUID = Field(foreign_key="tenant.id", nullable=True)


# Properties to return via API, id is always required
class TeamOut(TeamBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
