from typing import Optional

from app.api.models import Thread

from fastapi_filter.contrib.sqlalchemy import Filter



class ThreadFilter(Filter):

    updated_at__gt: Optional[str] = None
    updated_at__gte: Optional[str] = None
    updated_at__lt: Optional[str] = None
    updated_at__lte: Optional[str] = None
    updated_at: Optional[str] = None

    team_id: Optional[str] = None
    team__ilike: Optional[str] = None
    query__ilike: Optional[str] = None

    order_by: Optional[list[str]] = None
    search: Optional[str] = None

    class Constants(Filter.Constants):
        model = Thread
        ordering_field_name = "order_by"
        search_field_name = "search"
        search_model_fields = ["query"]    