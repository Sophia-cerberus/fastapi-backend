from typing import Any
from fastapi import APIRouter


from app.api.dependencies import SessionDep, CurrentInstanceProvider, CurrentTeamAndUser, InstanceStatementProvider
from app.api.models import (
    Message,
    ModelProvider,
    ModelProviderCreate,
    ModelProviderOut,
    ModelProviderUpdate,
)

from fastapi_pagination.ext.sqlmodel import paginate
from fastapi_pagination.links import Page

from fastapi_filter import FilterDepends

from ..filters import ProviderFilter


router = APIRouter(
    prefix="/provider", tags=["provider"], 
)

@router.get("/", response_model=Page[ModelProviderOut])
async def read_providers(
    session: SessionDep,
    statement: InstanceStatementProvider,
    provider_filter: ProviderFilter = FilterDepends(ProviderFilter)
) -> Any:
    """
    List of Providers
    """
    statement = provider_filter.filter(statement)
    statement = provider_filter.sort(statement)
    return await paginate(session, statement)


@router.get("/{id}", response_model=ModelProviderOut)
async def read_provider(provider: CurrentInstanceProvider) -> ModelProvider:
    """
    Get provider by ID.
    """
    return provider


# Routes for ModelProvider
@router.post("/", response_model=ModelProvider)
async def create_provider(
    model_provider: ModelProviderCreate, session: SessionDep,
    current_team_and_user: CurrentTeamAndUser,
) -> Any:
    provider = ModelProvider.model_validate(model_provider, update={
        "team_id": current_team_and_user.team.id,
        "owner_id": current_team_and_user.user.id
    })
    provider.set_api_key(model_provider.api_key)
    session.add(provider)
    await session.commit()
    await session.refresh(provider)
    return provider


@router.put("/{id}", response_model=ModelProviderOut)
async def update_provider(
    provider: CurrentInstanceProvider,
    provider_in: ModelProviderUpdate,
    session: SessionDep,
) -> ModelProvider:
    """
    Update a provider.
    """

    provider.sqlmodel_update(provider_in)

    if api_key := provider_in.api_key:
        provider.set_api_key(api_key)

    session.add(provider)
    await session.commit()
    await session.refresh(provider)
    return provider


@router.delete("/{id}", response_model=ModelProvider)
async def delete_provider(provider: CurrentInstanceProvider, session: SessionDep):
    """
    Delete a provider.
    """
    await session.delete(provider)
    await session.commit()
    return Message(message="Api key deleted successfully")
