from typing import Annotated
import uuid

from fastapi import Depends, HTTPException
from sqlmodel import select

from app.api.models import Subgraph

from .session import SessionDep
from .user import CurrentUser


async def validate_on_read(
    session: SessionDep, id: uuid.UUID, current_user: CurrentUser
) -> Subgraph:

    subgraph = await session.get(Subgraph, id)

    if not subgraph:
        raise HTTPException(status_code=404, detail="Subgraph not found")
    elif not current_user.is_superuser and (Subgraph.owner_id != current_user.id) and subgraph.is_public:
        raise HTTPException(status_code=400, detail="Not enough permissions")

    return subgraph


ValidateOnRead = Annotated[Subgraph, Depends(validate_on_read)]


async def validate_name_on_create(session: SessionDep, graph_in: Subgraph) -> None:
    """Validate that graph name is unique"""
    statement = select(Subgraph).where(
        Subgraph.name == graph_in.name, Subgraph.team_id == graph_in.team_id
    )

    graph = await session.scalar(statement)
    if graph:
        raise HTTPException(status_code=409, detail="Subgraph name already exists")


async def validate_name_on_update(
    session: SessionDep, graph_in: Subgraph, id: uuid.UUID
) -> None:
    """Validate that graph name is unique"""
    statement = select(Subgraph).where(
        Subgraph.name == graph_in.name, Subgraph.id != id, 
        Subgraph.team_id == graph_in.team_id
    )
    graph = await session.scalar(statement)
    if graph:
        raise HTTPException(status_code=409, detail="Subgraph name already exists")
    
    return await validate_on_read(session=session, id=id)


ValidateOnUpdate = Annotated[Subgraph, Depends(validate_name_on_update)]
