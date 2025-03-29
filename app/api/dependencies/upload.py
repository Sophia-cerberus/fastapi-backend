from typing import Annotated
import uuid

from fastapi import Depends, HTTPException
from sqlmodel import or_, select
from sqlmodel.sql._expression_select_cls import SelectOfScalar

from app.api.models import Upload, Team

from .session import SessionDep
from .team import CurrentTeamAndUser


async def instance_statement(current_team_and_user: CurrentTeamAndUser) ->  SelectOfScalar[Upload]:
    
    statement = select(Upload)
    if not current_team_and_user.user.is_superuser:
        statement = statement.join(Team).where(
            or_(
                Team.owner_id == current_team_and_user.user.id,        # Team owner可以访问整个Team的ApiKey
                Upload.owner_id == current_team_and_user.user.id,       # 其他用户只能访问自己的ApiKey
            )
        ).where(Upload.team_id == current_team_and_user.team.id)      # 限制在当前团队内

    return statement


async def current_instance(
    session: SessionDep, id: uuid.UUID, current_team_and_user: CurrentTeamAndUser
) -> Upload:
    
    statement = await instance_statement(current_team_and_user)
    statement = statement.where(Upload.id == id)

    upload = await session.scalar(statement)
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    return upload


InstanceStatement = Annotated[Upload, Depends(instance_statement)]
CurrentInstance = Annotated[Upload, Depends(current_instance)]