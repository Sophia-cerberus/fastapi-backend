from typing import Annotated, Union
import uuid
from fastapi import Depends, HTTPException, status
from sqlmodel import or_, select
from sqlmodel.sql._expression_select_cls import SelectOfScalar

from app.api.models import Member, MemberCreate, MemberUpdate, Team
from app.core.config import settings
from .team import CurrentTeamAndUser
from .session import SessionDep


async def instance_statement(current_team_and_user: CurrentTeamAndUser) ->  SelectOfScalar[Member]:
    
    statement = select(Member)
    if not current_team_and_user.user.is_superuser:
        statement = statement.join(Team).where(
            or_(
                Team.owner_id == current_team_and_user.user.id,        # Team owner可以访问整个Team的ApiKey
                Member.owner_id == current_team_and_user.user.id       # 其他用户只能访问自己的ApiKey
            )
        ).where(Member.team_id == current_team_and_user.team.id)      # 限制在当前团队内

    return statement


async def current_instance(
    session: SessionDep, id: uuid.UUID, current_team_and_user: CurrentTeamAndUser
) -> Member:
    
    statement = await instance_statement(current_team_and_user)
    statement = statement.where(Member.id == id)

    if not (member := await session.scalar(statement)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    return member


async def validate_name_in(
    session: SessionDep, member_in: Union[MemberCreate, MemberUpdate], current_team_and_user: CurrentTeamAndUser
) -> Member | None:

    if member_in.name in settings.PROTECTED_NAMES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="Name is a protected name. Choose another name."
        )
    statement = select(Member).where(
        Member.name == member_in.name, 
        Member.team_id == current_team_and_user.team.id,
    )
    return await session.scalar(statement)


async def validate_create_in(
    session: SessionDep, member_in: MemberCreate, current_team_and_user: CurrentTeamAndUser
) -> None:
    
    if await validate_name_in(session=session, member_in=member_in, current_team_and_user=current_team_and_user):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Member name already exists")


async def validate_update_in(
    session: SessionDep,  member_in: MemberUpdate, id: uuid.UUID, current_team_and_user: CurrentTeamAndUser
) -> None:
    
    if await validate_name_in(session=session, member_in=member_in, current_team_and_user=current_team_and_user):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Member name already exists")

    return await current_instance(session=session, id=id, current_team_and_user=current_team_and_user)


InstanceStatement = Annotated[SelectOfScalar[Member], Depends(instance_statement)]
CurrentInstance = Annotated[Member, Depends(current_instance)]
ValidateCreateIn = Annotated[None, Depends(validate_create_in)]
ValidateUpdateIn = Annotated[Member, Depends(validate_update_in)]

