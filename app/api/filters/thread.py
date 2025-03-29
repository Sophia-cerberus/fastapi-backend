from datetime import datetime
from typing import Optional
import uuid

from app.api.models import Thread

from fastapi_filter.contrib.sqlalchemy import Filter



class ThreadFilter(Filter):

    updated_at__gt: Optional[datetime] = None
    updated_at__gte: Optional[datetime] = None
    updated_at__lt: Optional[datetime] = None
    updated_at__lte: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    team_id: Optional[uuid.UUID] = None
    team__ilike: Optional[str] = None
    query__ilike: Optional[str] = None

    order_by: Optional[list[str]] = None
    search: Optional[str] = None

    class Constants(Filter.Constants):
        model = Thread
        ordering_field_name = "order_by"
        search_field_name = "search"
        search_model_fields = ["query"]    