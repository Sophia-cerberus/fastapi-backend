from typing import Annotated
import uuid
from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader
from sqlmodel import select, SQLModel

from app.api.models import TeamCreate, Team, TeamUpdate, Member, User
from app.core.security import security_manager

from .user import CurrentUser
from .session import SessionDep


async def validate_name_on_create(session: SessionDep, team_in: TeamCreate) -> None:
    """Validate that team name is unique"""
    statement = select(Team).where(Team.name == team_in.name)
    team = await session.scalar(statement)
    if team:
        raise HTTPException(status_code=400, detail="Team name already exists")


async def validate_on_read(
    session: SessionDep, id: uuid.UUID, current_user: CurrentUser
) -> Team:
    team = await session.get(Team, id)

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    elif not current_user.is_superuser and (team.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return team


ValidateOnRead = Annotated[Team, Depends(validate_on_read)]


async def validate_on_update(
    session: SessionDep, team_in: TeamUpdate, id: uuid.UUID, current_user: CurrentUser
) -> Team:
    """Validate that team name is unique"""
    statement = select(Team).where(Team.name == team_in.name, Team.id != id)
    same_name = await session.scalar(statement)
    if same_name:
        raise HTTPException(status_code=400, detail="Team name already exists")
    
    return await validate_on_read(session=session, id=id, current_user=current_user)


ValidateOnUpdate = Annotated[Team, Depends(validate_on_update)]


header_scheme = APIKeyHeader(name="x-api-key")


async def get_current_team_from_keys(
    session: SessionDep,
    team_id: uuid.UUID,
    key: str = Depends(header_scheme),
) -> Team:
    """Return team if apikey belongs to it"""
    team = await session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    verified = False
    for apikey in team.apikeys:
        if security_manager.verify_password(key, apikey.hashed_key):
            verified = True
            break
    if not verified:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return team


CurrentTeamFromKeys = Annotated[Team, Depends(get_current_team_from_keys)]


class TeamAndUser(SQLModel):
    team: Team
    user: User


async def get_current_team_and_user(
    session: SessionDep,
    team_id: uuid.UUID,
    current_user: CurrentUser,
) -> TeamAndUser:
    """Return team if apikey belongs to it"""
    team = await session.get(Team, team_id)
    if not current_user.is_superuser:
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        if team.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not enough permissions.")
    return TeamAndUser(team=team, user=current_user)


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
    return Member(name=name, type=type_, role=role, owner_of=None, position_x=0, position_y=0, belongs_to=team.id)
