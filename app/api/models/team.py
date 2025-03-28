from enum import Enum
from typing import Any, Optional
import uuid
from pydantic import model_validator
from sqlmodel import Field, Relationship, SQLModel


class TeamBase(SQLModel):
    name: str = Field(regex=r"^[a-zA-Z0-9_-]{1,64}$")
    description: str | None = None
    # 增加team的图标
    icon: str | None = None


class TeamCreate(TeamBase):
    workflow: str


class TeamUpdate(TeamBase):
    name: str | None = Field(regex=r"^[a-zA-Z0-9_-]{1,64}$", default=None)  # type: ignore[assignment]


class ChatMessageType(str, Enum):
    human = "human"
    ai = "ai"


class ChatMessage(SQLModel):
    type: ChatMessageType
    content: str
    imgdata: str | None = None  # 添加 imgdata 字段


class InterruptType(str, Enum):
    TOOL_REVIEW = "tool_review"
    OUTPUT_REVIEW = "output_review"
    CONTEXT_INPUT = "context_input"


class InterruptDecision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    REPLIED = "replied"
    UPDATE = "update"
    FEEDBACK = "feedback"
    REVIEW = "review"
    EDIT = "edit"
    CONTINUE = "continue"


class Interrupt(SQLModel):
    interaction_type: InterruptType | None = None
    decision: InterruptDecision
    tool_message: str | None = None


class TeamChat(SQLModel):
    messages: list[ChatMessage]
    interrupt: Interrupt | None = None


class TeamChatPublic(SQLModel):
    message: ChatMessage | None = None
    interrupt: Interrupt | None = None

    @model_validator(mode="after")
    def check_either_field(cls: Any, values: Any) -> Any:
        message, interrupt = values.message, values.interrupt
        if not message and not interrupt:
            raise ValueError('Either "message" or "interrupt" must be provided.')
        return values


class Team(TeamBase, table=True):
    id: uuid.UUID | None = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    name: str = Field(regex=r"^[a-zA-Z0-9_-]{1,64}$", unique=True)
    owner_id: uuid.UUID | None = Field(default=None, foreign_key="user.id", nullable=False)
    owner: Optional["User"] | None = Relationship(back_populates="teams") # type: ignore
    members: list["Member"] = Relationship( # type: ignore
        back_populates="belongs", sa_relationship_kwargs={"cascade": "delete"}
    )
    workflow: str  # TODO:
    threads: list["Thread"] = Relationship( # type: ignore
        back_populates="team", sa_relationship_kwargs={"cascade": "delete"}
    )
    graphs: list["Graph"] = Relationship( # type: ignore
        back_populates="team", sa_relationship_kwargs={"cascade": "delete"}
    )
    subgraphs: list["Subgraph"] = Relationship( # type: ignore
        back_populates="team", sa_relationship_kwargs={"cascade": "delete"}
    )
    apikeys: list["ApiKey"] = Relationship( # type: ignore
        back_populates="team", sa_relationship_kwargs={"cascade": "delete"}
    )


# Properties to return via API, id is always required
class TeamOut(TeamBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    workflow: str
