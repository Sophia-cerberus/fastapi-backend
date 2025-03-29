from typing import Optional

from app.api.models import Upload

from fastapi_filter.contrib.sqlalchemy import Filter



class UploadFilter(Filter):

    owner_id: Optional[str] = None
    owner__ilike: Optional[str] = None

    status: Optional[str] = None
    name__ilike: Optional[str] = None
    description__ilike: Optional[str] = None
    file_type: Optional[str] = None

    chunk_size__lt: Optional[int] = None
    chunk_size__lte: Optional[int] = None
    chunk_size__gt: Optional[int] = None
    chunk_size__gte: Optional[int] = None

    chunk_overlap__lt: Optional[int] = None
    chunk_overlap__lte: Optional[int] = None
    chunk_overlap__gt: Optional[int] = None
    chunk_overlap__gte: Optional[int] = None

    last_modified__lt: Optional[str] = None
    last_modified__lte: Optional[str] = None
    last_modified__gt: Optional[str] = None
    last_modified__gte: Optional[str] = None

    order_by: Optional[list[str]] = None
    search: Optional[str] = None

    class Constants(Filter.Constants):
        model = Upload
        ordering_field_name = "order_by"
        search_field_name = "search"
        search_model_fields = ["query"]    