from typing import Optional
import uuid

from app.api.models import Tenant

from fastapi_filter.contrib.sqlalchemy import Filter

from app.api.models.tenant import TenantPlan
from app.api.utils.models import StatusTypes



class TenantFilter(Filter):
    name__ilike: Optional[str] = None
    plan: Optional[TenantPlan] = None
    status: Optional[StatusTypes] = None
    description__ilike: Optional[str] = None
    order_by: Optional[list[str]] = None
    search: Optional[str] = None

    class Constants(Filter.Constants):
        model = Tenant
        ordering_field_name = "order_by"
        search_field_name = "search"
        search_model_fields = ["name", "owner"]    
