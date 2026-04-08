from pathlib import Path

import structlog
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

log = structlog.get_logger()

DATA_DIR = Path("data")


def create_engine(database_url: str) -> AsyncEngine:
    DATA_DIR.mkdir(exist_ok=True)
    log.info("creating_database_engine", url=database_url)
    return create_async_engine(database_url, echo=False)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def init_database(engine: AsyncEngine) -> None:
    from app.infrastructure.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("database_initialized")
