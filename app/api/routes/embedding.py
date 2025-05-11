from typing import Any

from fastapi import APIRouter

from app.api.dependencies import (
    SessionDep, CurrentTeamAndUser, CurrentInstanceEmbedding,
    InstanceStatementEmbedding
)
from app.api.models import Embedding, EmbeddingCreate, EmbeddingOut, EmbeddingUpdate, Message

from fastapi_pagination.ext.sqlmodel import paginate
from fastapi_pagination.links import Page

from fastapi_filter import FilterDepends

from ..filters import EmbeddingFilter

router = APIRouter(prefix="/embedding", tags=["embedding"])


@router.get("/", response_model=Page[EmbeddingOut])
async def read_embeddings(
    session: SessionDep,
    statement: InstanceStatementEmbedding,
    embedding_filter: EmbeddingFilter = FilterDepends(EmbeddingFilter)
) -> Any:
    """
    Retrieve embeddings with filtering.
    """
    statement = embedding_filter.filter(statement)
    statement = embedding_filter.sort(statement)
    return await paginate(session, statement)


@router.get("/{id}", response_model=EmbeddingOut)
async def read_embedding(embedding: CurrentInstanceEmbedding) -> Any:
    """
    Get embedding by ID.
    """
    return embedding


@router.post("/", response_model=EmbeddingOut)
async def create_embedding(
    *,
    session: SessionDep,
    current_team_and_user: CurrentTeamAndUser,
    embedding_in: EmbeddingCreate,
) -> Any:
    """
    Create new embedding.
    This is typically called by the document processing pipeline after an upload.
    """
    embedding = Embedding.model_validate(embedding_in, update={
        "team_id": current_team_and_user.team.id, 
        "owner_id": current_team_and_user.user.id,
    })
    session.add(embedding)
    await session.commit()
    await session.refresh(embedding)
    return embedding


@router.put("/{id}", response_model=EmbeddingOut)
async def update_embedding(
    *,
    session: SessionDep,
    embedding: CurrentInstanceEmbedding,
    embedding_in: EmbeddingUpdate,
) -> Any:
    """
    Update embedding by ID.
    This is typically used to update metadata or document content.
    """        
    embedding.sqlmodel_update(embedding_in)
    session.add(embedding)
    await session.commit()
    await session.refresh(embedding)
    return embedding


@router.delete("/{id}")
async def delete_embedding(
    session: SessionDep,
    embedding: CurrentInstanceEmbedding
) -> None:
    """
    Delete embedding by ID.
    """
    await session.delete(embedding)
    await session.commit()
    return Message(message="Embedding deleted successfully")
