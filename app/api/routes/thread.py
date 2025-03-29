from datetime import datetime
from typing import Any

from fastapi import APIRouter
from sqlmodel import select

from app.api.dependencies import CurrentTeamAndUser, SessionDep, CurrentInstanceThread, InstanceStatementThread

from app.api.models import (
    Message,
    Thread,
    ThreadCreate,
    ThreadOut,
    ThreadRead,
    ThreadUpdate,
)
from fastapi_pagination.ext.sqlmodel import paginate
from fastapi_pagination.links import Page

from fastapi_filter import FilterDepends

from ..filters import ThreadFilter


router = APIRouter(
    prefix="/thread", tags=["thread"], 
)


@router.get("/", response_model=Page[ThreadOut])
async def read_threads(
    session: SessionDep,
    statement: InstanceStatementThread,
    thread_filter: ThreadFilter = FilterDepends(ThreadFilter)
) -> Any:
    """
    List of threads
    """
    statement = thread_filter.filter(statement)
    statement = thread_filter.sort(statement)
    return await paginate(session, statement)


@router.get("/{id}", response_model=ThreadRead)
async def read_thread(
    thread: CurrentInstanceThread
) -> Any:
    """
    Get thread and its last checkpoint by ID
    """
    return thread


@router.post("/", response_model=ThreadOut)
async def create_thread(
    *,
    session: SessionDep,
    current_team_and_user: CurrentTeamAndUser,
    thread_in: ThreadCreate,
) -> Any:
    """
    Create new thread
    """
    thread = Thread.model_validate(thread_in, update={
        "team_id": current_team_and_user.team.id, 
        "owner": current_team_and_user.user.id, 
        "updated_at": datetime.now()
    })
    session.add(thread)
    await session.commit()
    await session.refresh(thread)
    return thread


@router.put("/{id}", response_model=ThreadOut)
async def update_thread(
    *,
    session: SessionDep,
    thread: CurrentInstanceThread,
    thread_in: ThreadUpdate,
) -> Any:
    """
    Update a thread.
    """
    thread.sqlmodel_update(thread_in)
    session.add(thread)
    await session.commit()
    await session.refresh(thread)
    return thread


@router.delete("/{id}")
async def delete_thread(
    session: SessionDep, thread: CurrentInstanceThread
) -> Any:
    """
    Delete a thread.
    """
    for checkpoint in thread.checkpoints:
        session.delete(checkpoint)

    await session.delete(thread)
    await session.commit()
    return Message(message="Thread deleted successfully")
