import asyncio
from json import loads
from typing import Annotated, AsyncGenerator
import uuid
import os

from fastapi import Depends, File, Form, HTTPException, UploadFile
from sqlmodel import or_, select
from sqlmodel.sql._expression_select_cls import SelectOfScalar

from app.api.models import Upload, UploadCreate, TeamUserJoin, RoleTypes, Team
from app.api.utils.models import StatusTypes
from app.core.config import settings
from app.core.string import uuid_8

from .session import SessionDep
from .common import CurrentTeamAndUser, StorageClientDep


async def instance_statement(current_team_and_user: CurrentTeamAndUser) ->  SelectOfScalar[Upload]:
    
    statement = select(Upload)
    if not current_team_and_user.user.is_superuser:
        if current_team_and_user.user.is_tenant_admin:
            statement = statement.join(Team).where(
                Team.tenant_id == current_team_and_user.team.tenant_id
            )
        else:
            statement = statement.join(TeamUserJoin).where(
                TeamUserJoin.user_id == current_team_and_user.user.id,
                TeamUserJoin.status == StatusTypes.ENABLE,
                TeamUserJoin.team_id == current_team_and_user.team.id == Upload.team_id,
            ).where(
                or_(
                    TeamUserJoin.role in [RoleTypes.ADMIN, RoleTypes.MODERATOR, RoleTypes.OWNER],
                    Upload.owner_id == current_team_and_user.user.id
                )
            )      # 限制在当前团队内

    return statement


async def current_instance(
    session: SessionDep, id: uuid.UUID, current_team_and_user: CurrentTeamAndUser
) -> Upload:
    
    statement = await instance_statement(current_team_and_user)
    statement = statement.where(Upload.id == id)

    upload = await session.scalar(statement)
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    return upload


async def upload_create_form(
    description: str = Form(...),
    chunk_size: int = Form(...),
    chunk_overlap: int = Form(...)
) -> UploadCreate:
    
    return UploadCreate(
        description=description,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )


async def create_upload_dep(
    session: SessionDep,
    current_team_and_user: CurrentTeamAndUser,
    storage_client: StorageClientDep,
    queue: asyncio.Queue,
    upload_in: UploadCreate = Depends(upload_create_form), 
    file: UploadFile = File(...),
) -> AsyncGenerator:
    
    buffer_size: int = settings.AWS_S3_UPLOAD_BUFFER
    bucket_name: str = settings.AWS_S3_BUCKET_NAME
    buffer: bytearray = bytearray()
    part_num: int = 1
    transferred_bytes: int = 0

    file_name, file_ext = os.path.splitext(file.filename)
    file_path: str = os.path.join(
        settings.AWS_S3_UPLOAD_PREFIX,
        str(current_team_and_user.team.id),
        str(current_team_and_user.user.id),
        f"{file_name}_{uuid_8()}{file_ext}"
    )

    upload_id: str | None = None
    parts: list = []
    
    while (file_chunk := await file.read(buffer_size)):

        buffer.extend(file_chunk)
        transferred_bytes += len(file_chunk)

        if len(buffer) >= buffer_size:
            upload_id, parts = await storage_client.upload_chunk(
                bucket_name=bucket_name, 
                remote_path=file_path,
                file_chunk=buffer,
                part_num=part_num,
                upload_id=upload_id,
                parts=parts,
            )
            part_num += 1
            buffer.clear()
            await queue.put({
                "status": "IN_PROGRESS", 
                "transferred_bytes": transferred_bytes,
                "data": None,
                "total_size": file.size
            })
    if buffer:  
        upload_id, parts = await storage_client.upload_chunk(
            bucket_name=bucket_name, 
            remote_path=file_path,
            file_chunk=buffer,
            part_num=part_num,
            upload_id=upload_id,
            parts=parts,
        )
    complete_upload_path: str = await storage_client.complete_upload(
        remote_path=file_path,
        upload_id=upload_id,
        parts=parts,
        bucket_name=bucket_name,
    )
    upload = Upload.model_validate(upload_in, update={
        "name": file.filename,
        "file_type": file.content_type,
        "file_path": complete_upload_path,
        "file_size": file.size,
        "team_id": current_team_and_user.team.id,
        "owner_id": current_team_and_user.user.id,
        "status": False
    })
    session.add(upload)
    await session.commit()
    await session.refresh(upload)
    await queue.put({
        "status": "COMPLETED",
        "transferred_bytes": transferred_bytes,
        "data": loads(upload.model_dump_json()),
        "total_size": file.size
    })


InstanceStatement = Annotated[SelectOfScalar[Upload], Depends(instance_statement)]
CurrentInstance = Annotated[Upload, Depends(current_instance)]
UploadCreateFormDep = Annotated[UploadCreate, Depends(upload_create_form)]