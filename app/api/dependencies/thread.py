from typing import Annotated
import uuid

from fastapi import Depends, HTTPException
from sqlmodel import or_, select
from sqlmodel.sql._expression_select_cls import SelectOfScalar

from app.api.models import Thread, Team

from .session import SessionDep
from .team import CurrentTeamAndUser


async def instance_statement(current_team_and_user: CurrentTeamAndUser) ->  SelectOfScalar[Thread]:
    
    statement = select(Thread)
    if not current_team_and_user.user.is_superuser:
        statement = statement.join(Team).where(
            or_(
                Team.owner_id == current_team_and_user.user.id,        # Team owner可以访问整个Team的ApiKey
                Thread.owner_id == current_team_and_user.user.id,       # 其他用户只能访问自己的ApiKey
            )
        ).where(Thread.team_id == current_team_and_user.team.id)      # 限制在当前团队内

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
