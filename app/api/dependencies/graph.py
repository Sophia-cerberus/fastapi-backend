
from typing import Annotated, Union
import uuid
from fastapi import Depends, HTTPException, status
from sqlmodel import or_, select
from sqlmodel.sql._expression_select_cls import SelectOfScalar

from app.api.models import Graph, GraphCreate, GraphUpdate, TeamUserJoin, RoleTypes, Team
from app.api.utils.models import StatusTypes
from app.core.config import settings

from .team import CurrentTeamAndUser
from .session import SessionDep


async def instance_statement(current_team_and_user: CurrentTeamAndUser) ->  SelectOfScalar[Graph]:
    
    statement: SelectOfScalar[Graph] = select(Graph)
    if not current_team_and_user.user.is_superuser:
        if current_team_and_user.user.is_tenant_admin:
            statement = statement.join(Team).where(
                Team.tenant_id == current_team_and_user.team.tenant_id
            )
        else:
            statement = statement.join(TeamUserJoin).where(
                TeamUserJoin.user_id == current_team_and_user.user.id,
                TeamUserJoin.status == StatusTypes.ENABLE,
                TeamUserJoin.team_id == current_team_and_user.team.id == Graph.team_id,
            ).where(
                or_(
                    TeamUserJoin.role in [RoleTypes.ADMIN, RoleTypes.MODERATOR, RoleTypes.OWNER],
                    Graph.owner_id == current_team_and_user.user.id,
                    Graph.is_public == True
                )
            )      # 限制在当前团队内

    return statement


async def current_instance(
    session: SessionDep, id: uuid.UUID, current_team_and_user: CurrentTeamAndUser
) -> Graph:

    statement = await instance_statement(current_team_and_user)
    statement = statement.where(Graph.id == id)

    if not (graph := await session.scalar(statement)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Graph not found")
    return graph


async def validate_name_in(
    session: SessionDep, graph_in: Union[GraphCreate, GraphUpdate], current_team_and_user: CurrentTeamAndUser
) -> Graph | None:

    if graph_in.name in settings.PROTECTED_NAMES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="Name is a protected name. Choose another name."
        )
    statement = select(Graph).where(
        Graph.name == graph_in.name, 
        Graph.team_id == current_team_and_user.team.id,
    )
    return await session.scalar(statement)


async def validate_create_in(
    session: SessionDep, graph_in: GraphCreate, current_team_and_user: CurrentTeamAndUser
) -> None:
    
    if await validate_name_in(session=session, graph_in=graph_in, current_team_and_user=current_team_and_user):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Graph name already exists")


async def validate_update_in(
    session: SessionDep, graph_in: GraphUpdate, id: uuid.UUID, current_team_and_user: CurrentTeamAndUser
) -> None:
    
    if await validate_name_in(session=session, graph_in=graph_in, current_team_and_user=current_team_and_user):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Graph name already exists")

    return await current_instance(session=session, id=id, current_team_and_user=current_team_and_user)


InstanceStatement = Annotated[SelectOfScalar[Graph], Depends(instance_statement)]
CurrentInstance = Annotated[Graph, Depends(current_instance)]
ValidateCreateIn = Annotated[None, Depends(validate_create_in)]
ValidateUpdateIn = Annotated[Graph, Depends(validate_update_in)]
