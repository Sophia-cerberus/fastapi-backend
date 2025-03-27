import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status, Security
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.models import Item, ItemCreate, ItemPublic, ItemUpdate, Message

from fastapi_pagination.ext.sqlmodel import paginate
from fastapi_pagination.links import Page

from fastapi_filter import FilterDepends

from ..filters import ItemFilter


router = APIRouter(prefix="/items", tags=["items"])


@router.get("/", response_model=Page[ItemPublic])
async def read_items(
    session: SessionDep, current_user: CurrentUser, item_filter: ItemFilter = FilterDepends(ItemFilter)
) -> Any:
    """
    Retrieve items.
    """

    statement = select(Item) 

    if not current_user.is_superuser:
        statement = statement.where(Item.owner_id == current_user.id)

    statement = item_filter.filter(statement)
    statement = item_filter.sort(statement)
    page_items = await paginate(session, statement)
    return page_items


@router.get("/{id}", response_model=ItemPublic)
async def read_item(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Get item by ID.
    """
    item = await session.get(Item, id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    
    return item


@router.post("/", response_model=ItemPublic)
async def create_item(
    *, session: SessionDep, current_user: CurrentUser, item_in: ItemCreate
) -> Any:
    """
    Create new item.
    """
    item = Item.model_validate(item_in, update={"owner_id": current_user.id})
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


@router.put("/{id}", response_model=ItemPublic)
async def update_item(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    item_in: ItemUpdate,
) -> Any:
    """
    Update an item.
    """
    item = await session.get(Item, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    update_dict = item_in.model_dump(exclude_unset=True)
    item.sqlmodel_update(update_dict)
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


@router.delete("/{id}", response_model=Message)
async def delete_item(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete an item.
    """
    item = await session.get(Item, id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    await session.delete(item)
    await session.commit()
    return Message(message="Item deleted successfully")
