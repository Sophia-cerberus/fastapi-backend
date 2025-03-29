from typing import Annotated
import uuid
from fastapi import Depends, HTTPException, status
from sqlmodel import or_, select
from app.api.models import Member, MemberCreate, MemberUpdate, Team
from app.core.config import settings
from .team import CurrentTeamAndUser
from .session import SessionDep


async def current_instance(
    session: SessionDep, id: uuid.UUID, current_team_and_user: CurrentTeamAndUser
) -> Member:
    
    statement = (
        select(Member).where(Member.belongs_to == current_team_and_user.team.id, Member.id == id)
    )
    if not current_team_and_user.user.is_superuser:
        statement = statement.join(Team).where(
            or_(
                Member.owner_id == current_team_and_user.user.id, 
                Team.owner_id == current_team_and_user.user.id,
            )
        )
        
    if not (member := await session.scalar(statement)):
        raise HTTPException(status_code=404, detail="Member not found")
    return member


async def validate_create_in(
    session: SessionDep, team_id: uuid.UUID, member_in: MemberCreate
) -> None:
    """Check if (name, team_id) is unique and name is not a protected name"""
    if member_in.name in settings.PROTECTED_NAMES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="Name is a protected name. Choose another name."
        )
    statement = select(Member).where(
        Member.name == member_in.name,
        Member.belongs_to == team_id,
    )
    member_unique = await session.scalar(statement)
    if not member_unique:
        return 
    
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT, 
        detail="Member with this name already exists"
    )


async def validate_update_in(
    session: SessionDep,  member_in: MemberUpdate, id: uuid.UUID, current_team_and_user: CurrentTeamAndUser
) -> None:
    """Check if (name, team_id) is unique and name is not a protected name"""
    if member_in.name in settings.PROTECTED_NAMES:
        raise HTTPException(
            status_code=409, detail="Name is a protected name. Choose another name."
        )
    statement = select(Member).where(
        Member.name == member_in.name, Member.id != id,
        Member.belongs_to == current_team_and_user.team.id,
    )
    if await session.scalar(statement):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Member name already exists")
    
    return await current_instance(session=session, id=id, current_team_and_user=current_team_and_user)


CurrentInstance = Annotated[Member, Depends(current_instance)]
ValidateCreateIn = Annotated[None, Depends(validate_create_in)]
ValidateUpdateIn = Annotated[Member, Depends(validate_update_in)]

