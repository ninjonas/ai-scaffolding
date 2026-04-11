import time

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.knowledge_file import KnowledgeFile
from app.infrastructure.mappers.knowledge_file import KnowledgeFileDataMapper
from app.infrastructure.models.knowledge_file import KnowledgeFileModel


class SQLKnowledgeFileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._log = structlog.get_logger(__name__)

    async def save(self, knowledge_file: KnowledgeFile) -> None:
        self._log.debug("repo_knowledge_save", file_id=knowledge_file.id, name=knowledge_file.name)
        start = time.monotonic()
        model = KnowledgeFileDataMapper.to_model(knowledge_file)
        await self._session.merge(model)
        duration_ms = round((time.monotonic() - start) * 1000, 3)
        self._log.debug("repo_knowledge_save_done", file_id=knowledge_file.id, duration_ms=duration_ms)

    async def get_by_id(self, file_id: str) -> KnowledgeFile | None:
        self._log.debug("repo_knowledge_get_by_id", file_id=file_id)
        start = time.monotonic()
        stmt = select(KnowledgeFileModel).where(KnowledgeFileModel.id == file_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        duration_ms = round((time.monotonic() - start) * 1000, 3)
        self._log.debug(
            "repo_knowledge_get_by_id_done",
            file_id=file_id,
            found=model is not None,
            duration_ms=duration_ms,
        )
        if model is None:
            return None
        return KnowledgeFileDataMapper.to_domain(model)

    async def list(
        self,
        scope: str | None = None,
        conversation_id: str | None = None,
    ) -> list[KnowledgeFile]:
        self._log.debug("repo_knowledge_list", scope=scope, conversation_id=conversation_id)
        start = time.monotonic()
        stmt = select(KnowledgeFileModel)
        if scope is not None:
            stmt = stmt.where(KnowledgeFileModel.scope == scope)
        if conversation_id is not None:
            stmt = stmt.where(KnowledgeFileModel.conversation_id == conversation_id)
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        files = [KnowledgeFileDataMapper.to_domain(m) for m in models]
        duration_ms = round((time.monotonic() - start) * 1000, 3)
        self._log.debug("repo_knowledge_list_done", count=len(files), duration_ms=duration_ms)
        return files

    async def delete(self, file_id: str) -> None:
        self._log.debug("repo_knowledge_delete", file_id=file_id)
        start = time.monotonic()
        stmt = select(KnowledgeFileModel).where(KnowledgeFileModel.id == file_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        deleted = model is not None
        if model:
            await self._session.delete(model)
        duration_ms = round((time.monotonic() - start) * 1000, 3)
        self._log.debug("repo_knowledge_delete_done", file_id=file_id, deleted=deleted, duration_ms=duration_ms)
