from typing import Any

from fastapi import APIRouter

from app.api.dependencies import (
    SessionDep, CurrentTeamAndUser, CurrentInstanceDataset, 
    ValidateCreateInDataset, ValidateUpdateInDataset, InstanceStatementDataset
)
from app.api.models import Dataset, DatasetCreate, DatasetOut, DatasetUpdate, Message

from fastapi_pagination.ext.sqlmodel import paginate
from fastapi_pagination.links import Page

from fastapi_filter import FilterDepends

from ..filters import DatasetFilter

router = APIRouter(prefix="/dataset", tags=["dataset"])


@router.get("/", response_model=Page[DatasetOut])
async def read_datasets(
    session: SessionDep,
    statement: InstanceStatementDataset,
    dataset_filter: DatasetFilter = FilterDepends(DatasetFilter)
) -> Any:
    """
    Retrieve datasets from team.
    """
    statement = dataset_filter.filter(statement)
    statement = dataset_filter.sort(statement)
    return await paginate(session, statement)


@router.get("/{id}", response_model=DatasetOut)
async def read_dataset(dataset: CurrentInstanceDataset) -> Any:
    """
    Get dataset by ID.
    """
    return dataset


@router.post("/", response_model=DatasetOut)
async def create_dataset(
    *,
    session: SessionDep,
    current_team_and_user: CurrentTeamAndUser,
    dataset_in: DatasetCreate,
    _: ValidateCreateInDataset,
) -> Any:
    """
    Create new dataset.
    """
    dataset = Dataset.model_validate(dataset_in, update={
        "team_id": current_team_and_user.team.id, 
        "owner_id": current_team_and_user.user.id
    })
    session.add(dataset)
    await session.commit()
    await session.refresh(dataset)
    return dataset


@router.put("/{id}", response_model=DatasetOut)
async def update_dataset(
    *,
    session: SessionDep,
    dataset: ValidateUpdateInDataset,
    dataset_in: DatasetUpdate,
) -> Any:
    """
    Update dataset by ID.
    """        
    dataset.sqlmodel_update(dataset_in)
    session.add(dataset)
    await session.commit()
    await session.refresh(dataset)
    return dataset


@router.delete("/{id}")
async def delete_dataset(
    session: SessionDep,
    dataset: CurrentInstanceDataset
) -> None:
    """
    Delete dataset by ID.
    All child datasets and uploads will be deleted due to cascade delete.
    """
    await session.delete(dataset)
    await session.commit()
    return Message(message="Dataset deleted successfully")
