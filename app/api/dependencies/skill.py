from typing import Annotated
import uuid

from fastapi import Depends, HTTPException

from app.api.models import Skill

from .session import SessionDep
from .user import CurrentUser


async def validate_on_read(
    session: SessionDep, id: uuid.UUID, current_user: CurrentUser
) -> Skill:
    
    skill = await session.get(Skill, id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    if not current_user.is_superuser and (skill.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return skill


ValidateOnRead = Annotated[Skill, Depends(validate_on_read)]