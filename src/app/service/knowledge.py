from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import structlog
from langchain_core.language_models import BaseChatModel

from app.domain.entities.knowledge_file import SCOPE_CONVERSATION, KnowledgeFile
from app.infrastructure.unit_of_work import SQLAlchemyUnitOfWork
from app.service.knowledge_frontmatter import detect_file_type, generate, is_image
from app.service.knowledge_frontmatter_llm import llm_describe_image, llm_generate

log = structlog.get_logger()

MAX_FILE_SIZE_BYTES = 500 * 1024  # 500KB
MAX_PROJECT_FILES = 50
MAX_CONVERSATION_FILES = 20
ERR_FILE_NOT_FOUND = "Knowledge file not found: "


class KnowledgeService:
    def __init__(
        self,
        uow_factory: Callable[[], SQLAlchemyUnitOfWork],
        llm: BaseChatModel | None = None,
        indexer: Any | None = None,
    ) -> None:
        self._uow_factory = uow_factory
        self._llm = llm
        self._indexer = indexer

    async def _index(self, file: KnowledgeFile) -> None:
        if self._indexer is None:
            return
        log.info("knowledge_index_start", file_id=file.id)
        try:
            chunks = await self._indexer.index(
                file.id, file.name, file.content, file.file_type, file.scope, file.conversation_id
            )
            log.info("knowledge_index_done", file_id=file.id, chunk_count=chunks)
        except Exception as exc:
            log.warning("knowledge_index_error", file_id=file.id, error=str(exc))

    async def upload(
        self,
        filename: str,
        content: str,
        scope: str,
        conversation_id: str | None = None,
    ) -> KnowledgeFile:
        log.info("knowledge_upload_start", filename=filename, scope=scope)
        file_type = detect_file_type(filename)
        if not is_image(file_type) and len(content.encode("utf-8")) > MAX_FILE_SIZE_BYTES:
            raise ValueError(f"File exceeds {MAX_FILE_SIZE_BYTES // 1024}KB limit")
        async with self._uow_factory() as uow:
            existing = await uow.knowledge.list(scope=scope, conversation_id=conversation_id)
            limit = MAX_CONVERSATION_FILES if scope == SCOPE_CONVERSATION else MAX_PROJECT_FILES
            if len(existing) >= limit:
                raise ValueError(f"File limit reached: max {limit} files for scope '{scope}'")
            name, description, tags = generate(filename, content, file_type)
            kf = KnowledgeFile(
                name=name,
                filename=filename,
                description=description,
                content=content,
                file_type=file_type,
                scope=scope,
                tags=tags,
                conversation_id=conversation_id,
            )
            await uow.knowledge.save(kf)
            await uow.commit()
        log.info("knowledge_upload_complete", file_id=kf.id, name=kf.name, scope=scope)
        await self._index(kf)
        return kf

    async def update(
        self,
        file_id: str,
        name: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
        content: str | None = None,
    ) -> KnowledgeFile:
        log.info("knowledge_update_start", file_id=file_id)
        async with self._uow_factory() as uow:
            existing = await uow.knowledge.get_by_id(file_id)
            if existing is None:
                raise ValueError(ERR_FILE_NOT_FOUND + file_id)
            updated = KnowledgeFile(
                id=existing.id,
                name=name if name is not None else existing.name,
                filename=existing.filename,
                description=description if description is not None else existing.description,
                content=content if content is not None else existing.content,
                file_type=existing.file_type,
                scope=existing.scope,
                tags=tags if tags is not None else existing.tags,
                conversation_id=existing.conversation_id,
                created_at=existing.created_at,
                updated_at=datetime.now(UTC),
            )
            await uow.knowledge.save(updated)
            await uow.commit()
        log.info("knowledge_update_complete", file_id=file_id, name=updated.name)
        if content is not None and self._indexer is not None:
            await self._indexer.delete(file_id)
            await self._index(updated)
        return updated

    async def get(self, file_id: str) -> KnowledgeFile | None:
        log.debug("knowledge_get", file_id=file_id)
        async with self._uow_factory() as uow:
            return await uow.knowledge.get_by_id(file_id)

    async def delete(self, file_id: str) -> None:
        log.info("knowledge_delete_start", file_id=file_id)
        async with self._uow_factory() as uow:
            existing = await uow.knowledge.get_by_id(file_id)
            if existing is None:
                raise ValueError(ERR_FILE_NOT_FOUND + file_id)
            await uow.knowledge.delete(file_id)
            await uow.commit()
        if self._indexer is not None:
            await self._indexer.delete(file_id)
        log.info("knowledge_delete_complete", file_id=file_id)

    async def list(
        self,
        scope: str | None = None,
        conversation_id: str | None = None,
    ) -> list[KnowledgeFile]:
        log.debug("knowledge_list", scope=scope, conversation_id=conversation_id)
        async with self._uow_factory() as uow:
            return await uow.knowledge.list(scope=scope, conversation_id=conversation_id)

    async def enrich_metadata(self, file_id: str) -> None:
        log.info("knowledge_enrich_start", file_id=file_id)
        try:
            async with self._uow_factory() as uow:
                file = await uow.knowledge.get_by_id(file_id)
                if file is None:
                    log.warning("knowledge_enrich_skip", file_id=file_id, reason="not_found")
                    return
            name, description, tags = await self._generate_enrichment(file)
            async with self._uow_factory() as uow:
                existing = await uow.knowledge.get_by_id(file_id)
                if existing is not None:
                    enriched = KnowledgeFile(
                        id=existing.id,
                        name=name or existing.name,
                        filename=existing.filename,
                        description=description or existing.description,
                        content=existing.content,
                        file_type=existing.file_type,
                        scope=existing.scope,
                        tags=tags or existing.tags,
                        enriched=True,
                        conversation_id=existing.conversation_id,
                        created_at=existing.created_at,
                        updated_at=datetime.now(UTC),
                    )
                    await uow.knowledge.save(enriched)
                    await uow.commit()
            log.info("knowledge_enrich_done", file_id=file_id, llm_used=bool(name))
        except Exception as exc:
            log.warning("knowledge_enrich_error", file_id=file_id, error=str(exc), exc_info=exc)

    async def _generate_enrichment(self, file: KnowledgeFile) -> tuple[str, str, list[str]]:
        if self._llm is not None and is_image(file.file_type):
            return await llm_describe_image(file.content, file.file_type, self._llm)
        if self._llm is not None:
            return await llm_generate(file.content, file.file_type, self._llm)
        return "", "", []
