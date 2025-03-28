from typing import Any

from fastapi import APIRouter
from sqlmodel import select

from app.api.dependencies import SessionDep, ValidateModelOnRead
from app.api.models import Message, Models, ModelUpdate, ModelCreate, ModelOut

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
    model_filter: ModelFilter = FilterDepends(ModelFilter)
) -> Any:
    """
    List of Models
    """
    statement = select(Models)
    statement = model_filter.filter(statement)
    statement = model_filter.sort(statement)
    return await paginate(session, statement)


@router.post("/", response_model=Models)
async def create_models(model_in: ModelCreate, session: SessionDep) -> Models:
    """
    Create Models
    """
    meta_ = model_in.meta_.copy()
    model = Models.model_validate(model_in, update={"meta_": meta_ or {}})
    session.add(model)
    await session.commit()
    await session.refresh(model)
    return model


@router.put("/{id}", response_model=Models)
async def update_model(model: ValidateModelOnRead, model_in: ModelUpdate, session: SessionDep):
    """
    Update Models
    """
    model.sqlmodel_update(model_in)
    session.add(model)
    await session.commit()
    await session.refresh(model)
    return model


# 新增一个用于更新模型元数据的端点
@router.patch("/{model_id}/metadata", response_model=Models)
async def update_model_metadata(
    model: ValidateModelOnRead, metadata_in: dict[str, Any], session: SessionDep
) -> Models:
    """
    Patch Meta Of Models.
    """
    model.meta_.update(metadata_in)
    session.add(model)
    await session.commit()
    await session.refresh(model)
    return model


@router.delete("/{model_id}", response_model=Models)
async def delete_model(model: ValidateModelOnRead, session: SessionDep) -> Message:
    """
    Delete a provider.
    """
    await session.delete(model)
    await session.commit()
    return Message(message="Api key deleted successfully")
