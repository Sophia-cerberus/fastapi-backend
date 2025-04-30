import uuid

from sqlmodel import Field, SQLModel
from app.api.utils.models import BaseModel, StatusTypes


class DictionaryBase(BaseModel):
    name: str = Field(unique=True, index=True)
    status: StatusTypes = Field(default=StatusTypes.ENABLE)
    description: str | None = None


# Properties to receive via API on creation
class DictionaryCreate(DictionaryBase):
    pass


# Properties to receive via API on update, all are optional
class DictionaryUpdate(SQLModel):
    name: str | None = None
    status: StatusTypes | None = None
    description: str | None = None


# Database model, database table inferred from class name
class Dictionary(DictionaryBase, table=True):
    __tablename__ = "dictionaries"

    id: uuid.UUID | None = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )


# Properties to return via API, id is always required
class DictionaryOut(DictionaryBase):
    id: uuid.UUID


# Dictionary Argument Models
class DictionaryArgumentBase(BaseModel):
    label: str = Field(max_length=64)
    value: str = Field(max_length=256)
    is_default: bool = Field(default=False)
    status: StatusTypes = Field(default=StatusTypes.ENABLE)
    sort: int = Field(max_length=256)
    dict_id: uuid.UUID = Field(foreign_key="dictionaries.id")


class DictionaryArgumentCreate(DictionaryArgumentBase):
    pass


class DictionaryArgumentUpdate(SQLModel):
    label: str | None = None
    value: str | None = None
    is_default: bool | None = None
    status: StatusTypes | None = None
    sort: int | None = None
    remark: str | None = None


class DictionaryArgument(DictionaryArgumentBase, table=True):
    __tablename__ = "dictionary_arguments"

    id: uuid.UUID | None = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )


class DictionaryArgumentOut(DictionaryArgumentBase):
    id: uuid.UUID