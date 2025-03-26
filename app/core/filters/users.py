from typing import Optional

from app.models import User

from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter

from .items import ItemFilter


class UserFilter(Filter):
    email: Optional[str] = None
    email__ilike: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    full_name: Optional[str] = None
    full_name__ilike: Optional[str] = None
    items: Optional[ItemFilter] = FilterDepends(with_prefix("items", ItemFilter))

    order_by: Optional[list[str]] = None
    search: Optional[str] = None

    class Constants(Filter.Constants):
        model = User
        ordering_field_name = "order_by"
        search_field_name = "search"
        search_model_fields = ["email", "is_active", "is_superuser", "full_name"]