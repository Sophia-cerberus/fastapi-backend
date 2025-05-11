
# We'll declare the type hint annotation here but define the actual function in team.py
# This breaks the circular dependency

from typing import Annotated, AsyncGenerator
from app.core.storage.s3 import StorageClient

import uuid
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError
from sqlmodel import SQLModel
from fastapi import Depends, HTTPException, status
from app.api.dependencies.session import SessionDep
from app.api.utils.models import StatusTypes
from app.core import security
from app.core.config import settings
from app.api.models import Team, User, TokenPayload
import jwt
from jwt.exceptions import InvalidTokenError


reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/token"
)

TokenDep = Annotated[str, Depends(reusable_oauth2)]


async def get_current_user(session: SessionDep, token: TokenDep) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)

        if token_data.type != security.TokenType.ACCESS_TOKEN.value:
            raise InvalidTokenError

    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )

    user = await session.get(User, token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.status != StatusTypes.ENABLE:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


CurrentUser = Annotated[User, Depends(dependency=get_current_user)]


class TeamAndUser(SQLModel):
    team: Team
    user: User


async def get_current_team_and_user(
    session: SessionDep,
    team_id: uuid.UUID,
    current_user: CurrentUser,
) -> TeamAndUser:
    """Return team if apikey belongs to it"""
    if not (team := await session.get(Team, team_id)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return TeamAndUser(team=team, user=current_user)


CurrentTeamAndUser = Annotated[TeamAndUser, Depends(get_current_team_and_user)]


def get_current_active_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user


CurrentActiveSuperuser = Annotated[User, Depends(get_current_active_superuser)]


async def get_storage_client() -> AsyncGenerator[StorageClient, None]:
    async with StorageClient() as client:
        yield client


StorageClientDep = Annotated[StorageClient, Depends(get_storage_client)]