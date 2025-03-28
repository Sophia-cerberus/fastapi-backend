import uuid

from enum import Enum
from typing import Any, Optional
from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint, JSON, Column
from sqlmodel import Enum as SQLEnum


class MemberSkillsLink(SQLModel, table=True):
    member_id: uuid.UUID | None = Field(
        default=None, foreign_key="member.id", primary_key=True
    )
    skill_id: uuid.UUID | None = Field(default=None, foreign_key="skill.id", primary_key=True)


class MemberUploadsLink(SQLModel, table=True):
    member_id: uuid.UUID | None = Field(
        default=None, foreign_key="member.id", primary_key=True
    )
    upload_id: uuid.UUID | None = Field(
        default=None, foreign_key="upload.id", primary_key=True
    )


class MemberBase(SQLModel):
    name: str = Field(regex=r"^[a-zA-Z0-9_-]{1,64}$")
    backstory: str | None = None
    role: str
    type: str  # one of: leader, worker, freelancer
    owner_of: int | None = None
    position_x: float
    position_y: float
    source: int | None = None
    provider: str = ""
    model: str = ""

    temperature: float = 0.1
    interrupt: bool = False


class MemberCreate(MemberBase):
    pass


class MemberUpdate(MemberBase):
    name: str | None = Field(regex=r"^[a-zA-Z0-9_-]{1,64}$", default=None)  # type: ignore[assignment]
    backstory: str | None = None
    role: str | None = None  # type: ignore[assignment]
    type: str | None = None  # type: ignore[assignment]
    belongs_to: uuid.UUID | None = None
    position_x: float | None = None  # type: ignore[assignment]
    position_y: float | None = None  # type: ignore[assignment]
    provider: str | None = None  # type: ignore[assignment]
    model: str | None = None  # type: ignore[assignment]

    temperature: float | None = None  # type: ignore[assignment]
    interrupt: bool | None = None  # type: ignore[assignment]


class Member(MemberBase, table=True):
    __table_args__ = (
        UniqueConstraint("name", "belongs_to", name="unique_team_and_name"),
    )
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    belongs_to: uuid.UUID = Field(foreign_key="team.id", nullable=False)
    belongs: Optional["Team"] | None = Relationship(back_populates="members") # type: ignore
    skills: list["Skill"] = Relationship( # type: ignore
        back_populates="members",
        link_model=MemberSkillsLink,
    )
    uploads: list["Upload"] = Relationship( # type: ignore
        back_populates="members",
        link_model=MemberUploadsLink,
    )


class MemberOut(MemberBase):
    id: uuid.UUID
    belongs_to: uuid.UUID
    owner_of: int | None


class SkillBase(SQLModel):
    name: str
    description: str
    display_name: str | None = None
    managed: bool = False
    tool_definition: dict[str, Any] | None = Field(
        default_factory=dict, sa_column=Column(JSON)
    )
    input_parameters: dict[str, Any] | None = Field(
        default_factory=dict, sa_column=Column(JSON)  # 用于存储输入参数
    )
    credentials: dict[str, Any] | None = Field(
        default_factory=dict, sa_column=Column(JSON)  # 新增字段,用于存储凭证信息
    )


class SkillCreate(SkillBase):
    tool_definition: dict[str, Any]  # Tool definition is required if not managed
    managed: bool = Field(default=False, const=False)  # Managed must be False
    credentials: dict[str, Any] | None = None  # 新增字段


class SkillUpdate(SkillBase):
    name: str | None = None  # type: ignore[assignment]
    description: str | None = None  # type: ignore[assignment]
    managed: bool | None = None  # type: ignore[assignment]
    tool_definition: dict[str, Any] | None = None
    credentials: dict[str, Any] | None = None  # 新增字段


class Skill(SkillBase, table=True):
    id: uuid.UUID | None = Field(default=None, primary_key=True)
    members: list["Member"] = Relationship( # type: ignore
        back_populates="skills",
        link_model=MemberSkillsLink, # type: ignore
    )
    owner_id: uuid.UUID | None = Field(default=None, foreign_key="user.id", nullable=False)
    owner: Optional["User"] | None = Relationship(back_populates="skills") # type: ignore


class SkillOut(SkillBase):
    id: uuid.UUID


class ToolDefinitionValidate(SQLModel):
    tool_definition: dict[str, Any]


class UploadBase(SQLModel):
    name: str
    description: str
    file_type: str  # 新字段，用于储文件类型
    web_url: str | None = None  # 新增字段，用于存储网页 URL


class UploadCreate(UploadBase):
    chunk_size: int
    chunk_overlap: int


class UploadUpdate(UploadBase):
    name: str | None = None
    description: str | None = None
    last_modified: datetime
    file_type: str | None = None
    web_url: str | None = None
    chunk_size: int | None = None
    chunk_overlap: int | None = None


class UploadStatus(str, Enum):
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    FAILED = "Failed"


class Upload(UploadBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID | None = Field(default=None, foreign_key="user.id", nullable=False)
    owner: Optional["User"] | None = Relationship(back_populates="uploads") # type: ignore
    members: list["Member"] = Relationship( # type: ignore
        back_populates="uploads",
        link_model=MemberUploadsLink, # type: ignore
    )
    last_modified: datetime = Field(default_factory=lambda: datetime.now())
    status: UploadStatus = Field(
        sa_column=Column(SQLEnum(UploadStatus), nullable=False)
    )
    chunk_size: int
    chunk_overlap: int


class UploadOut(UploadBase):
    id: uuid.UUID
    name: str
    last_modified: datetime
    status: UploadStatus
    owner_id: uuid.UUID | None = Field(default=None, foreign_key="user.id", nullable=False)
    file_type: str
    web_url: str | None
    chunk_size: int
    chunk_overlap: int