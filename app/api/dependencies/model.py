from typing import Annotated
import uuid

from fastapi import Depends, HTTPException

from app.api.models import Models

from .session import SessionDep
from .user import CurrentUser


async def validate_on_read(
    session: SessionDep, id: uuid.UUID, _: CurrentUser
) -> Models:
    
    instance = await session.get(Models, id)
    if not instance:
        raise HTTPException(
            status_code=404,
            detail="The provider with this ID does not exist in the system",
        )
    return instance


ValidateOnRead = Annotated[Models, Depends(validate_on_read)]