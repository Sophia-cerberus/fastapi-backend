from datetime import datetime
from typing import Any
import uuid

from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field, Index, SQLModel


class UploadBase(SQLModel):
    description: str


class UploadCreate(UploadBase):
    chunk_size: int
    chunk_overlap: int


class UploadUpdate(UploadBase):
    description: str | None = None
    chunk_size: int | None = None
    chunk_overlap: int | None = None
    last_modified: datetime


class Upload(UploadBase, table=True):
    id: uuid.UUID | None = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    name: str

    owner_id: uuid.UUID | None = Field(default=None, foreign_key="user.id", nullable=True)
    team_id: uuid.UUID | None = Field(default=None, foreign_key="team.id", nullable=False)

    last_modified: datetime = Field(default_factory=lambda: datetime.now(), nullable=False)
    status: bool = Field(default=False, nullable=False)
    chunk_size: int = Field(nullable=False)
    chunk_overlap: int = Field(nullable=False)
    file_type: str = Field(nullable=False)
    file_path: str = Field(nullable=False)
    file_size: float = Field(nullable=False)


class UploadOut(UploadBase):
    id: uuid.UUID
    name: str
    last_modified: datetime
    owner_id: uuid.UUID | None = Field(default=None, foreign_key="user.id", nullable=True)
    file_type: str
    file_path: str
    file_size: float
    chunk_size: int
    chunk_overlap: int



class Embedding(SQLModel, table=True):
    """Embedding store."""

    id: uuid.UUID | None = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )

    upload_id: uuid.UUID | None = Field(default=None, foreign_key="upload.id", nullable=False, ondelete="CASCADE")

    document: str = Field(nullable=True)
    cmetadata: dict[Any, Any] = Field(default_factory=dict, sa_column=Column(JSONB))

    owner_id: uuid.UUID | None = Field(foreign_key="user.id", nullable=False)

    team_id: uuid.UUID = Field(foreign_key="team.id", nullable=False)


    __table_args__ = (
        Index(
            "ix_metadata_gin",
            "cmetadata",
            postgresql_using="gin",
            postgresql_ops={"cmetadata": "jsonb_path_ops"},
        ),
    )
