from datetime import datetime
from typing import Any
import uuid

from sqlalchemy.dialects.postgresql import JSONB

from sqlmodel import Column, DateTime, Field, PrimaryKeyConstraint, SQLModel, String, func
from app.api.utils.models import BaseModel



class Checkpoint(BaseModel, table=True):
    __tablename__ = "checkpoints"
    __table_args__ = (
        PrimaryKeyConstraint("thread_id", "checkpoint_id", "checkpoint_ns"),
    )
    thread_id: uuid.UUID = Field(foreign_key="thread.id", primary_key=True)
    checkpoint_ns: str = Field(
        sa_column=Column(
            "checkpoint_ns", String, nullable=False, server_default="", primary_key=True
        ),
    )
    checkpoint_id: uuid.UUID = Field(primary_key=True)
    parent_checkpoint_id: uuid.UUID | None
    type: str | None
    checkpoint: dict[Any, Any] = Field(default_factory=dict, sa_column=Column(JSONB))
    metadata_: dict[Any, Any] = Field(
        default_factory=dict,
        sa_column=Column("metadata", JSONB, nullable=False, server_default="{}"),
    )
    created_at: datetime | None = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            default=func.now(),
            server_default=func.now(),
        )
    )


class CheckpointBlobs(BaseModel, table=True):
    __tablename__ = "checkpoint_blobs"
    __table_args__ = (
        PrimaryKeyConstraint("thread_id", "checkpoint_ns", "channel", "version"),
    )
    thread_id: uuid.UUID = Field(foreign_key="thread.id", primary_key=True)
    checkpoint_ns: str = Field(
        sa_column=Column(
            "checkpoint_ns", String, nullable=False, server_default="", primary_key=True
        ),
    )
    channel: str = Field(primary_key=True)
    version: str = Field(primary_key=True)
    type: str
    blob: bytes | None


class CheckpointOut(SQLModel):
    thread_id: uuid.UUID
    checkpoint_id: uuid.UUID
    checkpoint: bytes
    created_at: datetime


class Write(BaseModel, table=True):
    __tablename__ = "checkpoint_writes"
    __table_args__ = (
        PrimaryKeyConstraint(
            "thread_id", "checkpoint_ns", "checkpoint_id", "task_id", "idx"
        ),
    )
    thread_id: uuid.UUID = Field(foreign_key="thread.id", primary_key=True)
    checkpoint_ns: str = Field(
        sa_column=Column(
            "checkpoint_ns", String, nullable=False, server_default="", primary_key=True
        ),
    )
    checkpoint_id: uuid.UUID = Field(primary_key=True)
    task_id: uuid.UUID = Field(primary_key=True)
    idx: int = Field(primary_key=True)
    channel: str
    type: str | None
    blob: bytes

