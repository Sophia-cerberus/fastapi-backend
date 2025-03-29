from typing import Any
from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.dependencies import SessionDep, CurrentInstanceProvider, CurrentTeamAndUser
from app.core.providers import model_provider_manager
from app.api.crud.provider import (
    sync_provider_models,
)
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
async def read_provider_list_with_models(
    session: SessionDep,
    _: CurrentTeamAndUser,
    provider_filter: ProviderFilter = FilterDepends(ProviderFilter)
) -> Any:

    statement = select(ModelProvider)
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


# 新增：同步提供者的模型配置到数据库
@router.post("/{id}/sync", response_model=list[str])
async def sync_provider(
    provider: CurrentInstanceProvider,
    session: SessionDep,
):
    """
    Provider Sync to Models
    """
    config_models = model_provider_manager.get_supported_models(provider.provider_name)
    if not config_models:
        raise HTTPException(
            status_code=404,
            detail=f"No models found in configuration for provider {provider.provider_name}",
        )

    # 同步模型到数据库
    synced_models = await sync_provider_models(session, provider.id, config_models)

    return [model.ai_model_name for model in synced_models]