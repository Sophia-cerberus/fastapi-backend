from typing import Any

from fastapi import APIRouter, UploadFile, File, HTTPException
from sqlmodel import select, or_

from app.api.dependencies import (
    SessionDep, CurrentTeamAndUser, CurrentInstanceUpload
)

from app.api.models import Upload, UploadCreate, UploadOut, UploadUpdate, Message, Team
# from app.services.vector_store import get_embedding, search_similar_vectors

from fastapi_pagination.ext.sqlmodel import paginate
from fastapi_pagination.links import Page

from fastapi_filter import FilterDepends

from ..filters import UploadFilter


router = APIRouter(prefix="/upload", tags=["upload"])


@router.get("/", response_model=Page[UploadOut])
async def read_uploads(
    session: SessionDep,
    current_team_and_user: CurrentTeamAndUser,
    upload_filter: UploadFilter = FilterDepends(UploadFilter)
) -> Any:
    """
    Retrieve uploads from team.
    """
    statement = select(Upload).where(Upload.team_id == current_team_and_user.team.id)
    if not current_team_and_user.user.is_superuser:
        statement = statement.join(Team).where(
            or_(
                Upload.owner_id == current_team_and_user.user.id,
                Team.owner_id == current_team_and_user.user.id
            )
        )

    statement = upload_filter.filter(statement)
    statement = upload_filter.sort(statement)
    return await paginate(session, statement)


@router.get("/{id}", response_model=UploadOut)
async def read_upload(upload: CurrentInstanceUpload) -> Any:
    """
    Get upload by ID.
    """
    return upload


@router.post("/", response_model=UploadOut)
async def create_upload(
    *,
    session: SessionDep,
    current_team_and_user: CurrentTeamAndUser,
    upload_in: UploadCreate,
    file: UploadFile = File(...),
) -> Any:
    """
    Create new upload.
    """
    upload = Upload.model_validate(upload_in, update={
        "file_name": file.filename,
        "team_id": current_team_and_user.team.id,
        "owner_id": current_team_and_user.user.id,
    })
    session.add(upload)
    await session.commit()
    await session.refresh(upload)
    return upload

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
    upload.sqlmodel_update(upload_in)
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


@router.post("/{upload_id}/search")
async def search_upload(
    upload_id: int,
    query: str,
    session: SessionDep,
):
    """
    Perform vector search in an uploaded file.
    """
    upload = session.get(Upload, upload_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    # results = search_similar_vectors(upload.embedding, query)
    # return {"results": results}