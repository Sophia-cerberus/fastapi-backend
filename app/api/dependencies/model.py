from typing import Annotated
import uuid

from fastapi import Depends, HTTPException, status
from sqlmodel import or_, select

from app.api.models import Model, Team
from app.core.config import settings

from .session import SessionDep
from .team import CurrentTeamAndUser


async def current_instance(
    session: SessionDep, id: uuid.UUID, current_team_and_user: CurrentTeamAndUser
) -> Model:
    
    statement = (
        select(Model).where(Model.team_id == current_team_and_user.team.id, Model.id == id)
    )
    if not current_team_and_user.user.is_superuser:
        statement = statement.join(Model).where(
            or_(
                Model.owner_id == current_team_and_user.user.id, 
                Team.owner_id == current_team_and_user.user.id,
            )
        )
    if not (model := await session.scalar(statement)):
        raise HTTPException(status_code=404, detail="Model not found")
    return model


async def validate_update_in(
    session: SessionDep,  ai_model_in: Model, id: uuid.UUID, current_team_and_user: CurrentTeamAndUser
) -> None:

    if ai_model_in.name in settings.PROTECTED_NAMES:
        raise HTTPException(
            status_code=409, detail="Name is a protected name. Choose another name."
        )
    statement = select(Model).where(
        Model.ai_model_name == ai_model_in.ai_model_name, Model.id != id,
        Model.team_id == current_team_and_user.team.id,
    )
    if await session.scalar(statement):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Model name already exists")
    
    return await current_instance(session=session, id=id, current_team_and_user=current_team_and_user)


CurrentInstance = Annotated[Model, Depends(current_instance)]
ValidateUpdateIn = Annotated[Model, Depends(validate_update_in)]
