import asyncio
from datetime import datetime
from json import dumps
from typing import Any
import uuid

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse

from app.api.dependencies import (
    SessionDep, CurrentTeamAndUser, CurrentInstanceUpload, InstanceStatementUpload,
    create_upload_dep
)

from app.api.dependencies.upload import StorageClientDep, upload_create_form
from app.api.models import Upload, UploadCreate, UploadOut, UploadUpdate, Message
# from app.services.vector_store import get_embedding, search_similar_vectors

from fastapi_pagination.ext.sqlmodel import paginate
from fastapi_pagination.links import Page

from fastapi_filter import FilterDepends

from ..filters import UploadFilter


router = APIRouter(prefix="/upload", tags=["upload"])


@router.get("/", response_model=Page[UploadOut])
async def read_uploads(
    session: SessionDep,
    statement: InstanceStatementUpload,
    upload_filter: UploadFilter = FilterDepends(UploadFilter)
) -> Any:
    """
    Retrieve uploads from team.
    """
    statement = upload_filter.filter(statement)
    statement = upload_filter.sort(statement)
    return await paginate(session, statement)


@router.get("/{id}", response_model=UploadOut)
async def read_upload(upload: CurrentInstanceUpload) -> Any:
    """
    Get upload by ID.
    """
    return upload


@router.post("/")
async def create_upload(
    *,
    session: SessionDep,
    current_team_and_user: CurrentTeamAndUser,
    storage_client: StorageClientDep,
    upload_in: UploadCreate = Depends(upload_create_form), 
    file: UploadFile = File(...)
) -> Any:
    """
    Create new upload.
    """
    queue = asyncio.Queue()  # 创建队列

    background_task = await create_upload_dep(
        session=session, 
        current_team_and_user=current_team_and_user, 
        storage_client=storage_client, 
        upload_in=upload_in, 
        file=file,
        queue=queue
    )

    async def stream_progress():
        while 1:
            progress = await queue.get()
            yield dumps(progress, ensure_ascii=False, indent=4)

            if progress["status"] == "COMPLETED":
                break

    return StreamingResponse(
        content=stream_progress(), media_type="text/event-stream",
        background=background_task
    )


@router.put("/{id}", response_model=UploadOut)
async def update_upload(
    *,
    session: SessionDep,
    upload: CurrentInstanceUpload,
    upload_in: UploadUpdate,
) -> Any:
    """
    Update upload by ID.
    """        
    upload.sqlmodel_update(upload_in, update={
        "last_modified": datetime.now()
    })
    session.add(upload)
    await session.commit()
    await session.refresh(upload)
    return upload


@router.delete("/{id}")
async def delete_upload(
    session: SessionDep,
    upload: CurrentInstanceUpload
) -> None:
    """
    Delete upload by ID.
    """
    await session.delete(upload)
    await session.commit()
    return Message(message="Upload deleted successfully")


@router.get("/{id}/vector")
async def build_file_to_vector():
    ...


@router.post("/{id}/search")
async def search_file_in_vector():
    ...
