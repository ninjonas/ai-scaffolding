## Service Layer Patterns

### Problem

Multiple services duplicate agent invocation orchestration: timing, logging, error handling, and result extraction. This violates DRY and SOLID principles (SRP, OCP, DIP).

Example violation:

```python
# src/app/service/voice.py
async def transcribe(self, audio_b64: str, mime_type: str) -> str:
    log.info("voice_transcribe_start", mime_type=mime_type)
    start = time.monotonic()
    try:
        result = await self._agent_graph.ainvoke({...})
        transcript = result.get("transcript", "").strip()
        duration_s = time.monotonic() - start
        log.info("voice_transcribe_done", duration_s=round(duration_s, 3))
        return transcript
    except Exception as exc:
        duration_s = time.monotonic() - start
        log.error("voice_transcribe_error", duration_s=round(duration_s, 3))
        raise

# src/app/service/chat.py
async def _invoke_agent(self, ...):  # SAME PATTERN REPEATED
    log.info("invoking_agent", ...)
    start = time.monotonic()
    result = await self._agent_graph.ainvoke({...})
    duration = time.monotonic() - start
    log.info("agent_invocation_complete", duration_s=round(duration, 3))
    ...
```

### Mandatory Patterns

#### 1. AgentOrchestrator: Agent Infrastructure Service

All services invoking agents must delegate to `AgentOrchestrator` (or protocol-compatible abstraction).

**Location:** `src/app/agents/orchestrator/orchestrator.py`

Lives in `agents/` (not `service/`) because it's agent infrastructure—the orchestration layer that translates agent execution into service-layer concerns (timing, logging, error handling). This separation keeps services free of agent-specific details.

```python
from app.agents.orchestrator import AgentOrchestrator

class AgentOrchestrator:
    """Domain Service: Standardized agent invocation with telemetry and resilience.

    Part of the agent infrastructure layer. Encapsulates the cross-cutting concern
    of invoking compiled agent graphs with centralized timing, structured logging,
    error handling, and result mapping.
    """

    def __init__(self, agent_graph: Any) -> None:
        self._agent_graph = agent_graph

    async def invoke_with_telemetry(
        self,
        operation_name: str,
        state_dict: dict,
        result_mapper: Callable[[dict], dict],
        **log_context
    ) -> dict:
        """Invoke agent with standardized timing, logging, error handling.

        Args:
            operation_name: Unique ID (e.g., "voice_transcribe", "chat_response")
            state_dict: Input state for agent.ainvoke()
            result_mapper: Pure function extracting domain result from agent output
            **log_context: Structured logging fields (conversation_id, mime_type, etc.)

        Returns:
            Mapped result from agent

        Raises:
            Any exception from agent.ainvoke() is logged with timing context and re-raised
        """
```

#### 2. AgentOutputParser: LangChain Abstraction

Agent graph outputs contain LangChain-specific objects (AIMessage, etc.). All LangChain attribute access must go through `AgentOutputParser`.

**Location:** `src/app/agents/orchestrator/output_parser.py`

```python
from app.agents.orchestrator import AgentOutputParser

class AgentOutputParser:
    """Parses LangChain graph outputs → domain-neutral dicts.

    Isolates LangChain-specific message handling from service logic.
    Services never directly access .content, .tool_calls on LangChain objects.
    """

    @staticmethod
    def extract_last_message(result: dict) -> dict:
        """Extract last message, converting LangChain → plain dict."""
        last_msg = result["messages"][-1]
        return {
            "content": getattr(last_msg, "content", str(last_msg)),
            "tool_calls": getattr(last_msg, "tool_calls", []),
        }

    @staticmethod
    def extract_transcript(result: dict) -> str:
        """Extract transcript from voice agent output."""
        return result.get("transcript", "").strip()
```

**Benefits:**

- Services work with plain dicts, not LangChain objects
- Single place to handle LangChain API changes
- Clearer separation: agents own LangChain, services own domain logic

#### 3. No Direct timing/logging in Services

**Forbidden in `src/app/service/*.py`:**

- `time.monotonic()` — use orchestrator instead
- Inline try/except wrapping `ainvoke()` — use orchestrator instead
- Manual `duration_s = time.monotonic() - start` — use orchestrator instead

**Exceptions:**

- `src/app/domain/services/` (domain services may contain timing logic)
- `src/app/agents/orchestrator/` (the orchestrator and parser)
- Temporary/spike work (must be commented and tracked)

#### 4. Result Extraction via Mapper Functions

Result transformation must be **pure functions** passed to orchestrator, not inline lambda or post-processing.

