"""MemorySearcher: semantic search over past chat messages."""

from typing import Any

import structlog

from app.shared.field_keys import (
    CHROMA_COLLECTION_MESSAGES,
    CHROMA_RESULT_IDS,
    EMBEDDING_MODEL_DEFAULT,
)

log = structlog.get_logger()


class MemorySearcher:
    """Queries the chat_messages ChromaDB collection for cross-conversation memory.

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
            name=CHROMA_COLLECTION_MESSAGES,
            embedding_function=ef,
        )

    async def search(
        self,
        query: str,
        current_conversation_id: str,
        top_k: int = 5,
    ) -> list[dict]:
        """Search past messages from other conversations.

        Args:
            query: Natural language query string.
            current_conversation_id: Excluded from results to avoid self-referential matches.
            top_k: Maximum number of results to return.

        Returns:
            List of dicts: message_id, conversation_id, role, created_at, excerpt, score.
        """
        log.info("memory_search_start", query=query[:50])

        collection = self._get_collection()
        results = collection.query(
            query_texts=[query],
            n_results=top_k,
            where={"conversation_id": {"$ne": current_conversation_id}},
        )

        hits = []
        if results and results.get(CHROMA_RESULT_IDS):
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            distances = results["distances"][0]
            for doc, meta, dist in zip(docs, metas, distances, strict=False):
                hits.append(
                    {
                        "message_id": meta.get("message_id"),
                        "conversation_id": meta.get("conversation_id"),
                        "role": meta.get("role"),
                        "created_at": meta.get("created_at"),
                        "excerpt": doc,
                        "score": 1.0 - dist,
                    }
                )

        log.info("memory_search_done", result_count=len(hits))
        return hits
