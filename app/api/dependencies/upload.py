from json import dumps
from typing import Annotated, AsyncGenerator
import uuid

from fastapi import Depends, File, HTTPException, UploadFile
from sqlmodel import or_, select
from sqlmodel.sql._expression_select_cls import SelectOfScalar

from app.api.models import Upload, Team, UploadCreate
from app.core.storage.s3 import StorageClient
from app.core.config import settings

from .session import SessionDep
from .team import CurrentTeamAndUser


async def instance_statement(current_team_and_user: CurrentTeamAndUser) ->  SelectOfScalar[Upload]:
    
    statement = select(Upload)
    if not current_team_and_user.user.is_superuser:
        statement = statement.join(Team).where(
            or_(
                Team.owner_id == current_team_and_user.user.id,        # Team owner可以访问整个Team的ApiKey
                Upload.owner_id == current_team_and_user.user.id,       # 其他用户只能访问自己的ApiKey
            )
        ).where(Upload.team_id == current_team_and_user.team.id)      # 限制在当前团队内

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


async def create_upload(
    storage_client: StorageClient,
    file: UploadFile = File(...)
) -> AsyncGenerator[str, None]:
    
    buffer_size = settings.S3_BUFFER_SIZE
    buffer: bytearray = bytearray()
    part_num: int = 1
    transferred_bytes: float = 0.0
    file_path: str
    bucket_name: str
    upload_id: str | None = None
    parts: list = []

    while 1:
        file_chunk = await file.read(buffer_size)
        if not file_chunk:
            break

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
            yield dumps({
                "upload_id": upload_id,
                "status": "IN_PROGRESS", 
                "transferred_bytes": transferred_bytes
            })

    file_url: str = await storage_client.complete_upload(
        remote_path=file_path,
        upload_id=upload_id,
        parts=parts,
        bucket_name=bucket_name,
    )
    yield dumps({"status": "IS_COMPLETED", "file_path": file_url})


InstanceStatement = Annotated[Upload, Depends(instance_statement)]
CurrentInstance = Annotated[Upload, Depends(current_instance)]
CreateUploadDep = Annotated[Upload, Depends(create_upload)]