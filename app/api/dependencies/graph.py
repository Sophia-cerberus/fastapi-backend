
from typing import Annotated
import uuid
from fastapi import Depends, HTTPException
from sqlmodel import select

from app.api.models import Graph, GraphCreate, GraphUpdate, Team
from .user import CurrentUser
from .session import SessionDep


async def validate_on_read(
    session: SessionDep, id: uuid.UUID, current_user: CurrentUser, team_id: uuid.UUID
) -> Graph:

    statement = select(Graph).where(Graph.team_id == team_id, Graph.id == id)

    if not current_user.is_superuser:
        statement = statement.join(Team).where(Team.owner_id == current_user.id)

    graph = await session.scalar(statement)
    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found")
    return graph


ValidateOnRead = Annotated[Graph, Depends(validate_on_read)]


async def validate_name_on_create(session: SessionDep, graph_in: GraphCreate) -> None:
    """Validate that graph name is unique"""
    statement = select(Graph).where(Graph.name == graph_in.name)
    graph = await session.scalar(statement)
    if graph:
        raise HTTPException(status_code=409, detail="Graph name already exists")


async def validate_name_on_update(
    session: SessionDep, graph_in: GraphUpdate, id: uuid.UUID
) -> None:
    """Validate that graph name is unique"""
    statement = select(Graph).where(Graph.name == graph_in.name, Graph.id != id)
    graph = await session.scalar(statement)
    if graph:
        raise HTTPException(status_code=409, detail="Graph name already exists")
    
    return await validate_on_read(session=session, id=id)

ValidateOnUpdate = Annotated[Graph, Depends(validate_name_on_update)]
