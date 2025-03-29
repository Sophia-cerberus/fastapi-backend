
from typing import Annotated, Any
import uuid
from fastapi import Depends, HTTPException, status
from sqlmodel import or_, select
from sqlmodel.sql._expression_select_cls import SelectOfScalar

from app.api.models import ApiKey, Team
from .team import CurrentTeamAndUser
from .session import SessionDep


async def instance_statement(current_team_and_user: CurrentTeamAndUser) ->  SelectOfScalar[ApiKey]:
    
    statement = select(ApiKey)
    if not current_team_and_user.user.is_superuser:
        statement = statement.join(Team).where(
            or_(
                Team.owner_id == current_team_and_user.user.id,        # Team owner可以访问整个Team的ApiKey
                ApiKey.owner_id == current_team_and_user.user.id       # 其他用户只能访问自己的ApiKey
            )
        ).where(ApiKey.team_id == current_team_and_user.team.id)      # 限制在当前团队内
    return statement


async def current_instance(
    session: SessionDep, id: uuid.UUID, current_team_and_user: CurrentTeamAndUser
) -> ApiKey:

    statement = await instance_statement(current_team_and_user)
    statement = statement.where(ApiKey.id == id)

    if not (apikey := await session.scalar(statement)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Api key not found")
    return apikey


InstanceStatement = Annotated[ApiKey, Depends(instance_statement)]
CurrentInstance = Annotated[ApiKey, Depends(current_instance)]


