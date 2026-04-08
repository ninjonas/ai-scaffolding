import structlog
from langchain_core.tools import tool

log = structlog.get_logger()

MOCK_RESULTS = [
    {
        "title": "Mock Search Result",
        "url": "https://example.com/result",
        "snippet": "This is a mock search result. Replace with a real search API integration.",
    }
]


@tool
def search_web(query: str, num_results: int = 5) -> list[dict[str, str]]:
    """Search the web for information. Returns a list of results with title, url, and snippet."""
    log.info("web_search", query=query, num_results=num_results)
    return MOCK_RESULTS
