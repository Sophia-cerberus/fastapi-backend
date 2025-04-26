from typing import Any, Optional
import uuid

from sqlmodel import JSON, Column, Field, Relationship, SQLModel


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
    id: uuid.UUID | None = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )

    owner_id: uuid.UUID | None = Field(default=None, foreign_key="user.id", nullable=True)
    team_id: uuid.UUID = Field(foreign_key="team.id", nullable=False)

    is_public: Optional[bool] = Field(default=False, nullable=False)


class SkillOut(SkillBase):
    id: uuid.UUID


class ToolDefinitionValidate(SQLModel):
    tool_definition: dict[str, Any]