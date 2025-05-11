from typing import Annotated
import uuid
from sqlmodel import select
from sqlmodel.sql._expression_select_cls import SelectOfScalar

from typing_extensions import Annotated

from fastapi import Depends, HTTPException, status


from app.api.utils.models import StatusTypes
from app.api.models import User, TeamUserJoin, Team, RoleTypes

from .session import SessionDep
from .common import CurrentTeamAndUser


async def instance_statement(
    current_team_and_user: CurrentTeamAndUser
) -> SelectOfScalar[User]:

    statement: SelectOfScalar[User] = select(User).where(User.id != current_team_and_user.user.id)
    
    if not current_team_and_user.user.is_superuser:
        # 通过团队-用户关联表和团队表联查
        statement = statement.join(
            TeamUserJoin, User.id == TeamUserJoin.user_id
        ).join(
            Team, TeamUserJoin.team_id == Team.id
        ).where(
            Team.tenant_id == current_team_and_user.team.tenant_id,
            TeamUserJoin.status == StatusTypes.ENABLE
        )
    return statement


async def current_instance(
    session: SessionDep, 
    id: uuid.UUID, 
    current_team_and_user: CurrentTeamAndUser
) -> User:

    statement: SelectOfScalar[User] = await instance_statement(current_team_and_user)
    statement = statement.where(
        User.id == id, 
        TeamUserJoin.team_id == current_team_and_user.team.id
    )

    user = await session.scalar(statement)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


async def check_user_permission(
    session: SessionDep,
    id: uuid.UUID, 
    current_team_and_user: CurrentTeamAndUser
) -> None:
    
    if id == current_team_and_user.user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot operate on your own account through this endpoint"
        )    

    statement: SelectOfScalar[User] = await instance_statement(current_team_and_user)
    statement = statement.where(User.id == id)

    user = await session.scalar(statement)

    if not user: raise HTTPException(status_code=404, detail="User not found")

    if not current_team_and_user.user.is_superuser:

        if current_team_and_user.user.is_tenant_admin and user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No permission to operate on superuser account"
            )
        else:

            # 普通用户或团队管理员，需检查团队角色
            team_role_statement = select(TeamUserJoin.role).where(
                TeamUserJoin.user_id == current_team_and_user.user.id,  
                TeamUserJoin.team_id == current_team_and_user.team.id,
                TeamUserJoin.status == StatusTypes.ENABLE
            )
            user_role = await session.scalar(team_role_statement)
            
            target_role_statement = select(TeamUserJoin.role).where(
                TeamUserJoin.user_id == id,
                TeamUserJoin.team_id == current_team_and_user.team.id,
                TeamUserJoin.status == StatusTypes.ENABLE

            )
            target_role = await session.scalar(target_role_statement)

            if not target_role: raise HTTPException(status_code=404, detail="Target user is not in your team")

            if user_role == RoleTypes.ADMIN:
                if target_role in [RoleTypes.OWNER, RoleTypes.ADMIN]:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="No permission to operate on owner or admin account"
                    )
            elif user_role == RoleTypes.MODERATOR:
                if target_role in [RoleTypes.OWNER, RoleTypes.ADMIN, RoleTypes.MODERATOR]:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="No permission to operate on owner, admin or moderator account"
                    )
                
            elif user_role == RoleTypes.MEMBER:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No permission to operate on user accounts"
                )
            
            elif user_role == RoleTypes.OWNER:
                # Team owners have full permissions to modify any user in their team
                # No additional restrictions needed here
                pass

            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No permission to operate on this user"
                )
    return user


InstanceStatement = Annotated[SelectOfScalar[User], Depends(instance_statement)]
CurrentInstance = Annotated[User, Depends(current_instance)]
CheckUserUpdatePermission = Annotated[User, Depends(check_user_permission)]