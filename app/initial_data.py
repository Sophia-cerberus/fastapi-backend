import logging
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import engine, init_db

from app.utils.logger import get_logger

logger = get_logger(__name__)


async def init() -> None:
    async with AsyncSession(engine) as session:
        await init_db(session)


async def main() -> None:
    await logger.info("Creating initial data")
    await init()
    await logger.info("Initial data created")


if __name__ == "__main__":
    asyncio.run(main())
