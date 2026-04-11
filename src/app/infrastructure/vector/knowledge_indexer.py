"""KnowledgeIndexer: chunk and upsert knowledge files into ChromaDB."""

from typing import Any

import structlog

from app.infrastructure.database import TABLE_KNOWLEDGE_FILES
from app.shared.field_keys import EMBEDDING_MODEL_DEFAULT

CHUNK_TOKENS = 512
OVERLAP_TOKENS = 64

log = structlog.get_logger()


def _chunk_text(text: str, encoding: Any, chunk_size: int, overlap: int) -> list[str]:
    tokens = encoding.encode(text)
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunks.append(encoding.decode(tokens[start:end]))
        if end == len(tokens):
            break
        start += chunk_size - overlap
    return chunks


class KnowledgeIndexer:
    """Chunks and upserts knowledge file content into ChromaDB.

    Injected dependencies: chroma_client, settings.
    """

    def __init__(self, chroma_client: Any, settings: Any) -> None:
        self._client = chroma_client
        self._settings = settings

    def _get_collection(self) -> Any:
        from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

        ef = OpenAIEmbeddingFunction(
            api_key=self._settings.llm_api_key,
            model_name=EMBEDDING_MODEL_DEFAULT,
        )
        return self._client.get_or_create_collection(
            name=TABLE_KNOWLEDGE_FILES,
            embedding_function=ef,
        )

    async def index(
        self,
        file_id: str,
        name: str,
        content: str,
        file_type: str,
        scope: str,
        conversation_id: str | None = None,
    ) -> int:
        """Chunk content and upsert into the knowledge_files collection.

        Args:
            file_id: Unique identifier for the knowledge file.
            name: Human-readable file name.
            content: Raw text content to index.
            file_type: MIME type or extension describing the file.
            scope: 'project' or 'conversation'.
            conversation_id: Required when scope is 'conversation'.

        Returns:
            Number of chunks indexed.
        """
        import tiktoken

        bound_log = log.bind(file_id=file_id, name=name)
        bound_log.info("indexing_start")

        encoding = tiktoken.get_encoding("cl100k_base")
        chunks = _chunk_text(content, encoding, CHUNK_TOKENS, OVERLAP_TOKENS)

        collection = self._get_collection()
        ids = [f"{file_id}_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "file_id": file_id,
                "chunk_index": i,
                "name": name,
                "file_type": file_type,
                "scope": scope,
                "conversation_id": conversation_id or "",
            }
            for i in range(len(chunks))
        ]
        collection.upsert(ids=ids, documents=chunks, metadatas=metadatas)

        bound_log.info("indexing_done", chunk_count=len(chunks))
        return len(chunks)

    async def delete(self, file_id: str) -> None:
        """Delete all chunks for a given file_id.

        Args:
            file_id: The file whose chunks should be removed.
        """
        collection = self._get_collection()
        collection.delete(where={"file_id": file_id})
        log.info("indexing_deleted", file_id=file_id)
