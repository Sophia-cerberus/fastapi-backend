from typing import Any

from fastapi import APIRouter, Depends
from sqlmodel import select

from app.api.dependencies import (
    CurrentUser, SessionDep, ValidateSubGraphOnRead, ValidateSubGraphOnUpdate, 
    validate_subgraph_name_on_create
)
from app.api.models import (
    Message,
    Subgraph,
    SubgraphCreate,
    SubgraphOut,
    SubgraphUpdate,
)

from fastapi_pagination.ext.sqlmodel import paginate
from fastapi_pagination.links import Page

from fastapi_filter import FilterDepends

from ..filters import SubgraphFilter

router = APIRouter(
    prefix="/subgraph", tags=["subgraph"], 
)


@router.get("/", response_model=Page[SubgraphOut])
async def read_all_public_subgraphs(
    session: SessionDep, current_user: CurrentUser, 
    subgraph_filter: SubgraphFilter = FilterDepends(SubgraphFilter)
) -> Any:
    """
    Retrieve all public subgraphs.
    """
    statement = select(Subgraph)
    if not current_user.is_superuser:
        statement = statement.where(
            Subgraph.owner_id == current_user.id, Subgraph.is_public == True
        )

    statement = subgraph_filter.filter(statement)
    statement = subgraph_filter.sort(statement)
    return await paginate(session, statement)


@router.get("/{id}", response_model=SubgraphOut)
def read_subgraph(
    subgraph: ValidateSubGraphOnRead
) -> Any:
    """
    Get subgraph by ID.
    """
    return subgraph


@router.post("/", response_model=SubgraphOut)
async def create_subgraph(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    _: bool = Depends(validate_subgraph_name_on_create),
    subgraph_in: SubgraphCreate,
) -> Any:
    """
    Create new subgraph.
    """

    subgraph = Subgraph.model_validate(
        subgraph_in, update={"owner_id": current_user.id}
    )
    session.add(subgraph)
    await session.commit()
    await session.refresh(subgraph)
    return subgraph


@router.put("/{id}", response_model=SubgraphOut)
async def update_subgraph(
    *,
    session: SessionDep,
    subgraph: ValidateSubGraphOnUpdate,
    subgraph_in: SubgraphUpdate,
) -> Any:
    """
    Update subgraph by ID.
    """
    subgraph.sqlmodel_update(subgraph_in)
    session.add(subgraph)
    await session.commit()
    await session.refresh(subgraph)
    return subgraph


@router.delete("/{id}")
async def delete_subgraph(
    session: SessionDep,
    subgraph: ValidateSubGraphOnRead,
) -> Message:
    """
    Delete subgraph by ID.
    """
    await session.delete(subgraph)
    await session.commit()
    return Message(message="Subgraph deleted successfully")