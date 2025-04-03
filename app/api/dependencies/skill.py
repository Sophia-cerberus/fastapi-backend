from typing import Annotated, Union
import uuid

from fastapi import Depends, HTTPException, status
from sqlmodel import or_, select
from sqlmodel.sql._expression_select_cls import SelectOfScalar

from app.api.models import Skill, SkillUpdate, Team, SkillCreate
from app.core.config import settings

from .session import SessionDep
from .team import CurrentTeamAndUser


async def instance_statement(current_team_and_user: CurrentTeamAndUser) ->  SelectOfScalar[Skill]:
    
    statement = select(Skill)
    if not current_team_and_user.user.is_superuser:
        statement = statement.join(Team).where(
            or_(
                Team.owner_id == current_team_and_user.user.id,        # Team owner可以访问整个Team的ApiKey
                Skill.owner_id == current_team_and_user.user.id,       # 其他用户只能访问自己的ApiKey
                Skill.is_public == True
            )
        ).where(Skill.team_id == current_team_and_user.team.id)      # 限制在当前团队内

    return statement


async def current_instance(
    session: SessionDep, id: uuid.UUID, current_team_and_user: CurrentTeamAndUser
) -> Skill:
    
    statement = await instance_statement(current_team_and_user)
    statement = statement.where(Skill.id == id)

    if not (skill := await session.scalar(statement)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    return skill


async def validate_name_in(
    session: SessionDep, skill_in: Union[SkillUpdate, SkillCreate], current_team_and_user: CurrentTeamAndUser
) -> Skill | None:

    if skill_in.name in settings.PROTECTED_NAMES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="Name is a protected name. Choose another name."
        )
    statement = select(Skill).where(
        Skill.name == skill_in.name, 
        Skill.team_id == current_team_and_user.team.id,
    )
    return await session.scalar(statement)


async def validate_update_in(
    session: SessionDep,  skill_in: SkillUpdate, id: uuid.UUID, current_team_and_user: CurrentTeamAndUser
) -> None:
    if await validate_name_in(session=session, skill_in=skill_in, current_team_and_user=current_team_and_user):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Member name already exists")

    return await current_instance(session=session, id=id, current_team_and_user=current_team_and_user)


InstanceStatement = Annotated[SelectOfScalar[Skill], Depends(instance_statement)]
CurrentInstance = Annotated[Skill, Depends(current_instance)]
ValidateUpdateIn = Annotated[Skill, Depends(validate_update_in)]
