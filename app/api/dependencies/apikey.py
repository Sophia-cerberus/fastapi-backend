
from typing import Annotated
import uuid
from fastapi import Depends, HTTPException, status
from sqlmodel import or_, select
from sqlmodel.sql._expression_select_cls import SelectOfScalar

from app.api.models import ApiKey, TeamUserJoin, RoleTypes, Team
from app.api.utils.models import StatusTypes
from .common import CurrentTeamAndUser
from .session import SessionDep



async def instance_statement(current_team_and_user: CurrentTeamAndUser) ->  SelectOfScalar[ApiKey]:
    
    statement: SelectOfScalar[ApiKey] = select(ApiKey)
    if not current_team_and_user.user.is_superuser:
        if current_team_and_user.user.is_tenant_admin:
            statement = statement.join(Team).where(
                Team.tenant_id == current_team_and_user.team.tenant_id
            )
        else:
            statement = statement.join(TeamUserJoin).where(
                TeamUserJoin.user_id == current_team_and_user.user.id,
                TeamUserJoin.status == StatusTypes.ENABLE,
                TeamUserJoin.team_id == current_team_and_user.team.id == ApiKey.team_id,
            ).where(
                or_(
                    TeamUserJoin.role in [RoleTypes.ADMIN, RoleTypes.MODERATOR, RoleTypes.OWNER],
                    ApiKey.owner_id == current_team_and_user.user.id       # 其他用户只能访问自己的ApiKey
                )
            )     
    return statement


async def current_instance(
    session: SessionDep, id: uuid.UUID, current_team_and_user: CurrentTeamAndUser
) -> ApiKey:

    statement = await instance_statement(current_team_and_user)
    statement = statement.where(ApiKey.id == id)

    if not (apikey := await session.scalar(statement)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Api key not found")
    return apikey


InstanceStatement = Annotated[SelectOfScalar[ApiKey], Depends(instance_statement)]
CurrentInstance = Annotated[ApiKey, Depends(current_instance)]


