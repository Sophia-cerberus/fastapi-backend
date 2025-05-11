from typing import Any

from fastapi import APIRouter, Depends

from app.api.dependencies import (
    SessionDep,
    get_current_active_superuser,
    CurrentInstanceTenant, InstanceStatementTenant,
    ValidateCreateInTenant, ValidateUpdateOnTenant
)
from app.api.models import (
    Message,
    TenantUpdate,
    Tenant,
    TenantCreate,
    TenantOut,
)
from fastapi_pagination.ext.sqlmodel import paginate
from fastapi_pagination.links import Page

from fastapi_filter import FilterDepends

from ..filters import TenantFilter


router = APIRouter(
    prefix="/tenant", tags=["tenant"], 
)

@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Page[TenantOut]
)
async def read_tenants(
    session: SessionDep, 
    statement: InstanceStatementTenant,
    tenant_filter: TenantFilter = FilterDepends(TenantFilter)
) -> Any:
    """
    Retrieve tenants.
    """
    statement = tenant_filter.filter(statement)
    statement = tenant_filter.sort(statement)
    return await paginate(session, statement)


@router.post(
    "/", response_model=TenantOut
)
async def create_tenant(
    *, 
    session: SessionDep, 
    tenant_in: TenantCreate,
    _: ValidateCreateInTenant
) -> Any:
    """
    Create new tenant.
    """
    tenant: Tenant = Tenant.model_validate(tenant_in)
    session.add(tenant)
    await session.commit()
    await session.refresh(tenant)
    return tenant



@router.get("/{user_id}", response_model=TenantOut)
async def read_tenant_by_id(
    tenant: CurrentInstanceTenant
) -> Any:
    """Get a specific tenant by id."""
    return tenant


@router.patch(
    "/{user_id}",
    response_model=TenantOut,
)
async def update_user(
    *,
    session: SessionDep,
    tenant: ValidateUpdateOnTenant,
    tenant_in: TenantUpdate,
) -> Any:
    """
    Update a Tenant.
    """
    tenant.sqlmodel_update(tenant_in)
    session.add(tenant)
    await session.commit()
    await session.refresh(tenant)
    return tenant


@router.delete("/{user_id}")
async def delete_user(
    session: SessionDep,
    tenant: CurrentInstanceTenant
) -> Message:
    """
    Delete a Tenant.
    """
    await session.delete(tenant)
    await session.commit()
    return Message(message="Graph deleted successfully")
