from typing import Annotated, Union
import uuid
from fastapi import Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.sql._expression_select_cls import SelectOfScalar

from app.api.models import Tenant, TeamUserJoin, Team, TenantUpdate, TenantOut, TenantCreate
from app.api.utils.models import StatusTypes
from app.core.config import settings

from .session import SessionDep
from .common import CurrentTeamAndUser



async def instance_statement(current_team_and_user: CurrentTeamAndUser) ->  SelectOfScalar[Tenant]:
    
    statement = select(Tenant)
    if not current_team_and_user.user.is_superuser:
        statement: SelectOfScalar[Tenant] = statement.join(
            Team
        ).join(
            TeamUserJoin
        ).where(
            TeamUserJoin.team_id == current_team_and_user.team.id,
            TeamUserJoin.status == StatusTypes.ENABLE
        )
    
    return statement


async def current_instance(
    session: SessionDep, id: uuid.UUID, current_team_and_user: CurrentTeamAndUser
) -> Team:
    
    statement = await instance_statement(current_team_and_user)
    statement = statement.where(Team.id == id)

    if not (subgraph := await session.scalar(statement)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return subgraph


async def validate_name_in(
    session: SessionDep, tenant_in: Union[TenantUpdate, TenantCreate]
) -> Team | None:

    if tenant_in.name in settings.PROTECTED_NAMES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="Name is a protected name. Choose another name."
        )
    statement = select(Tenant).where(
        Tenant.name == tenant_in.name, 
    )
    return await session.scalar(statement)


async def validate_create_in(
    session: SessionDep, tenant_in: TenantCreate
) -> None:
    
    if await validate_name_in(session=session, tenant_in=tenant_in):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Team name already exists")

    
async def validate_update_in(
    session: SessionDep, tenant_in: TenantUpdate, id: uuid.UUID, current_team_and_user: CurrentTeamAndUser
) -> Team:
    
    if await validate_name_in(session=session, tenant_in=tenant_in):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Team name already exists")
    
    return await current_instance(session=session, id=id, current_team_and_user=current_team_and_user)


InstanceStatement = Annotated[SelectOfScalar[Team], Depends(instance_statement)]
CurrentInstance = Annotated[Team, Depends(current_instance)]
ValidateCreateIn = Annotated[None, Depends(validate_create_in)]
ValidateUpdateOn = Annotated[Team, Depends(validate_update_in)]
