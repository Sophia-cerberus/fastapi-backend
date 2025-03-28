
from typing import Any
import uuid

from fastapi import APIRouter, Depends
from sqlmodel import col, select

from app.api.dependencies import (
    CurrentUser, SessionDep, CurrentTeamAndUser, ValidateMemberOnRead,
    validate_member_name_on_create, validate_member_name_on_update
)
from app.api.models import (
    Member,
    MemberCreate,
    MemberOut,
    MemberUpdate,
    Message,
    Team,
)
from fastapi_pagination.ext.sqlmodel import paginate
from fastapi_pagination.links import Page

from fastapi_filter import FilterDepends

from ..filters import MemberFilter


router = APIRouter(prefix="/member", tags=["member"])


@router.get("/", response_model=Page[MemberOut])
async def read_members(
    session: SessionDep,
    current_user: CurrentUser,
    team_id: uuid.UUID,
    member_filter: MemberFilter = FilterDepends(MemberFilter)
) -> Any:
    """
    Retrieve members from team.
    """
    statement = select(Member).where(Member.belongs_to == team_id)
    if not current_user.is_superuser:
        statement = statement.join(Team).where(Team.owner_id == current_user.id)
    
    statement = member_filter.filter(statement)
    statement = member_filter.sort(statement)
    return await paginate(session, statement)


@router.get("/{id}", response_model=MemberOut)
async def read_member(member: ValidateMemberOnRead) -> Any:
    """
    Get member by ID.
    """
    return member


@router.post("/", response_model=MemberOut)
async def create_member(
    session: SessionDep,
    current_team_and_user: CurrentTeamAndUser,
    member_in: MemberCreate,
    _: bool = Depends(validate_member_name_on_create),
) -> Any:
    """
    Create new member.
    """
    member = Member.model_validate(member_in, update={"belongs_to": current_team_and_user.team.id})
    session.add(member)
    await session.commit()
    await session.refresh(member)
    return member


@router.put("/{id}", response_model=MemberOut)
async def update_member(
    *,
    session: SessionDep,
    member: ValidateMemberOnRead,
    member_in: MemberUpdate,
    _: bool = Depends(validate_member_name_on_update),
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
    session: SessionDep, member: ValidateMemberOnRead
) -> Message:
    """
    Delete a member.
    """
    session.delete(member)
    session.commit()
    return Message(message="Member deleted successfully")
