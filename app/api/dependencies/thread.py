from typing import Annotated
import uuid

from fastapi import Depends, HTTPException
from grpc import Status
from sqlmodel import select

from app.api.models import Thread, Team
from app.core.config import Settings

from .session import SessionDep
from .team import CurrentTeamAndUser


async def current_instance(
    session: SessionDep, id: uuid.UUID, current_team_and_user: CurrentTeamAndUser
) -> Thread:
    
    statement = select(Thread).where(
        Thread.id == id, Thread.team_id == current_team_and_user.team.id
    )
    if not current_team_and_user.user.is_superuser:
        statement.join(Team).where(Team.owner_id == current_team_and_user.user.id)

    thread = await session.scalar(statement)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    return thread


CurrentInstance = Annotated[Thread, Depends(current_instance)]
