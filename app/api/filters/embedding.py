from datetime import datetime
from typing import Optional, Any, Dict
import uuid

from app.api.models import Embedding

from fastapi_filter.contrib.sqlalchemy import Filter


class EmbeddingFilter(Filter):
    upload_id: Optional[uuid.UUID] = None
    owner_id: Optional[uuid.UUID] = None
    team_id: Optional[uuid.UUID] = None
    document__ilike: Optional[str] = None
    
    created_at__gt: Optional[datetime] = None
    created_at__gte: Optional[datetime] = None
    created_at__lt: Optional[datetime] = None
    created_at__lte: Optional[datetime] = None

    updated_at__gt: Optional[datetime] = None
    updated_at__gte: Optional[datetime] = None
    updated_at__lt: Optional[datetime] = None
    updated_at__lte: Optional[datetime] = None

    order_by: Optional[list[str]] = None
    search: Optional[str] = None

    class Constants(Filter.Constants):
        model = Embedding
        ordering_field_name = "order_by"
        search_field_name = "search"
        search_model_fields = ["document"] 