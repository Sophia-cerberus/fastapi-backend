from typing import Annotated
import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from sqlmodel import select, SQLModel

from app.api.models import TeamCreate, Team, TeamUpdate, Member, User
from app.core.security import security_manager

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
        raise HTTPException(status_code=404, detail="Team not found")
    return TeamAndUser(team=team, user=current_user)


CurrentTeamAndUser = Annotated[TeamAndUser, Depends(get_current_team_and_user)]


async def current_instance(
    session: SessionDep, id: uuid.UUID, current_user: CurrentUser
) -> Team:
    
    statement = select(Team).where(Team.owner_id == current_user.id, Team.id == id)

    if not (subgraph := await session.scalar(statement)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return subgraph


async def validate_create_in(session: SessionDep, team_in: TeamCreate) -> None:
    """Validate that team name is unique"""
    statement = select(Team).where(
        Team.name == team_in.name,
        Team.owner_id == team_in.team_id
    )
    if not await session.scalar(statement):
        return 
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Team name already exists")

    
async def validate_update_in(
    session: SessionDep, team_in: TeamUpdate, id: uuid.UUID, current_user: CurrentUser
) -> Team:
    """Validate that team name is unique"""
    statement = select(Team).where(Team.name == team_in.name, Team.id != id)
    if await session.scalar(statement):
        raise HTTPException(status_code=400, detail="Team name already exists")
    
    return await current_instance(session=session, id=id, current_user=current_user)


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
        apikey.team_id
        if security_manager.verify_password(key, apikey.hashed_key):
            verified = True
            break
    if not verified:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return team


CurrentInstance = Annotated[Team, Depends(current_instance)]
ValidateCreateIn = Annotated[None, Depends(validate_create_in)]
ValidateUpdateOn = Annotated[Team, Depends(validate_update_in)]
CurrentTeamFromKeys = Annotated[Team, Depends(get_current_team_from_keys)]


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
