from typing import Optional

from fastapi_filter import FilterDepends, with_prefix

from app.api.models import Team
from app.api.filters import ApiKeyFilter

from fastapi_filter.contrib.sqlalchemy import Filter



class TeamFilter(Filter):
    name__ilike: Optional[str] = None
    owner_id: Optional[str] = None
    owner__ilike: Optional[str] = None
    workflow: Optional[str] = None
    # member: Optional[MemberFilter] = FilterDepends(with_prefix("member", MemberFilter))
    # thread: Optional[ThreadFilter] = FilterDepends(with_prefix("threads", ThreadFilter))
    # graph: Optional[GraphFilter] = FilterDepends(with_prefix("graph", GraphFilter))
    # subgraph: Optional[SubgraphFilter] = FilterDepends(with_prefix("subgraph", Filter=SubgraphhFilter))
    apikey: Optional[ApiKeyFilter] = FilterDepends(with_prefix("threads", ApiKeyFilter))

    order_by: Optional[list[str]] = None
    search: Optional[str] = None

    class Constants(Filter.Constants):
        model = Team
        ordering_field_name = "order_by"
        search_field_name = "search"
        search_model_fields = ["name", "owner"]    