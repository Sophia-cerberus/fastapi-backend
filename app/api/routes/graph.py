from typing import Any
import uuid

from fastapi import APIRouter, Depends
from sqlmodel import select

from app.api.dependencies import (
    CurrentUser, SessionDep, CurrentTeamAndUser, ValidateGraphOnRead,
    validate_graph_name_on_create, ValidateGraphOnUpdate
)
from app.api.models import Graph, GraphCreate, GraphOut, GraphUpdate, Message, Team

from fastapi_pagination.ext.sqlmodel import paginate
from fastapi_pagination.links import Page

from fastapi_filter import FilterDepends

from ..filters import GraphFilter

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/", response_model=Page[GraphOut])
async def read_graphs(
    session: SessionDep,
    current_user: CurrentUser,
    team_id: uuid.UUID,
    graph_filter: GraphFilter = FilterDepends(GraphFilter)
) -> Any:
    """
    Retrieve graphs from team.
    """

    statement = select(Graph).where(Graph.team_id == team_id)
    if not current_user.is_superuser:
        statement = statement.join(Team).where(Team.owner_id == current_user.id)

    statement = graph_filter.filter(statement)
    statement = graph_filter.sort(statement)
    return await paginate(session, statement)


@router.get("/{id}", response_model=GraphOut)
async def read_graph(graph: ValidateGraphOnRead) -> Any:
    """
    Get graph by ID.
    """
    return graph


@router.post("/", response_model=GraphOut)
async def create_graph(
    *,
    session: SessionDep,
    current_team_and_user: CurrentTeamAndUser,
    graph_in: GraphCreate,
    _: bool = Depends(validate_graph_name_on_create),
) -> Any:
    """
    Create new graph.
    """
    graph = Graph.model_validate(
        graph_in, update={"team_id": current_team_and_user.team.id, "owner_id": current_team_and_user.user.id}
    )
    session.add(graph)
    await session.commit()
    await session.refresh(graph)
    return graph


@router.put("/{id}", response_model=GraphOut)
async def update_graph(
    *,
    session: SessionDep,
    _: CurrentTeamAndUser,
    graph: ValidateGraphOnUpdate,
    graph_in: GraphUpdate,
) -> Any:
    """
    Update graph by ID.
    """
    graph.sqlmodel_update(graph_in)
    session.add(graph)
    await session.commit()
    await session.refresh(graph)
    return graph


@router.delete("/{id}")
async def delete_graph(
    session: SessionDep,
    _: CurrentTeamAndUser,
    graph: ValidateGraphOnRead
) -> None:
    """
    Delete graph by ID.
    """
    await session.delete(graph)
    await session.commit()
    return Message(message="Api key deleted successfully")
