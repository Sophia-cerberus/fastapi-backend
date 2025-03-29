from typing import Annotated
import uuid

from fastapi import Depends, HTTPException
from sqlmodel import or_, select

from app.api.models import Upload, Team

from .session import SessionDep
from .team import CurrentTeamAndUser


async def current_instance(
    session: SessionDep, id: uuid.UUID, current_team_and_user: CurrentTeamAndUser
) -> Upload:
    
    statement = select(Upload).where(
        Upload.id == id, Upload.team_id == current_team_and_user.team.id
    )
    if not current_team_and_user.user.is_superuser:
        statement = statement.join(Upload).where(
            or_(
                Upload.owner_id == current_team_and_user.user.id, 
                Team.owner_id == current_team_and_user.user.id,
            )
        )
    upload = await session.scalar(statement)
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    return upload


CurrentInstance = Annotated[Upload, Depends(current_instance)]