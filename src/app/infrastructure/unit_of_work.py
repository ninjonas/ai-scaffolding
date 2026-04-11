from typing import Self

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.repositories.conversation import ConversationRepository
from app.domain.repositories.knowledge_file import KnowledgeFileRepository
from app.infrastructure.repositories.conversation import SQLConversationRepository
from app.infrastructure.repositories.knowledge_file import SQLKnowledgeFileRepository

log = structlog.get_logger()


class SQLAlchemyUnitOfWork:
    conversations: ConversationRepository
    knowledge: KnowledgeFileRepository

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def __aenter__(self) -> Self:
        self._session = self._session_factory()
        self.conversations = SQLConversationRepository(self._session)
        self.knowledge = SQLKnowledgeFileRepository(self._session)
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
