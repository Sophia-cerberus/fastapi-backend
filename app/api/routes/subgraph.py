from typing import Any

from fastapi import APIRouter
from sqlmodel import select, or_

from app.api.dependencies import (
    SessionDep, CurrentInstanceSubGraph, ValidateOnCreateSubGraph, CurrentTeamAndUser, ValidateOnUpdateSubGraph
)
from app.api.models import (
    Message,
    Subgraph,
    SubgraphCreate,
    SubgraphOut,
    SubgraphUpdate,
    Team,
)

from fastapi_pagination.ext.sqlmodel import paginate
from fastapi_pagination.links import Page

from fastapi_filter import FilterDepends

from ..filters import SubgraphFilter


router = APIRouter(
    prefix="/subgraph", tags=["subgraph"], 
)


@router.get("/", response_model=Page[SubgraphOut])
async def read_all_public_subgraphs(
    session: SessionDep, 
    current_team_and_user: CurrentTeamAndUser,
    subgraph_filter: SubgraphFilter = FilterDepends(SubgraphFilter)
) -> Any:
    """
    Retrieve all public subgraphs.
    """
    statement = select(Subgraph).where(Subgraph.team_id == current_team_and_user.team.id)
    if not current_team_and_user.user.is_superuser:
        statement = statement.join(Team).where(
            or_(
                Subgraph.owner_id == current_team_and_user.user.id, 
                Subgraph.is_public == True,
                Team.owner_id == current_team_and_user.user.id
            )
        )

    statement = subgraph_filter.filter(statement)
    statement = subgraph_filter.sort(statement)
    return await paginate(session, statement)


@router.get("/{id}", response_model=SubgraphOut)
async def read_subgraph(
    subgraph: CurrentInstanceSubGraph
) -> Any:
    """
    Get subgraph by ID.
    """
    return subgraph


@router.post("/", response_model=SubgraphOut)
async def create_subgraph(
    *,
    session: SessionDep,
    current_team_and_user: CurrentTeamAndUser,
    subgraph_in: SubgraphCreate,
     _: ValidateOnCreateSubGraph
) -> Any:
    """
    Create new subgraph.
    """

    subgraph = Subgraph.model_validate(subgraph_in, update={
        "owner_id": current_team_and_user.user.id,
        "team_id": current_team_and_user.team.id,
    })
    session.add(subgraph)
    await session.commit()
    await session.refresh(subgraph)
    return subgraph


@router.put("/{id}", response_model=SubgraphOut)
async def update_subgraph(
    *,
    session: SessionDep,
    subgraph: ValidateOnUpdateSubGraph,
    subgraph_in: SubgraphUpdate,
) -> Any:
    """
    Update subgraph by ID.
    """
    subgraph.sqlmodel_update(subgraph_in)
    session.add(subgraph)
    await session.commit()
    await session.refresh(subgraph)
    return subgraph


@router.delete("/{id}")
async def delete_subgraph(
    session: SessionDep,
    subgraph: CurrentInstanceSubGraph,
) -> Message:
    """
    Delete subgraph by ID.
    """
    await session.delete(subgraph)
    await session.commit()
    return Message(message="Subgraph deleted successfully")