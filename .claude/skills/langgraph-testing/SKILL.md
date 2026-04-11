---
name: langgraph-testing
description: LangGraph/LangChain agent unit-test patterns — fake BaseChatModel, node isolation, async and routing table tests. Use when writing or reviewing tests under src/app/agents/.
argument-hint: "<agent-or-node-module>"
---

# LangGraph testing

Step-by-step patterns for unit-testing agent nodes and routers. Aligns with `test_gemini_cis.py`-style tests: small helpers, direct calls, explicit assertions — but use a **real fake `BaseChatModel`**, not HTTP mocks, for LLM nodes.

## Workflow

### 1. Node unit test (sync or async)

1. **Build state**: a `dict` with the keys the node reads (e.g. `messages`, `skill_context` for `ChatbotState`-shaped data). Use `HumanMessage` / `AIMessage` from `langchain_core.messages`.
2. **Call the node**: `result = await invoke_llm(state, llm)` (or sync `result = my_node(state)`).
3. **Assert partial update**: e.g. `assert "messages" in result` and check the last message content, `tool_calls`, etc. Do not require the full graph state.

Template:

```python
import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.agents.chatbot.nodes import should_continue
from app.agents.constants import NODE_END, NODE_TOOLS

def test_should_continue_no_tools():
    state = {"messages": [HumanMessage("hi"), AIMessage(content="plain reply")]}
    assert should_continue(state) == NODE_END
```

### 2. Fake `BaseChatModel` (fixed `AIMessage`)

Subclass `BaseChatModel`, implement `_generate` to return a `ChatResult` with your `AIMessage`, and override **`bind_tools`** to return `self` when the node calls `llm.bind_tools(...)` (default `BaseChatModel.bind_tools` raises `NotImplementedError`).

```python
from typing import Any, List, Optional

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult

class FixedAIMessageModel(BaseChatModel):
    """Minimal fake: always returns the configured AIMessage (sync + async invoke)."""

    response: AIMessage

    def _generate(
        self,
        messages: List[Any],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        return ChatResult(generations=[ChatGeneration(message=self.response)])

    @property
    def _llm_type(self) -> str:
        return "fixed-test-llm"

    def bind_tools(self, tools: Any, **kwargs: Any) -> Any:
        return self
```

Construct with `FixedAIMessageModel(response=AIMessage(content="x", tool_calls=[...]))` when testing tool-routing paths.

### 3. Async node test

Use `@pytest.mark.asyncio` and an `async def` test. With `asyncio_mode = "auto"` in `pyproject.toml`, marking remains useful for clarity and tooling.

```python
@pytest.mark.asyncio
async def test_invoke_llm_appends_message():
    from app.agents.chatbot.nodes import invoke_llm

    llm = FixedAIMessageModel(response=AIMessage(content="hello"))
    state = {"messages": [HumanMessage("hi")], "images": [], "skill_context": ""}
    out = await invoke_llm(state, llm)
    assert out["messages"][-1].content == "hello"
```

### 4. Routing table tests

Keep routers pure: parametrize `(state_dict, expected_next)` — no LLM, no graph.

```python
import pytest
from langchain_core.messages import AIMessage

from app.agents.constants import NODE_END, NODE_TOOLS

@pytest.mark.parametrize(
    ("state", "expected"),
    [
        (
            {
                "messages": [
                    AIMessage(content="", tool_calls=[{"name": "x", "args": {}, "id": "1"}]),
                ],
            },
            NODE_TOOLS,
        ),
        ({"messages": [AIMessage(content="done")]}, NODE_END),
    ],
)
def test_should_continue_routes(state, expected):
    from app.agents.chatbot.nodes import should_continue
    assert should_continue(state) == expected
```

Use the real `NODE_*` constants in assertions, not string literals, when matching production edges.

### 5. Integration tests vs unit tests

| Goal | Use |
|------|-----|
| Correctness of one node’s inputs/outputs, routing decisions | **Unit**: direct node calls + fake LLM |
| End-to-end agent behavior, checkpointing, multi-node flows | **Integration**: compiled graph, optional real or stubbed backends in a dedicated test module — few tests, mark slow if needed |

Do not block ordinary development on full-graph runs; keep the bulk of coverage in node and router unit tests.

## Related

- Rule: `.claude/rules/langgraph-testing.md`
- Agent structure/state: `.claude/rules/langgraph-conventions.md`
