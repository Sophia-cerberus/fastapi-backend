from datetime import datetime
import uuid

from sqlmodel import Field, SQLModel

from app.core.graph.messages import ChatResponse
from app.api.utils.models import BaseModel


class ThreadBase(BaseModel):
    query: str


class ThreadCreate(ThreadBase):
    pass


class ThreadUpdate(ThreadBase):
    query: str | None = None  # type: ignore[assignment]
    remark: str | None = None


class Thread(ThreadBase, table=True):
    id: uuid.UUID | None = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    team_id: uuid.UUID | None = Field(default=None, foreign_key="team.id", nullable=False)
    owner_id: uuid.UUID | None = Field(default=None, foreign_key="user.id", nullable=True)
    

class ThreadOut(SQLModel):
    id: uuid.UUID
    query: str
    updated_at: datetime


class ThreadRead(ThreadOut):
    messages: list[ChatResponse]
