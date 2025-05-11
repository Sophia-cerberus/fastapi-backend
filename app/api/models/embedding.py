from datetime import datetime
from typing import Any
import uuid

from sqlmodel import Field, Index
from app.api.utils.models import BaseModel


class EmbeddingBase(BaseModel):
    document: str | None = Field(default=None)
    cmetadata: dict[Any, Any] = Field(default_factory=dict)


class EmbeddingCreate(EmbeddingBase):
    upload_id: uuid.UUID


class EmbeddingUpdate(EmbeddingBase):
    pass


class Embedding(EmbeddingBase, table=True):
    """Embedding store."""

    id: uuid.UUID | None = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    upload_id: uuid.UUID | None = Field(default=None, foreign_key="upload.id", nullable=False, ondelete="CASCADE")

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


class EmbeddingOut(EmbeddingBase):
    id: uuid.UUID
    upload_id: uuid.UUID
    owner_id: uuid.UUID | None
    team_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
