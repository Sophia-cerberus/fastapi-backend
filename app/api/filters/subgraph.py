from datetime import datetime
from typing import Optional
import uuid

from app.api.models import Subgraph

from fastapi_filter.contrib.sqlalchemy import Filter


class SubgraphFilter(Filter):

    owner_id: Optional[uuid.UUID] = None
    owner__ilike: Optional[str] = None
    team_id: Optional[uuid.UUID] = None
    team__ilike: Optional[str] = None

    created_at__gt: Optional[datetime] = None
    created_at__gte: Optional[datetime] = None
    created_at__lt: Optional[datetime] = None
    created_at__lte: Optional[datetime] = None

    updated_at__gt: Optional[datetime] = None
    updated_at__gte: Optional[datetime] = None
    updated_at__lt: Optional[datetime] = None
    updated_at__lte: Optional[datetime] = None

    name: Optional[str] = None
    name__ilike: Optional[str] = None
    description: Optional[str] = None
    description__ilike: Optional[str] = None

    is_public: Optional[bool] = None  # 是否公开，可供其他用户使用

    order_by: Optional[list[str]] = None
    search: Optional[str] = None

    class Constants(Filter.Constants):
        model = Subgraph
        ordering_field_name = "order_by"
        search_field_name = "search"
        search_model_fields = ["name", "description"]    
