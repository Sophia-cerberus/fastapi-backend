import uuid

from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint


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
    team_id: uuid.UUID | None = None
    position_x: float | None = None  # type: ignore[assignment]
    position_y: float | None = None  # type: ignore[assignment]
    provider: str | None = None  # type: ignore[assignment]
    model: str | None = None  # type: ignore[assignment]

    temperature: float | None = None  # type: ignore[assignment]
    interrupt: bool | None = None  # type: ignore[assignment]


class Member(MemberBase, table=True):
    __table_args__ = (
        UniqueConstraint("name", "team_id", name="unique_team_and_name"),
    )
    id: uuid.UUID | None = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    team_id: uuid.UUID | None = Field(default=None, foreign_key="team.id", nullable=False)
    owner_id: uuid.UUID | None = Field(default=None, foreign_key="user.id", nullable=True)


class MemberOut(MemberBase):
    id: uuid.UUID
    team_id: uuid.UUID
    owner_id: uuid.UUID | None