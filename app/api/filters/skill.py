from typing import Optional

from app.api.models import Skill

from fastapi_filter.contrib.sqlalchemy import Filter


class SkillFilter(Filter):

    name: Optional[str] = None
    name__ilike: Optional[str] = None
    description: Optional[str] = None
    description__ilike: Optional[str] = None
    display_name: Optional[str] = None
    display_name__ilike: Optional[str] = None
    managed: Optional[bool] = None

    order_by: Optional[list[str]] = None
    search: Optional[str] = None

    class Constants(Filter.Constants):
        model = Skill
        ordering_field_name = "order_by"
        search_field_name = "search"
        search_model_fields = ["name", "description", 'display_name']    
