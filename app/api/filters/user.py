from typing import Optional

from app.api.models import User

from fastapi_filter.contrib.sqlalchemy import Filter


class UserFilter(Filter):
    email__ilike: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    is_tenant_admin: Optional[bool] = None
    full_name__ilike: Optional[str] = None

    order_by: Optional[list[str]] = None
    search: Optional[str] = None

    class Constants(Filter.Constants):
        model = User
        ordering_field_name = "order_by"
        search_field_name = "search"
        search_model_fields = ["email", "full_name"]