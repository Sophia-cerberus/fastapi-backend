from typing import Optional
from app.api.models import ModelProvider

from fastapi_filter.contrib.sqlalchemy import Filter


class ProviderFilter(Filter):

    provider_name: Optional[str] = None
    provider_name__ilike: Optional[str] = None
    description__ilike: Optional[str] = None

    order_by: Optional[list[str]] = None
    search: Optional[str] = None

    class Constants(Filter.Constants):
        model = ModelProvider
        ordering_field_name = "order_by"
        search_field_name = "search"
        search_model_fields = ["provider_name", "description"]    
