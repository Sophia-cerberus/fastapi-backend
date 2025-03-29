from typing import Optional
import uuid

from fastapi_filter import FilterDepends, with_prefix

from app.api.models import Team

from fastapi_filter.contrib.sqlalchemy import Filter



class TeamFilter(Filter):
    name__ilike: Optional[str] = None
    owner_id: Optional[uuid.UUID] = None
    owner__ilike: Optional[str] = None
    workflow: Optional[str] = None
    order_by: Optional[list[str]] = None
    search: Optional[str] = None

    class Constants(Filter.Constants):
        model = Team
        ordering_field_name = "order_by"
        search_field_name = "search"
        search_model_fields = ["name", "owner"]    