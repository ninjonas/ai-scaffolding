import pytest

from app.agents.tools.knowledge import (
    CONTEXT_FRAMING,
    HIGH_CONFIDENCE_SCORE,
    make_search_knowledge_tool,
)
from app.domain.entities.knowledge_file import SCOPE_PROJECT


class _FakeSearcher:
    def __init__(self, results: list[dict]):
        self._results = results

    async def search(self, query: str, scope: str, conversation_id: str | None = None, top_k: int = 5) -> list[dict]:
        return self._results


@pytest.mark.asyncio
async def test_search_knowledge_returns_formatted_results():
    results = [{"name": "My Doc", "score": 0.92, "excerpt": "Some relevant text"}]
    tool = make_search_knowledge_tool(_FakeSearcher(results))
    output = await tool.ainvoke({"query": "test query"})
    assert "My Doc" in output
    assert "0.92" in output
    assert "Some relevant text" in output


@pytest.mark.asyncio
async def test_search_knowledge_empty_returns_no_results_message():
    tool = make_search_knowledge_tool(_FakeSearcher([]))
    output = await tool.ainvoke({"query": "test query"})
    assert "No relevant documents found" in output


@pytest.mark.asyncio
async def test_search_knowledge_multiple_results_ranked():
    results = [
        {"name": "Doc A", "score": 0.9, "excerpt": "First result"},
        {"name": "Doc B", "score": 0.7, "excerpt": "Second result"},
    ]
    tool = make_search_knowledge_tool(_FakeSearcher(results))
    output = await tool.ainvoke({"query": "test query", "scope": SCOPE_PROJECT})
    assert "1." in output
    assert "2." in output
    assert "Doc A" in output
    assert "Doc B" in output


@pytest.mark.asyncio
async def test_high_score_result_shows_excerpt():
    score = HIGH_CONFIDENCE_SCORE + 0.1
    results = [{"name": "Doc", "score": score, "excerpt": "Full excerpt here"}]
    tool = make_search_knowledge_tool(_FakeSearcher(results))
    output = await tool.ainvoke({"query": "q"})
    assert CONTEXT_FRAMING in output
    assert "Full excerpt here" in output


@pytest.mark.asyncio
async def test_low_score_result_hides_excerpt():
    score = HIGH_CONFIDENCE_SCORE - 0.1
    results = [{"name": "Weak Doc", "score": score, "excerpt": "Hidden text"}]
    tool = make_search_knowledge_tool(_FakeSearcher(results))
    output = await tool.ainvoke({"query": "q"})
    assert "Weak Doc" in output
    assert "Hidden text" not in output
    assert "low confidence" in output
