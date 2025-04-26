import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks

from sqlmodel import select

from app.api.dependencies import (
    CurrentUser,
    SessionDep,
    get_current_active_superuser,
)
from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.api.models import (
    Team,
    UpdatePassword,
    User,
    UserCreate,
    UserOut,
    UserRegister,
    UserUpdate,
    UserUpdateMe,
    Message,
    UpdateLanguageMe
)
from app.utils.template import generate_new_account_email, send_email
from fastapi_pagination.ext.sqlmodel import paginate
from fastapi_pagination.links import Page

from fastapi_filter import FilterDepends

from ..filters import UserFilter


router = APIRouter(
    prefix="/users", tags=["users"], 
)

@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Page[UserOut]
)
async def read_users(session: SessionDep, user_filter: UserFilter = FilterDepends(UserFilter)) -> Any:
    """
    Retrieve users.
    """
    statement = select(User)
    statement = user_filter.filter(statement)
    statement = user_filter.sort(statement)
    return await paginate(session, statement)


@router.post(
    "/", dependencies=[Depends(get_current_active_superuser)], response_model=UserOut
)
async def create_user(*, session: SessionDep, user_in: UserCreate, background_tasks: BackgroundTasks) -> Any:
    """
    Create new user.
    """
    statement = select(User).where(User.email == user_in.email)
    user = await session.scalar(statement)
    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The user with this email already exists in the system."
        )

    user = User.model_validate(
        user_in, update={"hashed_password": get_password_hash(user_in.password)}
    )
    session.add(user)
    await session.commit()
    await session.refresh(instance=user)

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
    if user_in.email:
        statement = select(User).where(User.email == user_in.email)
        existing_user = await session.scalar(statement)

        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, 
                detail="User with this email already exists"
            )

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
    if current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Super users are not allowed to delete themselves"
        )

    await session.delete(current_user)
    await session.commit()
    return Message(message="User deleted successfully")


@router.post("/signup", response_model=UserOut)
async def register_user(session: SessionDep, user_in: UserRegister) -> Any:
    """
    Create new user without the need to be logged in.
    """
    statement = select(User).where(User.email == user_in.email)
    if await session.scalar(statement):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="The user with this email already exists in the system"
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
    user_id: uuid.UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """Get a specific user by id."""
    if not (user := await session.get(User, user_id)):
        raise HTTPException(status_code=404, detail="User not found")
        
    if not current_user.is_superuser and user != current_user:
        raise HTTPException(status_code=403, detail="Not enough privileges")
        
    return user


@router.patch(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserOut,
)
async def update_user(
    *,
    session: SessionDep,
    user_id: uuid.UUID,
    user_in: UserUpdate,
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

    user.sqlmodel_update(user_in, update={
        "hashed_password": get_password_hash(user_in.password)
    })
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@router.delete("/{user_id}", dependencies=[Depends(get_current_active_superuser)])
async def delete_user(
    session: SessionDep, current_user: CurrentUser, user_id: uuid.UUID
) -> Message:
    """
    Delete a user.
    """
    if not (user := await session.get(User, user_id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found"
        )
    elif user != current_user and not current_user.is_superuser:
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
