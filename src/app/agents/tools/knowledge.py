import structlog
from langchain_core.tools import tool

from app.infrastructure.vector.knowledge_searcher import KnowledgeSearcher

log = structlog.get_logger(__name__)

NO_RESULTS_MSG = "No relevant documents found."
HIGH_CONFIDENCE_SCORE = 0.5
RESULT_FORMAT = "{rank}. **{name}** (score: {score:.2f})\n   {excerpt}\n"
LOW_SCORE_FORMAT = "{rank}. **{name}** (score: {score:.2f}) — low confidence, may not be relevant\n"
CONTEXT_FRAMING = (
    "The following results were retrieved from the knowledge base. "
    "Use them only if directly relevant to the user's question. "
    "Low-scoring results are weak signals and may not be useful.\n\n"
)


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
        lines = []
        for i, r in enumerate(results):
            if r["score"] >= HIGH_CONFIDENCE_SCORE:
                lines.append(RESULT_FORMAT.format(rank=i + 1, name=r["name"], score=r["score"], excerpt=r["excerpt"]))
            else:
                lines.append(LOW_SCORE_FORMAT.format(rank=i + 1, name=r["name"], score=r["score"]))
        log.info("search_knowledge_done", result_count=len(results))
        return CONTEXT_FRAMING + "\n".join(lines)

    return search_knowledge
