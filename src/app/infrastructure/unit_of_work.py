from typing import Self

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.infrastructure.repositories.conversation import SQLConversationRepository

log = structlog.get_logger()


class SQLAlchemyUnitOfWork:
    conversations: SQLConversationRepository

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def __aenter__(self) -> Self:
        self._session = self._session_factory()
        self.conversations = SQLConversationRepository(self._session)
        log.debug("uow_started")
        return self

    async def commit(self) -> None:
        await self._session.commit()
        log.debug("uow_committed")

    async def rollback(self) -> None:
        await self._session.rollback()
        log.debug("uow_rolled_back")

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type:
            await self.rollback()
        await self._session.close()
        log.debug("uow_closed")
