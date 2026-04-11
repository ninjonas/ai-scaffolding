## LangGraph testing

Scope: unit tests for LangGraph agent code under `src/app/agents/`.

### Node unit tests

- Call **node functions directly** with a fixture state dict (shape matches graph state); assert the **returned partial dict** only.
- **Do not** use the compiled graph in unit tests (`compile()`, `ainvoke()` on the full graph). Test nodes in isolation.

### LLM

- Inject a **fake `BaseChatModel`** with deterministic **`AIMessage`** outputs. Avoid mocking the LLM via `patch` / `MagicMock` for node tests.

### Async

- Nodes that use **`ainvoke`** or other async paths must be tested with **`pytest.mark.asyncio`** and async test functions.

### Routing

- **Table-test** pure routing (`should_continue`, `decide_next`, …): `@pytest.mark.parametrize` golden state → expected next node / edge label.
- **Supervisor**: exercise **each route branch** in its own case (or param row); do not rely on one long graph run for branch coverage.

See skill: langgraph-testing for fixture patterns and fake LLM setup
