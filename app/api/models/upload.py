from datetime import datetime
import uuid

from sqlmodel import Field
from app.api.utils.models import BaseModel, StatusTypes


class UploadBase(BaseModel):
    description: str


class UploadCreate(UploadBase):
    dataset_id: uuid.UUID


class UploadUpdate(UploadBase):
    description: str | None = None
    update_at: datetime
    remark: str | None = None


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
    dataset_id: uuid.UUID = Field(foreign_key="dataset.id", nullable=False)

    status: StatusTypes = Field(default=StatusTypes.ENABLE)
    file_type: str = Field(nullable=False)
    file_path: str = Field(nullable=False)
    file_size: float = Field(nullable=False)


class UploadOut(UploadBase):
    id: uuid.UUID
    name: str
    update_at: datetime
    owner_id: uuid.UUID
    file_type: str
    file_path: str
    file_size: float