```python
# GOOD: Use AgentOutputParser to abstract LangChain
from app.agents.orchestrator import AgentOutputParser

def voice_result_mapper(result: dict) -> dict:
    """Map voice output to domain result."""
    return {"transcript": AgentOutputParser.extract_transcript(result)}

def chat_result_mapper(result: dict) -> dict:
    """Map chat output to domain result."""
    msg = AgentOutputParser.extract_last_message(result)
    return {"content": msg["content"], "tool_calls": msg["tool_calls"]}

async def transcribe(self, audio_b64: str, mime_type: str) -> str:
    result = await self._orchestrator.invoke_with_telemetry(
        "voice_transcribe",
        {"messages": [], "audio_b64": audio_b64, "mime_type": mime_type},
        voice_result_mapper,
        mime_type=mime_type,
    )
    return result["transcript"]

# BAD: Inline lambda
result = await self._orchestrator.invoke_with_telemetry(
    "voice_transcribe",
    {...},
    lambda r: {"transcript": r.get("transcript", "").strip()},  # ← Extract to module level
    mime_type=mime_type,
)
```

(Future: Mappers for DTO↔Pydantic/domain entity conversion will follow a similar pattern in `src/app/infrastructure/mappers/`.)

#### 5. AgentBroker: Facade for State Construction (NEW)

Services must **never build graph state dicts directly**. This couples them to graph schema. Instead, delegate to `AgentBroker` (Mediator pattern).

**Location:** `src/app/agents/orchestrator/broker.py`

```python
from app.agents.orchestrator import AgentBroker, AgentOrchestrator

class AgentBroker:
    """Mediates between service layer and orchestrator (Facade pattern).

    Services communicate in domain language. Broker translates to graph state schema
    and invokes orchestrator. Result is domain-neutral.

    Benefits:
    - Services only know domain concepts (content, audio_b64, mime_type)
    - Graph schema changes only affect broker, not services
    - State construction and orchestration are managed centrally
    - Single source of truth for each operation
    """

    def __init__(self, orchestrator: AgentOrchestrator) -> None:
        self._orchestrator = orchestrator

    async def chat_response(
        self,
        content: str,
        images: list[str] | None = None,
        **context,
    ) -> dict:
        """Chat operation in domain language."""
        state = {
            "messages": [{"role": "user", "content": content}],
            "images": images or [],
        }
        return await self._orchestrator.invoke_with_telemetry(
            "chat_response",
            state,
            chat_result_mapper,
            **context,
        )

    async def voice_transcribe(
        self,
        audio_b64: str,
        mime_type: str,
        **context,
    ) -> dict:
        """Voice operation in domain language."""
        state = {
            "messages": [],
            "audio_b64": audio_b64,
            "mime_type": mime_type,
        }
        return await self._orchestrator.invoke_with_telemetry(
            "voice_transcribe",
            state,
            voice_result_mapper,
            **context,
        )
```

**Service usage (ultra-clean):**

```python
class VoiceService:
    def __init__(self, broker: AgentBroker) -> None:
        self._broker = broker

    async def transcribe(self, audio_b64: str, mime_type: str) -> str:
        """Service speaks only domain language."""
        result = await self._broker.voice_transcribe(audio_b64, mime_type)
        return result["transcript"]
```

**Benefit: Service is now completely LangGraph-agnostic. Graph schema changes never reach service code.**

#### 6. Services Depend on Broker Protocol (NOT Orchestrator)

```python
# GOOD: Accept broker abstraction (domain language only)
class VoiceService:
    def __init__(self, broker: AgentBroker) -> None:
        self._broker = broker

class ChatService:
    def __init__(self, broker: AgentBroker) -> None:
        self._broker = broker

# BAD: Services directly depend on orchestrator or graph
class VoiceService:
    def __init__(self, orchestrator: AgentOrchestrator) -> None:
        # ← Violates DIP; service builds graph state dicts, couples to schema
        self._orchestrator = orchestrator
```

### Checked by

- `scripts/lib/check_service_patterns.py` — AST-based validator
- Run via `just check-service-patterns`
- Run via `just check` (aggregated)
- Git pre-commit hook enforces (via `just git-pre-commit`)

### Enforcement

| Violation                                            | Severity |
| ---------------------------------------------------- | -------- |
| `time.monotonic()` in `src/app/service/*.py`         | WARN     |
| Duplicate `ainvoke()` + timing pattern               | FAIL     |
| Service calls `self._agent_graph.ainvoke()` directly | FAIL     |
| Inline lambda result mapper                          | WARN     |

### See Also

- [Architecture Rules: Service Layer Integration](./architecture.md#how-to-apply)
- [Code Conventions: DI Requirements](./code-conventions.md#dependency-injection-python)
