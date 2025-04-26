from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.dependencies import (
    SessionDep, CurrentInstanceTeam,
    ValidateCreateInTeam, ValidateUpdateOnTeam, CurrentUser, InstanceStatementTeam
)
from app.api.models import (
    Message,
    Team,
    TeamCreate,
    TeamOut,
    TeamUpdate,
)
from fastapi_pagination.ext.sqlmodel import paginate
from fastapi_pagination.links import Page

from fastapi_filter import FilterDepends

from ..filters import TeamFilter


router = APIRouter(
    prefix="/team", tags=["team"], 
)

@router.get("/", response_model=Page[TeamOut])
async def read_teams(
    session: SessionDep, statement: InstanceStatementTeam, 
    team_filter: TeamFilter = FilterDepends(TeamFilter)
) -> Any:
    """
    List of teams
    """
    statement = team_filter.filter(statement)
    statement = team_filter.sort(statement)
    return await paginate(session, statement)


@router.get("/{id}", response_model=TeamOut)
async def read_team(team: CurrentInstanceTeam) -> Any:
    """
    Get team by ID.
    """
    return team


@router.post("/", response_model=TeamOut)
async def create_team(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    team_in: TeamCreate,
    _: ValidateCreateInTeam
) -> Team:
    """
    Create new team and it's team leader
    """
    team = Team.model_validate(team_in, update={
        "owner_id": current_user.id,
    })

    session.add(team)
    await session.commit()
    await session.refresh(team)
    return team



@router.put("/{id}", response_model=TeamOut)
async def update_team(
    session: SessionDep,
    team_in: TeamUpdate,
    team: ValidateUpdateOnTeam,
) -> Any:
    """
    Update a team.
    """
    team.sqlmodel_update(team_in)
    session.add(team)
    await session.commit()
    await session.refresh(team)
    return team


@router.delete("/{id}")
async def delete_team(session: SessionDep, team: CurrentInstanceTeam) -> Any:
    """
    Delete a team.
    """
    await session.delete(team)
    await session.commit()
    return Message(message="Team deleted successfully")
