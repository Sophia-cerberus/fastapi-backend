from enum import IntEnum
from typing import Dict
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy.sql import func


class BaseModel(SQLModel):
    __abstract__ = True
    
    created_at: datetime | None = Field(
        default_factory=datetime.now,  # 添加Python级别默认值
        sa_column_kwargs={"server_default": func.now()},
        nullable=False,
    )
    updated_at: datetime | None = Field(
        default_factory=datetime.now,  # 添加Python级别默认值
        sa_column_kwargs={"server_default": func.now(), "onupdate": func.now()},
        nullable=False,
    )
    remark: str | None = Field(default=None, max_length=256)


class StatusTypes(IntEnum):
    ENABLE = 0
    DISABLE = 1
    EXPIRED = 2
    PENDING = 3
    LOCKED = 4
    HIDDEN = 5

    @property
    def description(self) -> str:
        return self._descriptions()[self]

    @classmethod
    def _descriptions(cls) -> Dict['StatusTypes', str]:
        return {
            cls.ENABLE: "已启用",
            cls.DISABLE: "已禁用",
            cls.EXPIRED: "已过期",
            cls.PENDING: "待处理",
            cls.LOCKED: "已锁定",
            cls.HIDDEN: "已隐藏"
        }

    def __str__(self) -> str:
        return self.description

    def __repr__(self):
        return f"{self.__class__.__name__}.{self.name}"

    @classmethod
    def _missing_(cls, value):
        try:
            # Handle integer values from database
            return cls(int(value))
        except (ValueError, TypeError):
            return None