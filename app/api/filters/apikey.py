from datetime import datetime
from typing import Optional
import uuid

from app.api.models import ApiKey

from fastapi_filter.contrib.sqlalchemy import Filter


class ApiKeyFilter(Filter):
    hashed_key: Optional[str] = None
    short_key: Optional[str] = None
    team_id: Optional[uuid.UUID] = None
    onwer_id: Optional[uuid.UUID] = None

    created_at__gt: Optional[datetime] = None
    created_at__gte: Optional[datetime] = None
    created_at__lt: Optional[datetime] = None
    created_at__lte: Optional[datetime] = None

    order_by: Optional[list[str]] = None
    search: Optional[str] = None

    class Constants(Filter.Constants):
        model = ApiKey
        ordering_field_name = "order_by"
        search_field_name = "search"
        search_model_fields = ["team", "description"]    
