from typing import Annotated, Union
import uuid
from fastapi import Depends, HTTPException, status
from sqlmodel import select, SQLModel
from sqlmodel.sql._expression_select_cls import SelectOfScalar

from app.api.models import TeamCreate, Team, TeamUpdate, User, Tenant, TeamUserJoin
from app.api.utils.models import StatusTypes
from app.core.config import settings

from .session import SessionDep
from .user import CurrentUser


class TeamAndUser(SQLModel):
    team: Team
    user: User


async def get_current_team_and_user(
    session: SessionDep,
    team_id: uuid.UUID,
    current_user: CurrentUser,
) -> TeamAndUser:
    """Return team if apikey belongs to it"""
    if not (team := await session.get(Team, team_id)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return TeamAndUser(team=team, user=current_user)


async def instance_statement(current_user: CurrentUser, tenant_id: uuid.UUID) ->  SelectOfScalar[Team]:
    """Return all teams that the current user has access to"""
    statement = select(Team)
    
    if not current_user.is_superuser:
        # Join with TeamUserJoin to get all teams the user is a member of
        statement = statement.join(TeamUserJoin).where(
            Team.tenant_id == tenant_id,
            TeamUserJoin.user_id == current_user.id,
            TeamUserJoin.status == StatusTypes.ENABLE
        )
    return statement


async def current_instance(
    session: SessionDep, id: uuid.UUID, current_user: CurrentUser, tenant_id: uuid.UUID
) -> Team:
    
    statement = await instance_statement(current_user, tenant_id)
    statement = statement.where(Team.id == id)

    if not (subgraph := await session.scalar(statement)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return subgraph


async def validate_name_in(
    session: SessionDep, team_in: Union[TeamUpdate, TeamCreate]
) -> Team | None:

    if team_in.name in settings.PROTECTED_NAMES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="Name is a protected name. Choose another name."
        )
    statement = select(Team).where(
        Team.name == team_in.name, 
    )
    return await session.scalar(statement)


async def validate_create_in(
    session: SessionDep, team_in: TeamCreate
) -> None:
    
    if await validate_name_in(session=session, team_in=team_in):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Team name already exists")

    
async def validate_update_in(
    session: SessionDep, team_in: TeamUpdate, id: uuid.UUID, current_user: CurrentUser, tenant_id: uuid.UUID
) -> Team:
    
    if await validate_name_in(session=session, team_in=team_in):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Team name already exists")
    
    return await current_instance(session=session, id=id, current_user=current_user, tenant_id=tenant_id)


InstanceStatement = Annotated[SelectOfScalar[Team], Depends(instance_statement)]
CurrentInstance = Annotated[Team, Depends(current_instance)]
ValidateCreateIn = Annotated[None, Depends(validate_create_in)]
ValidateUpdateOn = Annotated[Team, Depends(validate_update_in)]
CurrentTeamAndUser = Annotated[TeamAndUser, Depends(get_current_team_and_user)]
