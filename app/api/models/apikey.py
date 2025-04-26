from datetime import datetime
import uuid

from sqlmodel import Field
from app.api.utils.models import BaseModel



class ApiKeyBase(BaseModel):
    description: str | None = "Default API Key Description"


class ApiKeyCreate(ApiKeyBase):
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

    created_at: datetime | None = Field(
        default_factory=lambda: datetime.now()
    )


class ApiKeyOut(ApiKeyBase):
    id: uuid.UUID | None = Field(default=None, primary_key=True)
    key: str
    created_at: datetime


class ApiKeyOutPublic(ApiKeyBase):
    id: uuid.UUID
    short_key: str
    created_at: datetime
