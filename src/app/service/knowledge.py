from collections.abc import Callable
from datetime import datetime

import structlog

from app.domain.entities.knowledge_file import (
    SCOPE_CONVERSATION,
    KnowledgeFile,
)
from app.infrastructure.mappers.knowledge_file import KnowledgeFileDataMapper
from app.infrastructure.unit_of_work import SQLAlchemyUnitOfWork
from app.service.knowledge_frontmatter import detect_file_type, generate

log = structlog.get_logger()

MAX_FILE_SIZE_BYTES = 500 * 1024  # 500KB
MAX_PROJECT_FILES = 50
MAX_CONVERSATION_FILES = 20
ERR_FILE_NOT_FOUND = "Knowledge file not found: "


class KnowledgeService:
    def __init__(self, uow_factory: Callable[[], SQLAlchemyUnitOfWork]) -> None:
        self._uow_factory = uow_factory

    async def upload(
        self,
        filename: str,
        content: str,
        scope: str,
        conversation_id: str | None = None,
    ) -> KnowledgeFile:
        log.info(
            "knowledge_upload_start",
            filename=filename,
            scope=scope,
            conversation_id=conversation_id,
        )

        if len(content.encode("utf-8")) > MAX_FILE_SIZE_BYTES:
            raise ValueError(f"File exceeds {MAX_FILE_SIZE_BYTES // 1024}KB limit")

        file_type = detect_file_type(filename)

        async with self._uow_factory() as uow:
            existing = await uow.knowledge.list(scope=scope, conversation_id=conversation_id)
            limit = MAX_CONVERSATION_FILES if scope == SCOPE_CONVERSATION else MAX_PROJECT_FILES
            if len(existing) >= limit:
                raise ValueError(f"File limit reached: max {limit} files for scope '{scope}'")

            name, description, tags = generate(filename, content, file_type)
            knowledge_file = KnowledgeFile(
                name=name,
                description=description,
                content=content,
                file_type=file_type,
                scope=scope,
                tags=tags,
                conversation_id=conversation_id,
            )

            await uow.knowledge.save(knowledge_file)
            await uow.commit()

        log.info(
            "knowledge_upload_complete",
            file_id=knowledge_file.id,
            name=knowledge_file.name,
            file_type=file_type,
            scope=scope,
            tag_count=len(tags),
        )
        return knowledge_file

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
                description=description if description is not None else existing.description,
                content=content if content is not None else existing.content,
                file_type=existing.file_type,
                scope=existing.scope,
                tags=tags if tags is not None else existing.tags,
                conversation_id=existing.conversation_id,
                created_at=existing.created_at,
                updated_at=datetime.utcnow(),
            )

            await uow.knowledge.save(updated)
            await uow.commit()

        log.info("knowledge_update_complete", file_id=file_id, name=updated.name)
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
        log.info("knowledge_delete_complete", file_id=file_id)

    async def list(
        self,
        scope: str | None = None,
        conversation_id: str | None = None,
    ) -> list[KnowledgeFile]:
        log.debug("knowledge_list", scope=scope, conversation_id=conversation_id)
        async with self._uow_factory() as uow:
            return await uow.knowledge.list(scope=scope, conversation_id=conversation_id)

    async def get_catalog(
        self,
        scope: str | None = None,
        conversation_id: str | None = None,
    ) -> list[dict]:
        log.debug("knowledge_get_catalog", scope=scope, conversation_id=conversation_id)
        async with self._uow_factory() as uow:
            files = await uow.knowledge.list(scope=scope, conversation_id=conversation_id)
        return [KnowledgeFileDataMapper.to_catalog_dict(f) for f in files]
