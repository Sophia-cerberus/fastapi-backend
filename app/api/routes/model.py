from typing import Any

from fastapi import APIRouter
from sqlmodel import select

from app.api.dependencies import SessionDep, CurrentInstanceModel, CurrentTeamAndUser, ValidateUpdateInModel, InstanceStatementModel
from app.api.models import Message, ModelCreate, Model, ModelOut, ModelUpdate

from fastapi_pagination.ext.sqlmodel import paginate
from fastapi_pagination.links import Page

from fastapi_filter import FilterDepends

from ..filters import ModelFilter


router = APIRouter(
    prefix="/model", tags=["model"], 
)


@router.get("/", response_model=Page[ModelOut])
async def read_models(
    session: SessionDep,
    statement: InstanceStatementModel,
    model_filter: ModelFilter = FilterDepends(ModelFilter),
) -> Any:
    """
    List of Models
    """
    statement = model_filter.filter(statement)
    statement = model_filter.sort(statement)
    return await paginate(session, statement)


@router.post("/", response_model=Model)
async def create_models(
    ai_model_in: ModelCreate, session: SessionDep, 
    current_team_and_user: CurrentTeamAndUser) -> Model:
    """
    Create Models
    """
    meta_ = ai_model_in.meta_.copy()
    model = Model.model_validate(ai_model_in, update={
        "meta_": meta_ or {},
        "owner_id": current_team_and_user.user.id,
        "team_id": current_team_and_user.team.id
    })
    session.add(model)
    await session.commit()
    await session.refresh(model)
    return model


@router.get("/{id}", response_model=Model)
async def read_model(model: CurrentInstanceModel) -> ModelOut:
    """
    Retrieve Model
    """
    return model
    

@router.put("/{id}", response_model=ModelOut)
async def update_model(
    model: ValidateUpdateInModel, ai_model_in: ModelUpdate, session: SessionDep
) -> Any:
    """
    Update Models
    """
    model.sqlmodel_update(ai_model_in)
    session.add(model)
    await session.commit()
    await session.refresh(model)
    return model


# 新增一个用于更新模型元数据的端点
@router.patch("/{id}/metadata", response_model=ModelOut)
async def update_model_metadata(
    model: ValidateUpdateInModel, metadata_in: dict[str, Any], session: SessionDep
) -> Any:
    """
    Patch Meta Of Models.
    """
    model.meta_.update(metadata_in)
    session.add(model)
    await session.commit()
    await session.refresh(model)
    return model


@router.delete("/{id}", response_model=Message)
async def delete_model(model: CurrentInstanceModel, session: SessionDep) -> Message:
    """
    Delete a provider.
    """
    await session.delete(model)
    await session.commit()
    return Message(message="Api key deleted successfully")
