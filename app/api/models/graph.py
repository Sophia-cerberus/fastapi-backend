from datetime import datetime
from typing import Any
import uuid

from sqlalchemy.dialects.postgresql import JSONB

from sqlmodel import Column, DateTime, Field, func
from app.api.utils.models import BaseModel


class GraphBase(BaseModel):
    name: str = Field(regex=r"^[a-zA-Z0-9_-]{1,64}$")
    description: str | None = None
    config: dict[Any, Any] = Field(default_factory=dict, sa_column=Column(JSONB))
    metadata_: dict[Any, Any] = Field(
        default_factory=dict,
        sa_column=Column("metadata", JSONB, nullable=False, server_default="{}"),
    )
    is_public: bool = Field(default=False)  # 是否公开，可供其他用户使用


class GraphCreate(GraphBase):
    created_at: datetime
    updated_at: datetime
    team_id: uuid.UUID
    owner_id: uuid.UUID
    parent: uuid.UUID | None = None


class GraphUpdate(GraphBase):
    name: str | None = None
    updated_at: datetime
    id: uuid.UUID | None = None
    team_id: uuid.UUID | None = None
    parent: uuid.UUID | None = None
    remark: str | None = None


class Graph(GraphBase, table=True):
    id: uuid.UUID | None = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    owner_id: uuid.UUID | None = Field(default=None, foreign_key="user.id", nullable=True)
    team_id: uuid.UUID = Field(foreign_key="team.id", nullable=False)

    parent: uuid.UUID | None = Field(default=None, index=True, foreign_key="graph.id", nullable=True)


class GraphOut(GraphBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    team_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    parent: uuid.UUID

