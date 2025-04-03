from typing import Annotated, Union
import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from sqlmodel import select, SQLModel
from sqlmodel.sql._expression_select_cls import SelectOfScalar

from app.api.models import TeamCreate, Team, TeamUpdate, Member, User
from app.core.security import security_manager
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


async def instance_statement(current_user: CurrentUser) ->  SelectOfScalar[Team]:
    
    statement = select(Team)
    if not current_user.is_superuser:
        statement = (
            select(Team).where(Team.owner_id == current_user.id)
        )
    return statement


async def current_instance(
    session: SessionDep, id: uuid.UUID, current_user: CurrentUser
) -> Team:
    
    statement = await instance_statement(current_user)
    statement = statement.where(Team.id == id)

    if not (subgraph := await session.scalar(statement)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return subgraph


async def validate_name_in(
    session: SessionDep, team_in: Union[TeamUpdate, TeamCreate], current_user: CurrentUser
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
    session: SessionDep, team_in: TeamCreate, current_user: CurrentUser
) -> None:
    
    if await validate_name_in(session=session, team_in=team_in, current_user=current_user):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Team name already exists")

    
async def validate_update_in(
    session: SessionDep, team_in: TeamUpdate, id: uuid.UUID, current_user: CurrentUser
) -> Team:
    
    if await validate_name_in(session=session, team_in=team_in, current_user=current_user):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Team name already exists")
    
    return await current_instance(session=session, id=id, current_user=current_user)


InstanceStatement = Annotated[SelectOfScalar[Team], Depends(instance_statement)]
CurrentInstance = Annotated[Team, Depends(current_instance)]
ValidateCreateIn = Annotated[None, Depends(validate_create_in)]
ValidateUpdateOn = Annotated[Team, Depends(validate_update_in)]
CurrentTeamAndUser = Annotated[TeamAndUser, Depends(get_current_team_and_user)]


def create_member_for_team(team: Team) -> Member:

    """Create a member based on team workflow."""
    roles = {
        "hierarchical": (f"{team.name}Leader", "root", "Gather inputs from your team and answer the question."),
        "sequential": ("Worker0", "freelancer_root", "Answer the user's question."),
        "chatbot": ("ChatBot", "chatbot", "Answer the user's question."),
        "ragbot": ("RagBot", "ragbot", "Answer the user's question using knowledge base."),
        "workflow": ("Workflow", "workflow", "Answer the user's question."),
    }
    if team.workflow not in roles:
        raise HTTPException(status_code=400, detail="Invalid workflow")
    name, type_, role = roles[team.workflow]
    return Member(name=name, type=type_, role=role, owner_id=team.owner_id, position_x=0, position_y=0, team_id=team.id)
