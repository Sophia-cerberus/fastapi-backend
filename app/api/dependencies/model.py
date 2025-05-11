from typing import Annotated, Union

import uuid

from fastapi import Depends, HTTPException, status
from sqlmodel import or_, select
from sqlmodel.sql._expression_select_cls import SelectOfScalar

from app.api.models import ModelCreate, TeamUserJoin, Model, ModelUpdate, RoleTypes, Team
from app.api.utils.models import StatusTypes
from app.core.config import settings

from .session import SessionDep
from .common import CurrentTeamAndUser


async def instance_statement(current_team_and_user: CurrentTeamAndUser) ->  SelectOfScalar[Model]:
    
    statement: SelectOfScalar[Model] = select(Model)
    if not current_team_and_user.user.is_superuser:
        if current_team_and_user.user.is_tenant_admin:
            statement = statement.join(Team).where(
                Team.tenant_id == current_team_and_user.team.tenant_id
            )
        else:
            statement = statement.join(TeamUserJoin).where(
                TeamUserJoin.user_id == current_team_and_user.user.id,
                TeamUserJoin.status == StatusTypes.ENABLE,
                TeamUserJoin.team_id == current_team_and_user.team.id == Model.team_id                   
            ).where(
                or_(
                    TeamUserJoin.role in [RoleTypes.ADMIN, RoleTypes.MODERATOR, RoleTypes.OWNER],
                    Model.owner_id == current_team_and_user.user.id
                )
            )      # 限制在当前团队内

    return statement


async def current_instance(
    session: SessionDep, id: uuid.UUID, current_team_and_user: CurrentTeamAndUser
) -> Model:
    
    statement = await instance_statement(current_team_and_user)
    statement = statement.where(Model.id == id)

    if not (model := await session.scalar(statement)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    return model


async def validate_name_in(
    session: SessionDep, ai_model_in: Union[ModelUpdate, ModelCreate], current_team_and_user: CurrentTeamAndUser
) -> Model | None:

    if ai_model_in.name in settings.PROTECTED_NAMES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="Name is a protected name. Choose another name."
        )
    statement = select(Model).where(
        Model.ai_model_name == ai_model_in.ai_model_name, 
        Model.team_id == current_team_and_user.team.id,
    )
    return await session.scalar(statement)


async def validate_update_in(
    session: SessionDep,  ai_model_in: ModelUpdate, id: uuid.UUID, current_team_and_user: CurrentTeamAndUser
) -> None:

    if await validate_name_in(session=session, ai_model_in=ai_model_in, current_team_and_user=current_team_and_user):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Member name already exists")

    return await current_instance(session=session, id=id, current_team_and_user=current_team_and_user)


InstanceStatement = Annotated[SelectOfScalar[Model], Depends(instance_statement)]
CurrentInstance = Annotated[Model, Depends(current_instance)]
ValidateUpdateIn = Annotated[Model, Depends(validate_update_in)]
