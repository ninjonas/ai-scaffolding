import structlog
from langchain_core.tools import tool

from app.infrastructure.vector.memory_searcher import MemorySearcher

log = structlog.get_logger(__name__)

MEMORY_RESULTS_SENTINEL = "MEMORY_RESULTS_PENDING"


def make_search_memory_tool(memory_searcher: MemorySearcher):
    """Factory that closes over a MemorySearcher and returns the search_memory tool."""

    @tool
    async def search_memory(query: str, current_conversation_id: str = "") -> dict:
        """Search past conversations for context relevant to the current question.

        Call this only when cross-conversation context would meaningfully change your answer —
        for example, when the user references something from a prior session. The user will be
        asked to confirm before retrieved context is used.
        """
        from langgraph.types import Command

        log.info(
            "search_memory_start",
            query=query[:50],
            current_conversation_id=current_conversation_id,
        )
        results = await memory_searcher.search(query, current_conversation_id)
        log.info("search_memory_done", result_count=len(results))
        return Command(update={"memory_results": results})

    return search_memory
