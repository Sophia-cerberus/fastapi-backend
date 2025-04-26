from datetime import datetime
import uuid

from sqlmodel import Column, DateTime, Field, SQLModel, func

from app.core.graph.messages import ChatResponse
from app.api.utils.models import BaseModel


class ThreadBase(BaseModel):
    query: str


class ThreadCreate(ThreadBase):
    pass


class ThreadUpdate(ThreadBase):
    query: str | None = None  # type: ignore[assignment]
    updated_at: datetime | None = None


class Thread(ThreadBase, table=True):
    id: uuid.UUID | None = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
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
    team_id: uuid.UUID | None = Field(default=None, foreign_key="team.id", nullable=False)
    owner_id: uuid.UUID | None = Field(default=None, foreign_key="user.id", nullable=True)
    

class ThreadOut(SQLModel):
    id: uuid.UUID
    query: str
    updated_at: datetime


class ThreadRead(ThreadOut):
    messages: list[ChatResponse]
