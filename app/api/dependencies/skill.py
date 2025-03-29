from typing import Annotated
import uuid

from fastapi import Depends, HTTPException, status
from sqlmodel import or_, select

from app.api.models import Skill, SkillUpdate, Team
from app.core.config import settings

from .session import SessionDep
from .team import CurrentTeamAndUser


async def current_instance(
    session: SessionDep, id: uuid.UUID, current_team_and_user: CurrentTeamAndUser
) -> Skill:
    
    statement = select(Skill).where(Skill.team_id == current_team_and_user.team.id, Skill.id == id)
    if not current_team_and_user.user.is_superuser:
        statement = statement.where(
            or_(
                Skill.owner_id == current_team_and_user.user.id, 
                Skill.is_public == True,
                Team.owner_id == current_team_and_user.user.id,
            )
        )

    if not (skill := await session.scalar(statement)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    return skill


async def validate_update_in(
    session: SessionDep,  skill_in: SkillUpdate, id: uuid.UUID, current_team_and_user: CurrentTeamAndUser
) -> None:
    """Check if (name, team_id) is unique and name is not a protected name"""
    if skill_in.name in settings.PROTECTED_NAMES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Name is a protected name. Choose another name."
        )
    statement = select(Skill).where(
        Skill.name == skill_in.name, Skill.id != id,
        Skill.team_id == current_team_and_user.team.id,
    )
    if await session.scalar(statement):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Member name already exists")
    
    return await current_instance(session=session, id=id, current_team_and_user=current_team_and_user)


CurrentInstance = Annotated[Skill, Depends(current_instance)]
ValidateUpdateIn = Annotated[Skill, Depends(validate_update_in)]
