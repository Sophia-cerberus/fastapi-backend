from typing import Annotated
import uuid
from fastapi import Depends, HTTPException
from sqlmodel import select
from app.api.models import Member, MemberCreate, MemberUpdate
from app.api.models.team import Team
from app.core.config import settings
from .user import CurrentUser
from .session import SessionDep


async def validate_name_on_create(
    session: SessionDep, team_id: uuid.UUID, member_in: MemberCreate
) -> None:
    """Check if (name, team_id) is unique and name is not a protected name"""
    if member_in.name in settings.PROTECTED_NAMES:
        raise HTTPException(
            status_code=409, detail="Name is a protected name. Choose another name."
        )
    statement = select(Member).where(
        Member.name == member_in.name,
        Member.belongs_to == team_id,
    )
    member_unique = await session.scalar(statement)
    if member_unique:
        raise HTTPException(
            status_code=409, detail="Member with this name already exists"
        )


async def validate_name_on_update(
    session: SessionDep, team_id: uuid.UUID, member_in: MemberUpdate, id: uuid.UUID
) -> None:
    """Check if (name, team_id) is unique and name is not a protected name"""
    if member_in.name in settings.PROTECTED_NAMES:
        raise HTTPException(
            status_code=409, detail="Name is a protected name. Choose another name."
        )
    statement = select(Member).where(
        Member.name == member_in.name,
        Member.belongs_to == team_id,
        Member.id != id,
    )
    member_unique = await session.scalar(statement)
    if member_unique:
        raise HTTPException(
            status_code=409, detail="Member with this name already exists"
        )
    
async def validate_on_read(
    session: SessionDep, id: uuid.UUID, team_id: uuid.UUID, current_user: CurrentUser
) -> Member:
    statement = select(Member).where(Member.id == id, Member.belongs_to == team_id)
    if not current_user.is_superuser:
        statement = statement.join(Team).where(Team.owner_id == current_user.id)

    member = await session.scalar(statement)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member


ValidateOnRead = Annotated[Member, Depends(validate_on_read)]

