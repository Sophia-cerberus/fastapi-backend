import uuid
from typing import Optional
from datetime import datetime
from sqlmodel import DateTime, Field, Relationship, SQLModel, Column, func

from app.core.graph.messages import ChatResponse


class ThreadBase(SQLModel):
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
    team: Optional["Team"] | None = Relationship(back_populates="threads") # type: ignore

    owner_id: uuid.UUID | None = Field(default=None, foreign_key="user.id", nullable=False)
    owner: Optional["User"] | None = Relationship(back_populates="threads") # type: ignore

    checkpoints: list["Checkpoint"] = Relationship( # type: ignore
        back_populates="thread", sa_relationship_kwargs={"cascade": "delete"}
    )
    checkpoint_blobs: list["CheckpointBlobs"] = Relationship( # type: ignore
        back_populates="thread", sa_relationship_kwargs={"cascade": "delete"}
    )

    writes: list["Write"] = Relationship( # type: ignore
        back_populates="thread", sa_relationship_kwargs={"cascade": "delete"}
    )


class ThreadOut(SQLModel):
    id: uuid.UUID
    query: str
    updated_at: datetime


class ThreadRead(ThreadOut):
    messages: list[ChatResponse]
