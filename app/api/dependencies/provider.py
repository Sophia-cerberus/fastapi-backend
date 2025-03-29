from typing import Annotated
import uuid

from fastapi import Depends, HTTPException, status
from sqlmodel import or_, select

from app.api.models import ModelProvider, Team

from .session import SessionDep
from .team import CurrentTeamAndUser


async def current_instance(
    session: SessionDep, id: uuid.UUID, current_team_and_user: CurrentTeamAndUser
) -> ModelProvider:
    
    statement = (
        select(ModelProvider).where(ModelProvider.team_id == current_team_and_user.team.id, ModelProvider.id == id)
    )
    if not current_team_and_user.user.is_superuser:
        statement = statement.join(ModelProvider).where(
            or_(
                ModelProvider.owner_id == current_team_and_user.user.id, 
                Team.owner_id == current_team_and_user.user.id,
            )
        )
    if not (provider := await session.scalar(statement)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="provider not found")
    return provider


CurrentInstance = Annotated[ModelProvider, Depends(current_instance)]
