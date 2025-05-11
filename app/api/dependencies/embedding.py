from typing import Annotated, Union
import uuid
from fastapi import Depends, HTTPException, status
from sqlmodel import or_, select
from sqlmodel.sql._expression_select_cls import SelectOfScalar

from app.api.models import Embedding, TeamUserJoin, RoleTypes, Team
from app.api.utils.models import StatusTypes

from .team import CurrentTeamAndUser
from .session import SessionDep


async def instance_statement(current_team_and_user: CurrentTeamAndUser, upload_id: uuid.UUID) -> SelectOfScalar[Embedding]:
    """Get a statement to query embeddings with proper access control."""
    statement = select(Embedding)
    if not current_team_and_user.user.is_superuser:
        if current_team_and_user.user.is_tenant_admin:
            statement = statement.join(Team).where(
                Team.tenant_id == current_team_and_user.team.tenant_id
            )
        else:
            statement = statement.join(TeamUserJoin).where(
                TeamUserJoin.user_id == current_team_and_user.user.id,
                TeamUserJoin.status == StatusTypes.ENABLE,
                TeamUserJoin.team_id == current_team_and_user.team.id == Embedding.team_id,
                Embedding.upload_id == upload_id
            ).where(
                or_(
                    TeamUserJoin.role in [RoleTypes.ADMIN, RoleTypes.MODERATOR, RoleTypes.OWNER],
                    Embedding.owner_id == current_team_and_user.user.id
                )
            )      # Restrict to current team
    return statement


async def current_instance(
    session: SessionDep, id: uuid.UUID, upload_id: uuid.UUID, current_team_and_user: CurrentTeamAndUser
) -> Embedding:
    """Get a specific embedding by ID with access control."""
    statement = await instance_statement(current_team_and_user, upload_id)
    statement = statement.where(Embedding.id == id)

    if not (embedding := await session.scalar(statement)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Embedding not found")
    return embedding


# For convenience in route functions
InstanceStatement = Annotated[SelectOfScalar[Embedding], Depends(instance_statement)]
CurrentInstance = Annotated[Embedding, Depends(current_instance)]