from typing import Optional

from app.models import Item

from fastapi_filter.contrib.sqlalchemy import Filter


class ItemFilter(Filter):
    title: Optional[str] = None
    title__ilike: Optional[str] = None
    description: Optional[str] = None
    description__ilike: Optional[str] = None
    order_by: Optional[list[str]] = None
    search: Optional[str] = None

    class Constants(Filter.Constants):
        model = Item
        ordering_field_name = "order_by"
        search_field_name = "search"
        search_model_fields = ["title", "description"]