"""KnowledgeSearcher: semantic search over indexed knowledge files."""

from typing import Any

import structlog

from app.domain.entities.knowledge_file import SCOPE_CONVERSATION, SCOPE_PROJECT
from app.infrastructure.database import TABLE_KNOWLEDGE_FILES
from app.shared.field_keys import (
    CHROMA_RESULT_IDS,
    EMBEDDING_MODEL_DEFAULT,
    FIELD_KEY_FILE_TYPE,
    FIELD_KEY_NAME,
)

log = structlog.get_logger()

MIN_RELEVANCE_SCORE = 0.3
MIN_RELEVANCE_SCORE_CONVERSATION = 0.15


def build_search_filter(scope: str, conversation_id: str | None = None) -> dict | None:
    """Build the ChromaDB ``where`` filter for a knowledge search.

    When *scope* is ``conversation``, returns an ``$or`` filter that includes
    both conversation-scoped docs (filtered by *conversation_id*) **and**
    project-scoped docs so that project knowledge is always visible.
    """
    if scope == SCOPE_CONVERSATION:
        if not conversation_id:
            return None
        return {
            "$or": [
                {"$and": [{"scope": SCOPE_CONVERSATION}, {"conversation_id": conversation_id}]},
                {"scope": SCOPE_PROJECT},
            ],
        }
    return {"scope": scope}


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

        where = build_search_filter(scope, conversation_id)
        if where is None:
            bound_log.warning("search_skipped", reason="conversation scope requires conversation_id")
            return []

        collection = self._get_collection()
        results = collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where,
        )

        hits = []
        seen_files: set[str] = set()
        if results and results.get(CHROMA_RESULT_IDS):
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            distances = results["distances"][0]
            for doc, meta, dist in zip(docs, metas, distances, strict=False):
                score = 1.0 - dist
                threshold = MIN_RELEVANCE_SCORE_CONVERSATION if scope == SCOPE_CONVERSATION else MIN_RELEVANCE_SCORE
                if score < threshold:
                    continue
                fid = meta.get("file_id", "")
                if fid in seen_files:
                    continue
                seen_files.add(fid)
                hits.append(
                    {
                        "file_id": fid,
                        "name": meta.get(FIELD_KEY_NAME),
                        "file_type": meta.get(FIELD_KEY_FILE_TYPE),
                        "chunk_index": meta.get("chunk_index"),
                        "excerpt": doc,
                        "score": score,
                    }
                )

        filtered = len(distances) - len(hits) if results and results.get(CHROMA_RESULT_IDS) else 0
        bound_log.info("search_done", result_count=len(hits), filtered_below_threshold=filtered)
        return hits
