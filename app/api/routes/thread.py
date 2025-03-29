from datetime import datetime
from typing import Any

from fastapi import APIRouter
from sqlmodel import select

from app.api.dependencies import CurrentTeamAndUser, SessionDep, ValidateThreadOnRead
from app.core.graph.checkpoint.utils import (
    convert_checkpoint_tuple_to_messages,
    get_checkpoint_tuples,
)
from app.api.models import (
    Message,
    Team,
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
    current_team_and_user: CurrentTeamAndUser,
    thread_filter: ThreadFilter = FilterDepends(ThreadFilter)
) -> Any:
    """
    Retrieve threads
    """
    statement = select(Thread).where(Thread.team_id == current_team_and_user.team.id)
    if not current_team_and_user.user.is_superuser:
        statement = statement.where(
            Thread.owner_id == current_team_and_user.user.id
        )

    statement = thread_filter.filter(statement)
    statement = thread_filter.sort(statement)
    return await paginate(session, statement)


@router.get("/{id}", response_model=ThreadRead)
async def read_thread(
    thread: ValidateThreadOnRead
) -> Any:
    """
    Get thread and its last checkpoint by ID
    """
    checkpoint_tuple = await get_checkpoint_tuples(str(thread.id))
    if checkpoint_tuple:
        messages = convert_checkpoint_tuple_to_messages(checkpoint_tuple)
    else:
        messages = []

    return ThreadRead(
        id=thread.id,
        query=thread.query,
        messages=messages,
        updated_at=thread.updated_at,
    )


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
    thread: ValidateThreadOnRead,
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
    session: SessionDep, thread: ValidateThreadOnRead
) -> Any:
    """
    Delete a thread.
    """
    
    for checkpoint in thread.checkpoints:
        session.delete(checkpoint)

    await session.delete(thread)
    await session.commit()
    return Message(message="Thread deleted successfully")


@router.get("/public/{thread_id}", response_model=ThreadRead)
async def read_thread_public(
    thread: ValidateThreadOnRead
) -> Any:
    """
    Get thread and its last checkpoint by ID
    """
    
    checkpoint_tuple = await get_checkpoint_tuples(str(thread.id))
    if checkpoint_tuple:
        messages = convert_checkpoint_tuple_to_messages(checkpoint_tuple)
    else:
        messages = []
    return ThreadRead(
        id=thread.id,
        query=thread.query,
        messages=messages,
        updated_at=thread.updated_at,
    )