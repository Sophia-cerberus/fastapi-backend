from typing import Annotated
import uuid

from fastapi import Depends, HTTPException, status
from sqlmodel import or_, select
from sqlmodel.sql._expression_select_cls import SelectOfScalar

from app.api.models import ModelProvider, TeamUserJoin, RoleTypes, Team
from app.api.utils.models import StatusTypes

from .session import SessionDep
from .team import CurrentTeamAndUser


async def instance_statement(current_team_and_user: CurrentTeamAndUser) ->  SelectOfScalar[ModelProvider]:
    
    statement: SelectOfScalar[ModelProvider] = select(ModelProvider)
    if not current_team_and_user.user.is_superuser:
        if current_team_and_user.user.is_tenant_admin:
            statement = statement.join(Team).where(
                Team.tenant_id == current_team_and_user.team.tenant_id
            )
        else:
            statement = statement.join(TeamUserJoin).where(
                TeamUserJoin.user_id == current_team_and_user.user.id,
                TeamUserJoin.status == StatusTypes.ENABLE,
                TeamUserJoin.team_id == current_team_and_user.team.id == ModelProvider.team_id  
            ).where(
                or_(
                    TeamUserJoin.role in [RoleTypes.ADMIN, RoleTypes.MODERATOR, RoleTypes.OWNER],
                    ModelProvider.owner_id == current_team_and_user.user.id
                )
            )      # 限制在当前团队内
        
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
