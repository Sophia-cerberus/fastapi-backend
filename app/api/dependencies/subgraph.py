from typing import Annotated
import uuid

from fastapi import Depends, HTTPException, status
from sqlmodel import or_, select

from app.api.models import Subgraph, Team

from .session import SessionDep
from .team import CurrentTeamAndUser


async def current_instance(
    session: SessionDep, id: uuid.UUID, current_team_and_user: CurrentTeamAndUser
) -> Subgraph:
    
    statement = select(Subgraph).where(Subgraph.team_id == current_team_and_user.team.id, Subgraph.id == id)
    if not current_team_and_user.user.is_superuser:
        statement = statement.where(
            or_(
                Subgraph.owner_id == current_team_and_user.user.id, 
                Subgraph.is_public == True,
                Team.owner_id == current_team_and_user.user.id,
            )
        )

    if not (subgraph := await session.scalar(statement)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subgraph not found")
    return subgraph


async def validate_create_in(session: SessionDep, graph_in: Subgraph) -> None:
    """Validate that graph name is unique"""
    statement = select(Subgraph).where(
        Subgraph.name == graph_in.name, 
        Subgraph.team_id == graph_in.team_id
    )
    if not await session.scalar(statement):
        return 
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Subgraph name already exists")


async def validate_update_in(
    session: SessionDep, graph_in: Subgraph, id: uuid.UUID
) -> None:
    """Validate that graph name is unique"""
    statement = select(Subgraph).where(
        Subgraph.name == graph_in.name, Subgraph.id != id, 
        Subgraph.team_id == graph_in.team_id
    )
    if await session.scalar(statement):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Subgraph name already exists")
    
    return await current_instance(session=session, id=id)


CurrentInstance = Annotated[Subgraph, Depends(current_instance)]
ValidateCreateIn = Annotated[None, Depends(validate_create_in)]
ValidateUpdateOn = Annotated[Subgraph, Depends(validate_update_in)]
