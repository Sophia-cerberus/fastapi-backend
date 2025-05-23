from sqlalchemy.ext.asyncio import AsyncSession

from sqlmodel import select

from app.core.config import settings
from app.api.models import User, UserCreate
from app.core.security import get_password_hash

from pydantic import PostgresDsn
from sqlalchemy.ext.asyncio.engine import AsyncEngine
from sqlalchemy.ext.asyncio import create_async_engine

dsn: PostgresDsn = settings.SQLALCHEMY_RUNNABLE_DATABASE_URI
engine: AsyncEngine = create_async_engine(dsn.unicode_string())


# make sure all SQLModel models are imported (app.api.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28
        

async def init_db(session: AsyncSession) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines
    # from sqlmodel import SQLModel

    # This works because the models are already imported and registered from app.api.models
    # SQLModel.metadata.create_all(engine)

    user = await session.scalar(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    )
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            phone=settings.FIRST_SUPERUSER_PHONE,
            is_superuser=True,
        )
        user = User.model_validate(
            user_in, update={
                "hashed_password": get_password_hash(user_in.password)
            }
        )
        session.add(user)
        await session.commit()
        await session.refresh(instance=user)
        return user

