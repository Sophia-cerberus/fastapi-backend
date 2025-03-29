from datetime import datetime
from typing import Any, Optional
import uuid
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, func
from sqlalchemy.dialects.postgresql import JSONB


class GraphBase(SQLModel):
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


class GraphUpdate(GraphBase):
    name: str | None = None
    updated_at: datetime


class Graph(GraphBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID | None = Field(default=None, foreign_key="user.id", nullable=False)
    owner: Optional["User"] | None = Relationship(back_populates="graphs") # type: ignore
    team_id: uuid.UUID = Field(foreign_key="team.id", nullable=False)
    team: Optional["Team"] = Relationship(back_populates="graphs") # type: ignore
    created_at: datetime | None = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            default=func.now(),
            server_default=func.now(),
        )
    )
    updated_at: datetime | None = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            default=func.now(),
            onupdate=func.now(),
            server_default=func.now(),
        )
    )


class GraphOut(GraphBase):
    id: uuid.UUID
