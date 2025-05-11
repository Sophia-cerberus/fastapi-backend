from datetime import datetime
from typing import Any
import uuid

from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field, Index
from app.api.utils.models import BaseModel, StatusTypes


class DatasetBase(BaseModel):
    name: str = Field(index=True)
    description: str | None = Field(default=None, max_length=256)
    status: StatusTypes = Field(default=StatusTypes.ENABLE)
    cmetadata: dict[Any, Any] = Field(default_factory=dict, sa_column=Column(JSONB))


class DatasetCreate(DatasetBase):
    parent_id: uuid.UUID | None = None


class DatasetUpdate(DatasetBase):
    name: str | None = None
    description: str | None = None
    status: StatusTypes | None = None
    cmetadata: dict[Any, Any] | None = None
    parent_id: uuid.UUID | None = None
    remark: str | None = None


class Dataset(DatasetBase, table=True):
    """Dataset for knowledge base management with recursive tree structure."""

    id: uuid.UUID | None = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    
    team_id: uuid.UUID = Field(foreign_key="team.id", nullable=False)
    owner_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    # Self-referential relationship for tree structure
    parent_id: uuid.UUID | None = Field(default=None, foreign_key="dataset.id", nullable=True)

    __table_args__ = (
        Index(
            "ix_dataset_cmetadata_gin",
            "cmetadata",
            postgresql_using="gin",
            postgresql_ops={"cmetadata": "jsonb_path_ops"},
        ),
    )


class DatasetOut(DatasetBase):
    id: uuid.UUID
    name: str
    description: str | None
    status: StatusTypes
    team_id: uuid.UUID
    owner_id: uuid.UUID
    parent_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
