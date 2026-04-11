## Agent Conventions

### Folder structure

- Each agent is a flat package under `src/app/agents/<agent_name>/`
- Every agent folder contains: `__init__.py`, `graph.py`, `nodes.py`, `state.py`
- Agent-specific tools go in the agent's skill folder, not in the agent folder
- Shared tools go in `src/app/agents/tools/`

### Naming

- Agent folder names: `snake_case` (e.g., `chatbot`, `researcher`, `code_reviewer`)
- Graph variables: `<agent>_graph` (e.g., `chatbot_graph`)
- State classes: `<Agent>State` (e.g., `ChatbotState`)
- Node functions: `snake_case` verbs (e.g., `invoke_llm`, `run_tools`, `load_skills`)

### Orchestration

- Agents never import sibling agents — only an orchestrator (supervisor) composes them
- Imports flow downward: supervisor → sub-agents → tools/skills
- Use `Command(goto="agent_name")` for handoffs or direct subgraph composition
- Supervisor lives at `src/app/agents/supervisor/`

### Prompts

- All prompts are plain markdown files in `src/app/agents/prompts/`
- Shared system prompt: `prompts/system.md` (all agents inherit)
- Shared output format: `prompts/output_format.md`
- Agent-specific prompts: `prompts/<agent_name>/*.md`
- Load with `Path.read_text()` — no Jinja2, no `ChatPromptTemplate`
- Assembly: `system.md` + `persona.md` + rules + `output_format.md`

### Skills

- Each skill is a folder under `src/app/agents/skills/<skill_name>/`
- Required: `SKILL.md` (markdown instructions with YAML frontmatter)
- Optional: `tools.py` (LangChain `@tool` decorated functions)
- Skills are loaded progressively — agent sees catalog first, loads full instructions on demand
- The skill loader (`skills/loader.py`) exposes `load_skill` and `read_skill_file` as LangChain tools

### Rules

- Behavioral constraints live in `src/app/agents/rules/*.md`
- Loaded as system context at prompt assembly time

### LLM provider

- All LLM access goes through `src/app/shared/llm.py` factory
- Never instantiate `ChatOpenAI` directly in agent code
- Provider is configured via env vars (`LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`)

### Service layer integration

Services do NOT invoke agent graphs directly. Instead, they delegate to `AgentOrchestrator`:

**Pattern:**

- `AgentOrchestrator` lives in `src/app/agents/orchestrator/`
- Services receive pre-compiled orchestrators via DI at app startup
- Services call `await self._orchestrator.invoke_with_telemetry(operation_name, state_dict, result_mapper, **context)`

**Result transformation:**

- Agent outputs are transformed via `AgentOutputParser` to hide LangChain details
- Services never access LangChain message objects directly (no `.content`, `.tool_calls` attribute access)
- Result mappers extract domain-relevant data: pure functions in `src/app/service/mappers.py`

**Lifecycle:**

- Agent graphs compiled once at app startup in `main.py` and wrapped in orchestrators
- Orchestrators injected into services via DI — never instantiated in service code
- Orchestrators handle timing, logging, error handling centrally

**State shape:**

- Services pass state dicts matching the graph's input schema to `invoke_with_telemetry()`
- Orchestrator applies result_mapper to normalize output
- Services receive plain dicts with extracted domain data, never raw LangChain objects

### AgentOrchestrator and AgentOutputParser

**AgentOrchestrator** (`src/app/agents/orchestrator/orchestrator.py`):

- Domain service for standardized agent invocation with resilience and observability
- Centralizes timing, logging, error handling across all service-to-agent calls
- Signature: `async invoke_with_telemetry(operation_name, state_dict, result_mapper, **log_context)`
- Emits structured logs: `operation_name_start`, `operation_name_done`, `operation_name_error` with duration_s

**AgentOutputParser** (`src/app/agents/orchestrator/output_parser.py`):

- Abstracts LangChain-specific message handling away from services
- Pure static methods: `extract_last_message()`, `extract_transcript()`, etc.
- Transforms LangChain objects → plain dicts
- Single source of truth for LangChain API changes

**Example: Adding a new service**

```python
# 1. Define result mapper in src/app/service/mappers.py
from app.agents.orchestrator import AgentOutputParser

def my_result_mapper(result: dict) -> dict:
    msg = AgentOutputParser.extract_last_message(result)
    return {"summary": msg["content"]}

# 2. Inject orchestrator in service (from src/app/main.py: my_orchestrator = AgentOrchestrator(my_graph))
class MyService:
    def __init__(self, orchestrator: AgentOrchestrator) -> None:
        self._orchestrator = orchestrator

    async def do_work(self, prompt: str) -> str:
        result = await self._orchestrator.invoke_with_telemetry(
            "my_operation",
            {"messages": [{"role": "user", "content": prompt}]},
            my_result_mapper,
            operation_context=prompt[:50],
        )
        return result["summary"]
```

Services never touch LangChain directly; all message extraction goes through `AgentOutputParser`.
