from typing import Protocol

from app.domain.entities.knowledge_file import KnowledgeFile


class KnowledgeFileRepository(Protocol):
    async def save(self, knowledge_file: KnowledgeFile) -> None: ...

    async def get_by_id(self, file_id: str) -> KnowledgeFile | None: ...

    async def list(
        self,
        scope: str | None = None,
        conversation_id: str | None = None,
    ) -> list[KnowledgeFile]: ...

    async def delete(self, file_id: str) -> None: ...
