
from typing import Annotated
import uuid
from fastapi import Depends, HTTPException, status
from sqlmodel import select, or_

from app.api.models import ApiKey, Team
from .team import CurrentTeamAndUser
from .session import SessionDep


async def current_instance(
    session: SessionDep, id: uuid.UUID, current_team_and_user: CurrentTeamAndUser
) -> ApiKey:

    statement = (
        select(ApiKey).where(ApiKey.id == id, ApiKey.team_id == current_team_and_user.team.id)
    )
    if not current_team_and_user.user.is_superuser:
        statement = statement.join(Team).where(
            or_(
                Team.owner_id == current_team_and_user.user.id, 
                ApiKey.owner_id == current_team_and_user.user.id
            )
        )

    if not (apikey := await session.scalar(statement)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Api key not found")
    return apikey


CurrentInstance = Annotated[ApiKey, Depends(current_instance)]


