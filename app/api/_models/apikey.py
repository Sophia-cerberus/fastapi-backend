from datetime import datetime
from typing import Optional
import uuid
from zoneinfo import ZoneInfo
from sqlmodel import Field, Relationship, SQLModel


class ApiKeyBase(SQLModel):
    description: str | None = "Default API Key Description"


class ApiKeyCreate(ApiKeyBase):
    pass


class ApiKey(ApiKeyBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_key: str
    short_key: str
    
    team_id: uuid.UUID | None = Field(default=None, foreign_key="team.id", nullable=False)
    team: Optional["Team"] | None = Relationship(back_populates="apikeys") # type: ignore
    
    owner_id: uuid.UUID | None = Field(default=None, foreign_key="user.id", nullable=False)
    owner: Optional["User"] | None = Relationship(back_populates="apikeys") # type: ignore

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