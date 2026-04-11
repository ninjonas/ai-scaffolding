## LangGraph conventions

Scope: LangGraph/LangChain graph code under `src/app/agents/`. Complements `agent-conventions.md` (layout, prompts, skills, LLM factory)—do not repeat those here.

### State

- Subclass `MessagesState` for extra keys (e.g. `ChatbotState`, `ResearcherState`).
- Nodes return **partial dicts** only; never mutate the incoming `state` in place.
- Add `Annotated[..., reducer]` only for append/merge list semantics; leave a one-line note on why.

### Nodes

- Separate nodes when roles diverge: routing vs LLM vs tools/I/O (e.g. `should_continue` vs `invoke_llm` in `chatbot/nodes.py`).
- Wrap fragile I/O (`llm` calls, custom tool logic) in `try/except`; prefer returning a recoverable error in state over uncaught exceptions when the run should continue.
- Tool-calling loops must enforce a hard cap (e.g. `max_steps`).

### Tools (`@tool`)

- Docstring states **when** to call the tool (model contract). `snake_case` name, full type hints; use Pydantic `args_schema` for non-trivial arguments.

### Supervisor and subgraphs

- One authoritative routing step: the LLM sets the route in a single node; the conditional reads stable state (e.g. `route_task` → `next_agent` → `decide_next` in `supervisor/nodes.py`).
- Delegate via compiled subgraphs named `<agent>_graph`; **project** state and reset fields the child owns (see `chatbot_graph` / `researcher_graph` `ainvoke` payloads in `supervisor/graph.py`).

### LLM typing

- Graph factories and node helpers take `BaseChatModel` (`chatbot/graph.py`, `supervisor/graph.py`, `researcher/graph.py`). Never annotate `ChatOpenAI`.
