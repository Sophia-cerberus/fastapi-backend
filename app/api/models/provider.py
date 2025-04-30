from typing import Any
from enum import Enum
import uuid

from sqlalchemy.dialects.postgresql import JSONB


from sqlmodel import ARRAY, Column, Field, Relationship, SQLModel, String
from app.core.security import security_manager
from app.api.utils.models import BaseModel


class ModelProviderBase(BaseModel):
    provider_name: str = Field(regex=r"^[a-zA-Z0-9_-]{1,64}$", unique=True)
    base_url: str | None = None
    api_key: str | None = None
    icon: str | None = None
    description: str


class ModelProviderCreate(ModelProviderBase):
    pass


class ModelProviderUpdate(ModelProviderBase):
    provider_name: str | None = Field(regex=r"^[a-zA-Z0-9_-]{1,64}$", default=None, unique=True)  # type: ignore[assignment]
    description: str | None = None
    remark: str | None = None


class ModelProvider(ModelProviderBase, table=True):
    id: uuid.UUID | None = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    provider_name: str = Field(max_length=64)
    base_url: str | None = Field(default=None)
    api_key: str | None = Field(default=None)
    icon: str | None = Field(default=None)
    description: str | None = Field(default=None, max_length=256)

    owner_id: uuid.UUID | None = Field(default=None, foreign_key="user.id", nullable=True)
    team_id: uuid.UUID = Field(foreign_key="team.id", nullable=False)

    @property
    def encrypted_api_key(self) -> str | None:
        """返回加密的API密钥, 用于API响应"""
        if self.api_key:
            return self.api_key  # 已经是加密的
        return None

    @property
    def decrypted_api_key(self) -> str | None:
        """获取解密后的API密钥, 用于内部业务逻辑"""
        if self.api_key:
            return security_manager.decrypt_api_key(self.api_key)
        return None

    def set_api_key(self, value: str | None) -> None:
        """设置并加密API密钥"""
        if value:
            self.api_key = security_manager.encrypt_api_key(value)
        else:
            self.api_key = None

    # Relationship with Model
    models: list["Model"] = Relationship(
        back_populates="provider", cascade_delete="all, delete-orphan"
    )


class ModelCategory(str, Enum):
    LLM = "llm"
    CHAT = "chat"
    TEXT_EMBEDDING = "text-embedding"
    RERANK = "rerank"
    SPEECH_TO_TEXT = "speech-to-text"
    TEXT_TO_SPEECH = "text-to-speech"


class ModelCapability(str, Enum):
    VISION = "vision"


class ModelsBase(BaseModel):
    ai_model_name: str = Field(regex=r"^[a-zA-Z0-9/_:.-]{1,64}$", unique=True)
    provider_id: uuid.UUID
    categories: list[ModelCategory] = Field(sa_column=Column(ARRAY(String)))
    capabilities: list[ModelCapability] = Field(
        sa_column=Column(ARRAY(String)), default=[]
    )


class Model(ModelsBase, table=True):
    id: uuid.UUID | None = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    ai_model_name: str = Field(max_length=128)

    owner_id: uuid.UUID | None = Field(default=None, foreign_key="user.id", nullable=True)
    team_id: uuid.UUID = Field(foreign_key="team.id", nullable=False)

    provider_id: uuid.UUID = Field(foreign_key="modelprovider.id")
    categories: list[ModelCategory] = Field(sa_column=Column(ARRAY(String)))
    capabilities: list[ModelCapability] = Field(
        sa_column=Column(ARRAY(String)), default=[]
    )
    cmetadata: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column("cmetadata", JSONB, nullable=False, server_default="{}"),
    )
    # Relationship with ModelProvider
    provider: ModelProvider = Relationship(back_populates="models")


# Properties to return via API
class ModelProviderOut(SQLModel):
    id: uuid.UUID
    provider_name: str
    base_url: str | None
    api_key: str | None
    icon: str | None
    description: str | None

    class Config:
        from_attributes = True


class ModelOut(SQLModel):
    id: uuid.UUID
    ai_model_name: str
    provider: ModelProviderOut


# 新增一个用于创建模型的请求模型
class ModelCreate(ModelsBase):
    cmetadata: dict[str, Any] | None = None


# 新增一个用于更新模型的请求模型
class ModelUpdate(ModelsBase):
    ai_model_name: str | None = None
    provider_id: int | None = None
    cmetadata: dict[str, Any] | None = None
    remark: str | None = None
