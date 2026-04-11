import structlog
from langchain_core.tools import tool

from app.infrastructure.vector.knowledge_searcher import KnowledgeSearcher

log = structlog.get_logger(__name__)

NO_RESULTS_MSG = "No relevant documents found."
RESULT_FORMAT = "{rank}. **{name}** (score: {score:.2f})\n   {excerpt}\n"


def make_search_knowledge_tool(knowledge_searcher: KnowledgeSearcher):
    """Factory that closes over a KnowledgeSearcher and returns the search_knowledge tool."""

    @tool
    async def search_knowledge(
        query: str,
        scope: str = "project",
        conversation_id: str | None = None,
    ) -> str:
        """Search the knowledge base for documents relevant to the query.

        Use this for any question that might be answered by uploaded documents.
        Returns ranked excerpts with file names and relevance scores.
        """
        log.info("search_knowledge_start", query=query[:50], scope=scope)
        results = await knowledge_searcher.search(query, scope, conversation_id)
        if not results:
            log.info("search_knowledge_no_results")
            return NO_RESULTS_MSG
        lines = [
            RESULT_FORMAT.format(
                rank=i + 1, name=r["name"], score=r["score"], excerpt=r["excerpt"]
            )
            for i, r in enumerate(results)
        ]
        log.info("search_knowledge_done", result_count=len(results))
        return "\n".join(lines)

    return search_knowledge
