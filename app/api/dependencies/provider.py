from typing import Annotated
import uuid

from fastapi import Depends, HTTPException, status
from sqlmodel import case, or_, select
from sqlmodel.sql._expression_select_cls import SelectOfScalar

from app.api.models import ModelProvider, Team

from .session import SessionDep
from .team import CurrentTeamAndUser


async def instance_statement(current_team_and_user: CurrentTeamAndUser) ->  SelectOfScalar[ModelProvider]:
    
    statement = select(ModelProvider)
    if not current_team_and_user.user.is_superuser:
        statement = statement.join(Team).where(
            or_(
                Team.owner_id == current_team_and_user.user.id,        # Team owner可以访问整个Team的ApiKey
                ModelProvider.owner_id == current_team_and_user.user.id       # 其他用户只能访问自己的ApiKey
            )
        ).where(ModelProvider.team_id == current_team_and_user.team.id)      # 限制在当前团队内
        
    return statement


async def current_instance(
    session: SessionDep, id: uuid.UUID, current_team_and_user: CurrentTeamAndUser
) -> ModelProvider:
    
    statement = await instance_statement(current_team_and_user)
    statement = statement.where(ModelProvider.id == id)

    if not (provider := await session.scalar(statement)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="provider not found")
    return provider


InstanceStatement = Annotated[SelectOfScalar[ModelProvider], Depends(instance_statement)]
CurrentInstance = Annotated[ModelProvider, Depends(current_instance)]
