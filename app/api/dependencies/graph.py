
from typing import Annotated
import uuid
from fastapi import Depends, HTTPException, status
from sqlmodel import select, or_

from app.api.models import Graph, GraphCreate, GraphUpdate, Team
from app.core.config import settings

from .team import CurrentTeamAndUser
from .session import SessionDep


async def current_instance(
    session: SessionDep, id: uuid.UUID, current_team_and_user: CurrentTeamAndUser
) -> Graph:

    statement = (
        select(Graph).where(Graph.team_id == current_team_and_user.team.id, Graph.id == id)
    )
    if not current_team_and_user.user.is_superuser:
        statement = statement.join(Team).where(
            or_(
                Graph.owner_id == current_team_and_user.user.id, 
                Team.owner_id == current_team_and_user.user.id,
                Graph.is_public == True
            )
        )

    if not (graph := await session.scalar(statement)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Graph not found")
    return graph


async def validate_create_in(
        session: SessionDep, graph_in: GraphCreate, current_team_and_user: CurrentTeamAndUser
) -> None:
    
    statement = select(Graph).where(
        Graph.name == graph_in.name, 
        Graph.team_id == current_team_and_user.team.id,
    )
    if not await session.scalar(statement):
        return
    
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Graph name already exists")


async def validate_update_in(
    session: SessionDep, graph_in: GraphUpdate, id: uuid.UUID, current_team_and_user: CurrentTeamAndUser
) -> None:
    
    if graph_in.name in settings.PROTECTED_NAMES:
        raise HTTPException(
            status_code=409, detail="Name is a protected name. Choose another name."
        )
    statement = select(Graph).where(
        Graph.name == graph_in.name, Graph.id != id,
        Graph.team_id == current_team_and_user.team.id
    )
    if await session.scalar(statement):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Graph name already exists")
    
    return await current_instance(session=session, id=id, current_team_and_user=current_team_and_user)


CurrentInstance = Annotated[Graph, Depends(current_instance)]
ValidateCreateIn = Annotated[None, Depends(validate_create_in)]
ValidateUpdateIn = Annotated[Graph, Depends(validate_update_in)]
