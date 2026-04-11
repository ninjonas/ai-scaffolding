import time

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.entities.conversation import Conversation
from app.infrastructure.mappers.conversation import ConversationDataMapper
from app.infrastructure.models.conversation import ConversationModel


class SQLConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._log = structlog.get_logger(__name__)

    async def get_by_id(self, conversation_id: str) -> Conversation | None:
        self._log.debug("repo_get_by_id", conversation_id=conversation_id)
        start = time.monotonic()
        stmt = (
            select(ConversationModel)
            .where(ConversationModel.id == conversation_id)
            .options(selectinload(ConversationModel.messages))
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        found = model is not None
        duration_ms = round((time.monotonic() - start) * 1000, 3)
        self._log.debug(
            "repo_get_by_id_done",
            conversation_id=conversation_id,
            found=found,
            duration_ms=duration_ms,
        )
        if model is None:
            return None
        return ConversationDataMapper.to_domain(model)

    async def save(self, conversation: Conversation) -> None:
        self._log.debug("repo_save", conversation_id=conversation.id)
        start = time.monotonic()
        model = ConversationDataMapper.to_model(conversation)
        await self._session.merge(model)
        duration_ms = round((time.monotonic() - start) * 1000, 3)
        self._log.debug("repo_save_done", conversation_id=conversation.id, duration_ms=duration_ms)

    async def list_recent(self, limit: int = 20) -> list[Conversation]:
        self._log.debug("repo_list_recent", limit=limit)
        start = time.monotonic()
        stmt = (
            select(ConversationModel)
            .options(selectinload(ConversationModel.messages))
            .order_by(ConversationModel.updated_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        conversations = [ConversationDataMapper.to_domain(m) for m in models]
        duration_ms = round((time.monotonic() - start) * 1000, 3)
        self._log.debug(
            "repo_list_recent_done",
            limit=limit,
            count=len(conversations),
            duration_ms=duration_ms,
        )
        return conversations

    async def delete(self, conversation_id: str) -> None:
        self._log.debug("repo_delete", conversation_id=conversation_id)
        start = time.monotonic()
        stmt = select(ConversationModel).where(ConversationModel.id == conversation_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        deleted = model is not None
        if model:
            await self._session.delete(model)
        duration_ms = round((time.monotonic() - start) * 1000, 3)
        self._log.debug(
            "repo_delete_done",
            conversation_id=conversation_id,
            deleted=deleted,
            duration_ms=duration_ms,
        )
