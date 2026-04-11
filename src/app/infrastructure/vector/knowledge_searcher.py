"""KnowledgeSearcher: semantic search over indexed knowledge files."""

from typing import Any

import structlog

from app.infrastructure.database import TABLE_KNOWLEDGE_FILES
from app.shared.field_keys import (
    CHROMA_RESULT_IDS,
    EMBEDDING_MODEL_DEFAULT,
    FIELD_KEY_FILE_TYPE,
    FIELD_KEY_NAME,
)

log = structlog.get_logger()


class KnowledgeSearcher:
    """Queries the knowledge_files ChromaDB collection.

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

    async def search(
        self,
        query: str,
        scope: str,
        conversation_id: str | None = None,
        top_k: int = 5,
    ) -> list[dict]:
        """Search knowledge files by semantic similarity.

        Args:
            query: Natural language query string.
            scope: 'project' or 'conversation' filter.
            conversation_id: Required when scope is 'conversation'.
            top_k: Maximum number of results to return.

        Returns:
            List of dicts with keys: file_id, name, file_type, chunk_index, excerpt, score.
        """
        bound_log = log.bind(query=query[:50], scope=scope)
        bound_log.info("search_start")

        where: dict = {"scope": scope}
        if conversation_id:
            where["conversation_id"] = conversation_id

        collection = self._get_collection()
        results = collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where,
        )

        hits = []
        if results and results.get(CHROMA_RESULT_IDS):
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            distances = results["distances"][0]
            for doc, meta, dist in zip(docs, metas, distances, strict=False):
                hits.append(
                    {
                        "file_id": meta.get("file_id"),
                        "name": meta.get(FIELD_KEY_NAME),
                        "file_type": meta.get(FIELD_KEY_FILE_TYPE),
                        "chunk_index": meta.get("chunk_index"),
                        "excerpt": doc,
                        "score": 1.0 - dist,
                    }
                )

        bound_log.info("search_done", result_count=len(hits))
        return hits
