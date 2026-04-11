"""KnowledgeIndexer: chunk and upsert knowledge files into ChromaDB."""

from typing import Any

import structlog
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.infrastructure.database import TABLE_KNOWLEDGE_FILES
from app.service.knowledge_frontmatter import is_image
from app.shared.field_keys import EMBEDDING_MODEL_DEFAULT

CHUNK_SIZE_CHARS = 1024
CHUNK_OVERLAP_CHARS = 512
CHUNK_SEPARATORS = ["\n\n", "\n", ". ", " "]
DOC_TYPE_SUMMARY = "summary"
DOC_TYPE_CHUNK = "chunk"

log = structlog.get_logger()

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE_CHARS,
    chunk_overlap=CHUNK_OVERLAP_CHARS,
    separators=CHUNK_SEPARATORS,
)


def _chunk_text(text: str) -> list[str]:
    if not text.strip():
        return []
    return _splitter.split_text(text)


def _build_summary_chunk(
    file_id: str,
    name: str,
    description: str,
    tags: list[str] | None,
    base_meta: dict[str, str],
) -> tuple[list[str], list[str], list[dict]]:
    """Build a single summary document from LLM-enriched metadata."""
    tag_str = ", ".join(tags) if tags else ""
    summary = f"{name}. {description} Tags: {tag_str}".strip()
    meta = {**base_meta, "chunk_index": 0, "doc_type": DOC_TYPE_SUMMARY}
    return [f"{file_id}_summary"], [summary], [meta]


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
            api_base=self._settings.llm_base_url,
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
        description: str = "",
        tags: list[str] | None = None,
    ) -> int:
        """Chunk and upsert content into the knowledge_files collection.

        For images, indexes the LLM-generated metadata (name, description, tags)
        rather than raw base64. For text files, indexes the content directly.

        Returns:
            Number of chunks indexed.
        """
        bound_log = log.bind(file_id=file_id, name=name)
        bound_log.info("indexing_start")

        base_meta = {
            "file_id": file_id,
            "name": name,
            "file_type": file_type,
            "scope": scope,
            "conversation_id": conversation_id or "",
        }

        all_ids, all_docs, all_metas = _build_summary_chunk(
            file_id, name, description, tags, base_meta,
        )

        if not is_image(file_type):
            content_chunks = _chunk_text(content)
            for i, chunk in enumerate(content_chunks):
                all_ids.append(f"{file_id}_{i}")
                all_docs.append(chunk)
                all_metas.append(
                    {**base_meta, "chunk_index": i, "doc_type": DOC_TYPE_CHUNK},
                )

        collection = self._get_collection()
        if all_docs:
            collection.upsert(ids=all_ids, documents=all_docs, metadatas=all_metas)

        bound_log.info("indexing_done", chunk_count=len(all_docs))
        return len(all_docs)

    async def delete(self, file_id: str) -> None:
        """Delete all chunks for a given file_id.

        Args:
            file_id: The file whose chunks should be removed.
        """
        collection = self._get_collection()
        collection.delete(where={"file_id": file_id})
        log.info("indexing_deleted", file_id=file_id)
