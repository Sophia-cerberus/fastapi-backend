from typing import Any
import uuid

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.core.security import generate_apikey, generate_short_apikey, get_password_hash

from app.api.models import ApiKey, ApiKeyCreate, ApiKeyOut, ApiKeyOutPublic, Message, Team
from app.api.dependencies import CurrentUser, SessionDep, CurrentTeamAndUser

from fastapi_pagination.ext.sqlmodel import paginate
from fastapi_pagination.links import Page

from fastapi_filter import FilterDepends

from ..filters import ApiKeyFilter


router = APIRouter(
    prefix="/apikey", tags=["apikey"], 
)

@router.get("/{team_id}", response_model=Page[ApiKeyOutPublic])
async def read_api_keys(
    session: SessionDep,
    current_user: CurrentUser,
    team_id: uuid.UUID,
    api_key_filter: ApiKeyFilter = FilterDepends(ApiKeyFilter)
) -> Any:
    """Read api keys"""
    statement = select(ApiKey).where(ApiKey.team_id == team_id)
    if not current_user.is_superuser:
        statement = statement.where(ApiKey.owner_id == current_user.id)

    statement = api_key_filter.filter(statement)
    statement = api_key_filter.sort(statement)
    return await paginate(session, statement)


@router.post("/", response_model=ApiKeyOut)
async def create_api_key(
    session: SessionDep,
    current_team_and_user: CurrentTeamAndUser,
    apikey_in: ApiKeyCreate,
) -> Any:
    
    # Generate API key and hash it
    key = generate_apikey()

    # Create the API key object
    description = apikey_in.description
    apikey = ApiKey(
        team_id=current_team_and_user.team.id,
        hashed_key=get_password_hash(key),
        short_key=generate_short_apikey(key),
        description=None if not description or not description.strip() else description,
    )
    # Save the new API key to the database
    session.add(apikey)
    await session.commit()
    await session.refresh(apikey)
    
    return ApiKeyOut(key=key, **apikey.model_dump())


@router.delete("/{id}")
async def delete_api_key(
    session: SessionDep, current_user: CurrentUser, team_id: uuid.UUID, id: uuid.UUID
) -> Any:
    """Delete API key for a team."""
    statement = (
        select(ApiKey).join(Team).where(ApiKey.id == id, ApiKey.team_id == team_id)
    )
    if not current_user.is_superuser:
        statement = statement.where(Team.owner_id == current_user.id)

    apikey = await session.scalar(statement)

    if not apikey:
        raise HTTPException(status_code=404, detail="Api key not found")
    await session.delete(apikey)
    await session.commit()
    return Message(message="Api key deleted successfully")