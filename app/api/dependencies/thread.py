from typing import Annotated
import uuid

from fastapi import Depends, HTTPException
from sqlmodel import or_, select
from sqlmodel.sql._expression_select_cls import SelectOfScalar

from app.api.models import Thread, TeamUserJoin, RoleTypes, Team
from app.api.utils.models import StatusTypes

from .session import SessionDep
from .common import CurrentTeamAndUser


async def instance_statement(current_team_and_user: CurrentTeamAndUser) ->  SelectOfScalar[Thread]:
    
    statement = select(Thread)
    if not current_team_and_user.user.is_superuser:
        if current_team_and_user.user.is_tenant_admin:
            statement = statement.join(Team).where(
                Team.tenant_id == current_team_and_user.team.tenant_id
            )
        else:
            statement = statement.join(TeamUserJoin).where(
                TeamUserJoin.user_id == current_team_and_user.user.id,
                TeamUserJoin.status == StatusTypes.ENABLE,
                TeamUserJoin.team_id == current_team_and_user.team.id == Thread.team_id,
            ).where(
                or_(
                    TeamUserJoin.role in [RoleTypes.ADMIN, RoleTypes.MODERATOR, RoleTypes.OWNER],
                    Thread.owner_id == current_team_and_user.user.id
                )
            )      # 限制在当前团队内

    return statement


async def current_instance(
    session: SessionDep, id: uuid.UUID, current_team_and_user: CurrentTeamAndUser
) -> Thread:
    
    statement = await instance_statement(current_team_and_user)
    statement = statement.where(Thread.id == id)

    thread = await session.scalar(statement)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    return thread


InstanceStatement = Annotated[SelectOfScalar[Thread], Depends(instance_statement)]
CurrentInstance = Annotated[Thread, Depends(current_instance)]
