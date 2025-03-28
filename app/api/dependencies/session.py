from typing import Annotated
from collections.abc import  AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.core.db import engine


async def get_db() -> AsyncGenerator[AsyncSession, None, None]:
    async with AsyncSession(engine) as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_db)]