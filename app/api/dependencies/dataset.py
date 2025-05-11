from typing import Annotated, Union
import uuid
from fastapi import Depends, HTTPException, status
from sqlmodel import or_, select
from sqlmodel.sql._expression_select_cls import SelectOfScalar

from app.api.models import Dataset, DatasetCreate, DatasetUpdate, TeamUserJoin, RoleTypes, Team
from app.api.utils.models import StatusTypes
from app.core.config import settings

from .team import CurrentTeamAndUser
from .session import SessionDep


async def instance_statement(current_team_and_user: CurrentTeamAndUser) -> SelectOfScalar[Dataset]:
    
    statement: SelectOfScalar[Dataset] = select(Dataset)
    if not current_team_and_user.user.is_superuser:
        if current_team_and_user.user.is_tenant_admin:
            statement = statement.join(Team).where(
                Team.tenant_id == current_team_and_user.team.tenant_id
            )
        else:
            statement = statement.join(TeamUserJoin).where(
                TeamUserJoin.user_id == current_team_and_user.user.id,
                TeamUserJoin.status == StatusTypes.ENABLE,
                TeamUserJoin.team_id == current_team_and_user.team.id == Dataset.team_id,
            ).where(
                or_(
                    TeamUserJoin.role in [RoleTypes.ADMIN, RoleTypes.MODERATOR, RoleTypes.OWNER],
                    Dataset.owner_id == current_team_and_user.user.id
                )
            )      # Restrict to current team

    return statement


async def current_instance(
    session: SessionDep, id: uuid.UUID, current_team_and_user: CurrentTeamAndUser
) -> Dataset:

    statement = await instance_statement(current_team_and_user)
    statement = statement.where(Dataset.id == id)

    if not (dataset := await session.scalar(statement)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    return dataset


async def validate_name_in(
    session: SessionDep, dataset_in: Union[DatasetCreate, DatasetUpdate], current_team_and_user: CurrentTeamAndUser, parent_id: uuid.UUID = None
) -> Dataset | None:

    if hasattr(dataset_in, "name") and dataset_in.name and dataset_in.name in settings.PROTECTED_NAMES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="Name is a protected name. Choose another name."
        )
    
    # For datasets with the same name, they must have different parent_id
    # Use the provided parent_id or the one from dataset_in
    parent_id_to_check = parent_id if parent_id else getattr(dataset_in, "parent_id", None)
    
    statement = select(Dataset).where(
        Dataset.name == dataset_in.name,
        Dataset.team_id == current_team_and_user.team.id,
        Dataset.parent_id == parent_id_to_check
    )
    return await session.scalar(statement)


async def validate_parent(
    session: SessionDep, parent_id: uuid.UUID, current_team_and_user: CurrentTeamAndUser
) -> Dataset | None:
    if not parent_id:
        return None
    
    statement = await instance_statement(current_team_and_user)
    statement = statement.where(Dataset.id == parent_id)
    
    parent = await session.scalar(statement)
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent dataset not found or you don't have access to it"
        )
    return parent


async def validate_create_in(
    session: SessionDep, dataset_in: DatasetCreate, current_team_and_user: CurrentTeamAndUser
) -> None:
    
    # Validate parent exists if provided
    if dataset_in.parent_id:
        await validate_parent(session, dataset_in.parent_id, current_team_and_user)
    
    # Check for duplicate names at the same level
    if await validate_name_in(session=session, dataset_in=dataset_in, current_team_and_user=current_team_and_user):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="Dataset with this name already exists at the same level"
        )


async def validate_update_in(
    session: SessionDep, dataset_in: DatasetUpdate, id: uuid.UUID, current_team_and_user: CurrentTeamAndUser
) -> Dataset:
    
    # Get current dataset
    current_dataset = await current_instance(session=session, id=id, current_team_and_user=current_team_and_user)
    
    # If parent_id is changing, validate the new parent exists
    if dataset_in.parent_id is not None and dataset_in.parent_id != current_dataset.parent_id:
        # Prevent circular references by checking the parent isn't the dataset itself
        if dataset_in.parent_id == id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A dataset cannot be its own parent"
            )
        await validate_parent(session, dataset_in.parent_id, current_team_and_user)
    
    # If name is changing, check for duplicates at the same level
    if dataset_in.name and dataset_in.name != current_dataset.name:
        parent_id_to_check = dataset_in.parent_id if dataset_in.parent_id is not None else current_dataset.parent_id
        duplicate = await validate_name_in(
            session=session, 
            dataset_in=dataset_in, 
            current_team_and_user=current_team_and_user,
            parent_id=parent_id_to_check
        )
        if duplicate and duplicate.id != id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, 
                detail="Dataset with this name already exists at the same level"
            )
    
    return current_dataset


# For convenience in route functions
InstanceStatement = Annotated[SelectOfScalar[Dataset], Depends(instance_statement)]
CurrentInstance = Annotated[Dataset, Depends(current_instance)]
ValidateCreateIn = Annotated[None, Depends(validate_create_in)]
ValidateUpdateIn = Annotated[Dataset, Depends(validate_update_in)] 