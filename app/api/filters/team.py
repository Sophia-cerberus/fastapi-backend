from typing import Optional
import uuid

from app.api.models import Team

from fastapi_filter.contrib.sqlalchemy import Filter



class TeamFilter(Filter):
    tenant_id: Optional[uuid.UUID] = None
    owner_id: Optional[uuid.UUID] = None
    workflow: Optional[str] = None
    order_by: Optional[list[str]] = None
    search: Optional[str] = None

    class Constants(Filter.Constants):
        model = Team
        ordering_field_name = "order_by"
        search_field_name = "search"
        search_model_fields = ["name", "owner"]    