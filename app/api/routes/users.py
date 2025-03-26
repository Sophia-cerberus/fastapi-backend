import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import col, delete, func, select

from app import crud
from app.api.deps import (
    CurrentUser,
    SessionDep,
    get_current_active_superuser,
)
from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models import (
    Item,
    UpdatePassword,
    User,
    UserCreate,
    UserPublic,
    UserRegister,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
    Message
)
from app.utils import generate_new_account_email, send_email


router = APIRouter(prefix="/users", tags=["users"])

@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPublic,
)
async def read_users(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve users.
    """

    count_statement = select(func.count()).select_from(User)
    count = await session.scalar(count_statement)

    statement = select(User).offset(skip).limit(limit)
    users = (await session.scalars(statement)).all()
    
    return UsersPublic(data=users, count=count)


@router.post(
    "/", dependencies=[Depends(get_current_active_superuser)], response_model=UserPublic
)
async def create_user(*, session: SessionDep, user_in: UserCreate) -> Any:
    """
    Create new user.
    """
    user = await crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="The user with this email already exists in the system."
        )

    user = await crud.create_user(session=session, user_create=user_in)
    if settings.emails_enabled and user_in.email:
        email_data = generate_new_account_email(
            email_to=user_in.email, username=user_in.email, password=user_in.password
        )
        send_email(
            email_to=user_in.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    return user


@router.patch("/me", response_model=UserPublic)
async def update_user_me(
    *, session: SessionDep, user_in: UserUpdateMe, current_user: CurrentUser
) -> Any:
    """
    Update own user.
    """

    if user_in.email:
        existing_user = await crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != current_user.id:
            return HTTPException(
                status_code=status.HTTP_409_CONFLICT, 
                message="User with this email already exists"
            )

    user_data = user_in.model_dump(exclude_unset=True)
    current_user.sqlmodel_update(user_data)
    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)
    return user_data


@router.patch("/me/password", response_model=Message)
async def update_password_me(
    *, session: SessionDep, body: UpdatePassword, current_user: CurrentUser
) -> Any:
    """
    Update own password.
    """
    if not verify_password(body.current_password, current_user.hashed_password):
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, message="Incorrect password")
    
    if body.current_password == body.new_password:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            message="New password cannot be the same as the current one"
        )

    hashed_password = get_password_hash(body.new_password)
    current_user.hashed_password = hashed_password
    session.add(current_user)
    await session.commit()
    return Message(message="Password updated successfully")


@router.get("/me", response_model=UserPublic)
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
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            message="Super users are not allowed to delete themselves"
        )

    await session.delete(current_user)
    await session.commit()
    return Message(message="User deleted successfully")


@router.post("/signup", response_model=UserPublic)
async def register_user(session: SessionDep, user_in: UserRegister) -> Any:
    """
    Create new user without the need to be logged in.
    """
    user = await crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            message="The user with this email already exists in the system"
        )

    user_create = UserCreate.model_validate(user_in)
    user = await crud.create_user(session=session, user_create=user_create)
    return user


@router.get("/{user_id}", response_model=UserPublic)
async def read_user_by_id(
    user_id: uuid.UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """
    Get a specific user by id.
    """
    user = await session.get(User, user_id)
    if user == current_user:
        return user
    if not current_user.is_superuser:
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            message="The user doesn't have enough privileges"
        )

    return user


@router.patch(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPublic,
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

    db_user = await session.get(User, user_id)
    if not db_user:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            message="The user with this id does not exist in the system"
        )
    
    if user_in.email:
        existing_user = await crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != user_id:
            return HTTPException(
                status_code=status.HTTP_409_CONFLICT, 
                message="User with this email already exists"
            )

    user = await crud.update_user(session=session, db_user=db_user, user_in=user_in)
    return user


@router.delete("/{user_id}", dependencies=[Depends(get_current_active_superuser)])
async def delete_user(
    session: SessionDep, current_user: CurrentUser, user_id: uuid.UUID
) -> Message:
    """
    Delete a user.
    """
    user = await session.get(User, user_id)
    if not user:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            message="User not found"
        )
    if user == current_user:
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            message="Super users are not allowed to delete themselves"
        )
    statement = delete(Item).where(col(Item.owner_id) == user_id)
    await session.execute(statement)  # type: ignore
    await session.delete(user)
    await session.commit()
    return Message(message="User deleted successfully")
