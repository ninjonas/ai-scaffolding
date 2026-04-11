from pathlib import Path

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

log = structlog.get_logger()

DATA_DIR = Path("data")
TABLE_KNOWLEDGE_FILES = "knowledge_files"


def create_engine(database_url: str) -> AsyncEngine:
    DATA_DIR.mkdir(exist_ok=True)
    log.info("creating_database_engine", url=database_url)
    return create_async_engine(database_url, echo=False)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def _migrate_knowledge_files(conn) -> None:  # type: ignore[no-untyped-def]
    """Add missing columns to knowledge_files if they do not already exist."""
    result = await conn.execute(text(f"PRAGMA table_info({TABLE_KNOWLEDGE_FILES})"))
    columns = {row[1] for row in result.fetchall()}
    if "enriched" not in columns:
        sql = f"ALTER TABLE {TABLE_KNOWLEDGE_FILES} ADD COLUMN enriched BOOLEAN NOT NULL DEFAULT 0"
        await conn.execute(text(sql))
        log.info("migration_applied", table=TABLE_KNOWLEDGE_FILES, column="enriched")
    if "filename" not in columns:
        sql = f"ALTER TABLE {TABLE_KNOWLEDGE_FILES} ADD COLUMN filename TEXT NOT NULL DEFAULT ''"
        await conn.execute(text(sql))
        log.info("migration_applied", table=TABLE_KNOWLEDGE_FILES, column="filename")


async def init_database(engine: AsyncEngine) -> None:
    from app.infrastructure.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _migrate_knowledge_files(conn)
    log.info("database_initialized")
