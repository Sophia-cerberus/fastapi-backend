from datetime import datetime
import uuid

from sqlmodel import Field
from app.api.utils.models import BaseModel, StatusTypes



class ApiKeyBase(BaseModel):
    description: str | None = "Default API Key Description"
    status: StatusTypes = Field(default=StatusTypes.ENABLE)


class ApiKeyCreate(ApiKeyBase):
    pass


class ApiKeyUpdate(ApiKeyBase):
    pass


class ApiKey(ApiKeyBase, table=True):
    id: uuid.UUID | None = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    hashed_key: str
    short_key: str
    team_id: uuid.UUID | None = Field(default=None, foreign_key="team.id", nullable=False)
    owner_id: uuid.UUID | None = Field(default=None, foreign_key="user.id", nullable=True)


class ApiKeyOut(ApiKeyBase):
    id: uuid.UUID | None = Field(default=None, primary_key=True)
    key: str
    created_at: datetime
    description: str | None = None
    status: StatusTypes


class ApiKeyOutPublic(ApiKeyBase):
    id: uuid.UUID
    short_key: str
    created_at: datetime
    description: str | None = None
    status: StatusTypes
