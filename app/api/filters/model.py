from typing import Optional
import uuid
from app.api.models import Model

from fastapi_filter.contrib.sqlalchemy import Filter


class ModelFilter(Filter):

    ai_model_name: Optional[str] = None
    ai_model_name__ilike: Optional[str] = None
    provider_id: Optional[uuid.UUID] = None

    order_by: Optional[list[str]] = None
    search: Optional[str] = None

    class Constants(Filter.Constants):
        model = Model
        ordering_field_name = "order_by"
        search_field_name = "search"
        search_model_fields = ["ai_model_name"]    
