from typing import Optional
from app.api.models import Member

from fastapi_filter.contrib.sqlalchemy import Filter


class MemberFilter(Filter):
    name__like: Optional[str] = None
    backstory__like: Optional[str] = None
    type: Optional[str] = None

    position_x__gt: Optional[float] = None
    position_x__gte: Optional[float] = None
    position_x__lt: Optional[float] = None
    position_x__lte: Optional[float] = None
    position_x: Optional[float] = None

    position_y__gt: Optional[float] = None
    position_y__gte: Optional[float] = None
    position_y__lt: Optional[float] = None
    position_y__lte: Optional[float] = None
    position_y: Optional[float] = None

    temperature__gt: Optional[float] = None
    temperature__gte: Optional[float] = None
    temperature__lt: Optional[float] = None
    temperature__lte: Optional[float] = None
    temperature: Optional[float] = None

    model: Optional[str] = None
    interrupt: Optional[str] = None
    provider: Optional[str] = None

    order_by: Optional[list[str]] = None
    search: Optional[str] = None

    class Constants(Filter.Constants):
        model = Member
        ordering_field_name = "order_by"
        search_field_name = "search"
        search_model_fields = ["name", "backstory"]    
