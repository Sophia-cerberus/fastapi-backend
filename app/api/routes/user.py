import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status, BackgroundTasks

from sqlmodel import or_, select

from app.api.dependencies import (
    CurrentUser,
    SessionDep,
    CurrentTeamAndUser,
    InstanceStatementUsers,
    CurrentInstanceUser,
)
from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.api.models import (
    TeamUserJoin,
    UpdatePassword,
    User,
    UserCreate,
    UserOut,
    UserRegister,
    UserUpdate,
    UserUpdateMe,
    Message,
    UpdateLanguageMe,
    RoleTypes
)
from app.utils.template import generate_new_account_email, send_email
from fastapi_pagination.ext.sqlmodel import paginate
from fastapi_pagination.links import Page

from fastapi_filter import FilterDepends

from ..filters import UserFilter


router = APIRouter(
    prefix="/users", tags=["users"], 
)

@router.get("/", response_model=Page[UserOut])
async def read_users(
    session: SessionDep, 
    statement: InstanceStatementUsers,
    user_filter: UserFilter = FilterDepends(UserFilter)
) -> Any:
    """
    Get user list.
    """
    statement = user_filter.filter(statement)
    statement = user_filter.sort(statement)
    return await paginate(session, statement)


@router.post("/", response_model=UserOut)
async def create_user(
    *, 
    session: SessionDep, 
    current_team_and_user: CurrentTeamAndUser,
    user_in: UserCreate, 
    background_tasks: BackgroundTasks
) -> Any:
    """
    Create a new user.
    """
    # 检查邮箱是否已存在
    statement = select(User).where(
        or_(
            User.email == user_in.email,
            User.phone == user_in.phone
        )
    )
    user = await session.scalar(statement)
    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The user with this email already exists in the system."
        )

    # 权限检查
    if not current_team_and_user.user.is_superuser and not current_team_and_user.user.is_tenant_admin:
        # 检查当前用户在团队中的角色
        user_role_statement = select(TeamUserJoin.role).where(
            TeamUserJoin.user_id == current_team_and_user.user.id,
            TeamUserJoin.team_id == current_team_and_user.team.id
        )
        user_role = await session.scalar(user_role_statement)
        
        if not user_role or user_role not in [RoleTypes.ADMIN, RoleTypes.OWNER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only team admins or owners can create new users"
            )

    # 创建用户
    user = User.model_validate(
        user_in, update={"hashed_password": get_password_hash(user_in.password)}
    )
    
    session.add(user)
    await session.commit()
    await session.refresh(instance=user)

    # 为非超级管理员创建的用户，自动添加到当前团队
    if not current_team_and_user.user.is_superuser:
        team_user = TeamUserJoin(
            team_id=current_team_and_user.team.id,
            user_id=user.id,
            role=RoleTypes.MEMBER,
            status=user.status,
            invite_by=current_team_and_user.user.id,
            # 这里需要创建或获取一个邀请码
            invite_code=uuid.uuid4()  # 这里简化处理，实际应该创建一个真实的邀请码
        )
        session.add(team_user)
        await session.commit()

    # 发送欢迎邮件
    if settings.emails_enabled and user_in.email:
        email_data = generate_new_account_email(
            email_to=user_in.email, username=user_in.email, password=user_in.password
        )
        background_tasks.add_task(
        send_email,
            email_to=user_in.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    return user


@router.patch("/me/language", response_model=UserOut)
async def update_user_language(
    *, session: SessionDep, language_update: UpdateLanguageMe, current_user: CurrentUser
) -> Any:
    """
    Update the language of the current user.
    """
    # 更新用户的语言字段
    current_user.language = language_update.language

    # 提交更改到数据库
    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)

    return current_user


@router.patch("/me", response_model=UserOut)
async def update_user_me(
    *, session: SessionDep, user_in: UserUpdateMe, current_user: CurrentUser
) -> Any:
    """
    Update own user.
    """
    current_user.sqlmodel_update(user_in)
    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)
    return current_user


@router.patch("/me/password", response_model=Message)
async def update_password_me(
    *, session: SessionDep, body: UpdatePassword, current_user: CurrentUser
) -> Any:
    """
    Update own password.
    """
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")
    
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="New password cannot be the same as the current one"
        )

    hashed_password = get_password_hash(body.new_password)
    current_user.hashed_password = hashed_password
    session.add(current_user)
    await session.commit()
    return Message(message="Password updated successfully")


@router.get("/me", response_model=UserOut)
def read_user_me(current_user: CurrentUser) -> Any:
    """
    Get current user.
    """
    return current_user


@router.delete("/me", response_model=Message)
async def delete_user_me(session: SessionDep, current_user: CurrentUser) -> Any:
    """
    Delete own user.
    """
    if current_user.is_superuser or current_user.is_tenant_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Super users and tenant admins are not allowed to delete themselves"
        )

    await session.delete(current_user)
    await session.commit()
    return Message(message="User deleted successfully")


@router.post("/signup", response_model=UserOut)
async def register_user(session: SessionDep, user_in: UserRegister) -> Any:
    """
    Create new user without the need to be logged in.
    """
    statement = select(User).where(
        or_(
            User.email == user_in.email,
            User.phone == user_in.phone
        )
    )
    if await session.scalar(statement):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="The user with this email or phone already exists in the system"
        )

    user = User.model_validate(
        user_in, update={"hashed_password": get_password_hash(user_in.password)}
    )
    session.add(user)
    await session.commit()
    await session.refresh(instance=user)
    return user


@router.get("/{user_id}", response_model=UserOut)
async def read_user_by_id(
    user: CurrentInstanceUser
) -> Any:
    """Get a specific user by id."""

    return user


@router.patch(
    "/{user_id}",
    response_model=UserOut,
)
async def update_user(
    *,
    session: SessionDep,
    user_id: uuid.UUID,
    user_in: UserUpdate,
    user: CheckUserUpdatePermission,
) -> Any:
    """
    Update a user.
    """
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="The user with this id does not exist in the system"
        )
    
    if user_in.email:
        statement = select(User).where(User.email == user_in.email)
        existing_user = await session.scalar(statement)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, 
                detail="User with this email already exists"
            )

    update_data = {}
    if user_in.password:
        update_data["hashed_password"] = get_password_hash(user_in.password)
    
    user.sqlmodel_update(user_in, update=update_data)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@router.delete("/{user_id}")
async def delete_user(
    session: SessionDep, user: CurrentInstanceUser, current_user: CurrentUser
) -> Message:
    """
    Delete a user.
    """

    if user != current_user and not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    if user == current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Super users are not allowed to delete themselves"
        )
    await session.delete(user)
    await session.commit()
    return Message(message="User deleted successfully")
