
from typing import Any

from fastapi import APIRouter

from app.api.dependencies import (
    SessionDep, CurrentTeamAndUser, 
    CurrentInstanceMember, ValidateCreateInMember, ValidateUpdateInMember, InstanceStatementMember
)
from app.api.models import (
    Member,
    MemberCreate,
    MemberOut,
    MemberUpdate,
    Message,
)
from fastapi_pagination.ext.sqlmodel import paginate
from fastapi_pagination.links import Page

from fastapi_filter import FilterDepends

from ..filters import MemberFilter


router = APIRouter(prefix="/member", tags=["member"])


@router.get("/", response_model=Page[MemberOut])
async def read_members(
    session: SessionDep,
    statement: InstanceStatementMember,
    member_filter: MemberFilter = FilterDepends(MemberFilter)
) -> Any:
    """
    Retrieve members from team.
    """
    statement = member_filter.filter(statement)
    statement = member_filter.sort(statement)
    return await paginate(session, statement)


@router.get("/{id}", response_model=MemberOut)
async def read_member(member: CurrentInstanceMember) -> Any:
    """
    Get member by ID.
    """
    return member


@router.post("/", response_model=MemberOut)
async def create_member(
    session: SessionDep,
    current_team_and_user: CurrentTeamAndUser,
    member_in: MemberCreate,
    _: ValidateCreateInMember,
) -> Any:
    """
    Create new member.
    """
    member = Member.model_validate(member_in, update={
        "team_id": current_team_and_user.team.id,
        "owner_id": current_team_and_user.user.id
    })
    session.add(member)
    await session.commit()
    await session.refresh(member)
    return member


@router.put("/{id}", response_model=MemberOut)
async def update_member(
    *,
    session: SessionDep,
    member: ValidateUpdateInMember,
    member_in: MemberUpdate,
) -> Any:
    """
    Update a member.
    """
    update_dict = member_in.model_dump(exclude_unset=True)
    member.sqlmodel_update(update_dict)
    session.add(member)
    session.commit()
    session.refresh(member)
    return member


@router.delete("/{id}")
def delete_member(
    session: SessionDep, member: CurrentInstanceMember
) -> Message:
    """
    Delete a member.
    """
    session.delete(member)
    session.commit()
    return Message(message="Member deleted successfully")
