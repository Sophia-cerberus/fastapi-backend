from datetime import datetime
from typing import Any, Dict
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import select

from app.api.dependencies import (
    CurrentTeamAndUser, SessionDep, CurrentInstanceTeam,
    ValidateCreateInTeam, ValidateUpdateOnTeam, CurrentUser,
    create_member_for_team
)
# from app.core.graph.build import generator
from app.api.models import (
    Message,
    Team,
    TeamChat,
    TeamChatPublic,
    TeamCreate,
    TeamOut,
    TeamUpdate,
    Thread,
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
    session: SessionDep, current_user: CurrentUser, 
    team_filter: TeamFilter = FilterDepends(TeamFilter)
) -> Any:
    """
    Retrieve teams
    """
    statement = select(Team)
    if not current_user.is_superuser:
        statement = statement.where(Team.owner_id == current_user.id)

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
    current_team_and_user: CurrentTeamAndUser,
    team_in: TeamCreate,
    _: ValidateCreateInTeam
) -> Team:
    """
    Create new team and it's team leader
    """
    team = Team.model_validate(team_in, update={
        "owner_id": current_team_and_user.user.id
    })

    session.add(team)
    await session.commit()
    await session.refresh(team)  # 确保获取最新状态

    member = create_member_for_team(team := team.model_copy())
    session.add(member)
    await session.commit()

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
async def delete_team(session: SessionDep, team: CurrentTeamAndUser) -> Any:
    """
    Delete a team.
    """
    await session.delete(team)
    await session.commit()
    return Message(message="Team deleted successfully")


# @router.post("/{id}/stream/{thread_id}")
# async def stream(
#     session: SessionDep,
#     team: CurrentTeamAndUser,
#     thread_id: uuid.UUID,
#     team_chat: TeamChat,
# ) -> StreamingResponse:
#     """
#     Stream a response to a user's input.
#     """
#     # Check if thread belongs to the team
#     thread = await session.get(Thread, thread_id)
#     if not thread:
#         raise HTTPException(status_code=404, detail="Thread not found")
#     if thread.team_id != id:
#         raise HTTPException(
#             status_code=400, detail="Thread does not belong to the team"
#         )

#     # Populate the skills and accessible uploads for each member
#     members = team.members
#     for member in members:
#         member.skills = member.skills
#         member.uploads = member.uploads
#     graphs = team.graphs
#     for graph in graphs:
#         graph.config = graph.config
#     return StreamingResponse(
#         generator(team, members, team_chat.messages, thread_id, team_chat.interrupt),
#         media_type="text/event-stream",
#     )


# @router.post("/{team_id}/stream-public/{thread_id}")
# async def public_stream(
#     session: SessionDep,
#     team_id: uuid.UUID,
#     team_chat: TeamChatPublic,
#     thread_id: uuid.UUID,
#     team: CurrentTeamFromKeys,
# ) -> StreamingResponse:
#     # Check if thread belongs to the team
#     thread = await session.get(Thread, thread_id)
#     message_content = team_chat.message.content if team_chat.message else ""
#     if not thread:
#         # create new thread
#         thread = Thread(
#             id=thread_id,
#             query=message_content,
#             updated_at=datetime.now(),
#             team_id=team_id,
#         )
#         session.add(thread)
#         await session.commit()
#         await session.refresh(thread)
#     else:
#         if thread.team_id != team_id:
#             raise HTTPException(
#                 status_code=400, detail="Thread does not belong to the team"
#             )
#     # Populate the skills and accessible uploads for each member
#     members = team.members
#     for member in members:
#         member.skills = member.skills
#         member.uploads = member.uploads
#     messages = [team_chat.message] if team_chat.message else []
#     return StreamingResponse(
#         generator(team, members, messages, thread_id, team_chat.interrupt),
#         media_type="text/event-stream",
#     )