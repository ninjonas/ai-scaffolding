import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.entities.conversation import Conversation
from app.infrastructure.mappers.conversation import ConversationDataMapper
from app.infrastructure.models.conversation import ConversationModel

log = structlog.get_logger()


class SQLConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, conversation_id: str) -> Conversation | None:
        log.debug("repo_get_by_id", conversation_id=conversation_id)
        stmt = (
            select(ConversationModel)
            .where(ConversationModel.id == conversation_id)
            .options(selectinload(ConversationModel.messages))
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return ConversationDataMapper.to_domain(model)

    async def save(self, conversation: Conversation) -> None:
        log.debug("repo_save", conversation_id=conversation.id)
        model = ConversationDataMapper.to_model(conversation)
        await self._session.merge(model)

    async def list_recent(self, limit: int = 20) -> list[Conversation]:
        log.debug("repo_list_recent", limit=limit)
        stmt = (
            select(ConversationModel)
            .options(selectinload(ConversationModel.messages))
            .order_by(ConversationModel.updated_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [ConversationDataMapper.to_domain(m) for m in models]

    async def delete(self, conversation_id: str) -> None:
        log.debug("repo_delete", conversation_id=conversation_id)
        stmt = select(ConversationModel).where(ConversationModel.id == conversation_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
