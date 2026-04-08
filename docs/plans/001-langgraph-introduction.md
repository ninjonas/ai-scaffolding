# Plan: Introduce LangGraph & LangChain to Scaffolding

**Status**: Done
**Date**: 2026-04-07
**Author**: Claude + Jonas

## Progress

- [x] **Phase 1**: Foundation — deps added, `src/app/shared/` created (config, llm, logging, di), `.env.example` updated
- [x] **Phase 2**: Agent system — prompts, skill loader, 4 starter skills, rules, shared image tool
- [x] **Phase 4**: Domain + service — entities (Message, Conversation), value objects (OptimizedImage), repository protocol, ChatService
- [x] **Phase 7**: Just recipes — `scripts/gen.just` + `gen-types` recipe, setup dirs, `.gitignore` updated
- [x] **Phase 1b**: Persistence layer — database.py, ORM models, data mapper, SQLConversationRepository, SQLAlchemyUnitOfWork
- [x] **Phase 3**: Agents — chatbot (all tools), researcher (web search), supervisor (LLM router)
- [x] **Phase 5**: API layer — DTOs (camelCase), ChatMapper, routes (health + chat), main.py rewritten with lifespan
- [x] **Phase 6**: Frontend chat UI — Chat, ChatInput, MessageBubble components, image upload, tool call display

*Note: Phase 7 rules/skills creation skipped — Claude rules already existed in `.claude/rules/`.*

## Overview

Add a LangGraph-based agent system to the scaffolding project, with a starter chatbot that analyzes images, uses tools, and delegates to subagents. The architecture follows PofEAA patterns (service layer, repository, data mapper, DTOs) and mimics Claude Code's `.claude/` pattern for prompt/skill/rule management.

## Decisions Made

| #   | Decision                     | Choice                                                                    |
| --- | ---------------------------- | ------------------------------------------------------------------------- |
| 1   | Agent code language          | Python-only (TS stays frontend)                                           |
| 2   | Top-level folder             | `src/app/agents/` (inside existing app package)                           |
| 3   | Agent folder structure       | Flat — each agent is a named folder under `agents/`                       |
| 4   | Orchestration pattern        | Supervisor as a sibling agent folder (industry standard)                  |
| 5   | Agent-to-agent communication | Orchestrator imports sub-agents; no lateral imports                       |
| 6   | Package structure            | `src/app/{api,agents,domain,service,shared}`                              |
| 7   | Shared agent resources       | Directly under `agents/` — `agents/prompts/`, `agents/tools/`, etc.       |
| 8   | LLM provider                 | OpenRouter.ai via `ChatOpenAI` with configurable base URL factory         |
| 9   | TS ↔ PY type sync            | Pydantic as source of truth, auto-gen TS types from OpenAPI spec          |
| 10  | Prompt management            | Plain markdown files loaded at runtime (no Jinja2, no LCEL templates)     |
| 11  | Skills pattern               | `SKILL.md` + `tools.py` co-located per skill (progressive loading)        |
| 12  | Starter app tools            | Image analysis + web search + file ops + calculator + researcher subagent |
| 13  | API transport                | REST (SSE streaming) + WebSocket, both through a shared service layer     |
| 14  | Image optimization           | Client-side resize for preview + server-side (Pillow) before LLM call     |
| 15  | Logging                      | Verbose structured logging end-to-end (structlog)                         |
| 16  | Persistence                  | SQLite + SQLAlchemy (async), repository + unit of work + data mapper      |
| 17  | Search API                   | Mock for now (no external API key needed)                                 |
| 18  | WebSocket auth               | Simple token-based auth                                                   |

## Target Folder Structure

```
src/app/
├── api/                          # FastAPI routes (thin controllers)
│   ├── __init__.py
│   ├── router.py                 # mounts all route modules
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── chat.py               # POST /api/chat (SSE), WS /api/chat/ws
│   │   └── health.py             # GET /health
│   ├── dto/                      # Pydantic request/response models (DTOs)
│   │   ├── __init__.py
│   │   ├── chat.py               # ChatRequestDTO, ChatResponseDTO, etc.
│   │   └── common.py             # shared DTOs (pagination, errors)
│   └── mappers/                  # Data Mappers (Fowler) — DTO ↔ domain
│       ├── __init__.py
│       └── chat.py               # ChatMapper
│
├── agents/                       # LangGraph agent system
│   ├── __init__.py
│   ├── chatbot/                  # main chatbot agent
│   │   ├── __init__.py
│   │   ├── graph.py              # LangGraph StateGraph definition
│   │   ├── nodes.py              # node functions
│   │   └── state.py              # typed state schema
│   ├── researcher/               # subagent — research/web search
│   │   ├── __init__.py
│   │   ├── graph.py
│   │   ├── nodes.py
│   │   └── state.py
│   ├── supervisor/               # orchestrator — wires agents together
│   │   ├── __init__.py
│   │   ├── graph.py
│   │   ├── nodes.py
│   │   └── state.py
│   ├── prompts/                  # shared prompt templates (markdown)
│   │   ├── system.md             # global system prompt (all agents inherit)
│   │   ├── output_format.md      # shared output format template
│   │   ├── chatbot/
│   │   │   ├── persona.md
│   │   │   └── image_analysis.md
│   │   └── researcher/
│   │       └── persona.md
│   ├── skills/                   # skill bundles (SKILL.md + tools.py)
│   │   ├── __init__.py
│   │   ├── loader.py             # skill catalog + progressive loader
│   │   ├── analyze_image/
│   │   │   ├── SKILL.md
│   │   │   └── tools.py
│   │   ├── web_search/
│   │   │   ├── SKILL.md
│   │   │   └── tools.py
│   │   ├── file_ops/
│   │   │   ├── SKILL.md
│   │   │   └── tools.py
│   │   └── calculator/
│   │       ├── SKILL.md
│   │       └── tools.py
│   ├── rules/                    # behavioral constraints (markdown)
│   │   ├── safety.md
│   │   └── tone.md
│   └── tools/                    # shared tools (used across agents)
│       ├── __init__.py
│       └── image.py              # image optimization utilities
│
├── domain/                       # domain layer (DDD)
│   ├── __init__.py
│   ├── entities/
│   │   ├── __init__.py
│   │   ├── message.py            # Message entity
│   │   └── conversation.py       # Conversation aggregate
│   ├── value_objects/
│   │   ├── __init__.py
│   │   └── image.py              # OptimizedImage value object
│   └── repositories/             # repository interfaces (abstractions)
│       ├── __init__.py
│       └── conversation.py       # ConversationRepository protocol
│
├── infrastructure/               # persistence layer (PofEAA)
│   ├── __init__.py
│   ├── database.py               # SQLAlchemy engine, session factory
│   ├── models/                   # SQLAlchemy ORM models (data mapper)
│   │   ├── __init__.py
│   │   ├── conversation.py       # ConversationModel
│   │   └── message.py            # MessageModel
│   ├── mappers/                  # domain ↔ ORM data mappers (Fowler)
│   │   ├── __init__.py
│   │   └── conversation.py       # ConversationDataMapper
│   ├── repositories/             # concrete repository implementations
│   │   ├── __init__.py
│   │   └── conversation.py       # SQLConversationRepository
│   └── unit_of_work.py           # Unit of Work pattern
│
├── service/                      # application service layer (PofEAA)
│   ├── __init__.py
│   └── chat.py                   # ChatService — orchestrates API ↔ agent
│
├── shared/                       # cross-cutting concerns
│   ├── __init__.py
│   ├── config.py                 # Settings (pydantic-settings)
│   ├── llm.py                    # LLM factory (create_llm)
│   ├── logging.py                # structlog configuration
│   └── di.py                     # dependency injection container
│
├── __init__.py
└── main.py                       # FastAPI app entry point (updated)
```

## Implementation Phases

### Phase 1: Foundation (infrastructure + shared layer)

1. **Add Python dependencies** to `pyproject.toml`
   - `langgraph`, `langchain-core`, `langchain-openai`
   - `pydantic-settings`, `structlog`, `Pillow`
   - `sqlalchemy[asyncio]>=2`, `aiosqlite` (async SQLite)
   - Dev: `langgraph-cli` (optional)
1. **Create `src/app/shared/`**
   - `config.py` — Settings class with LLM provider config, env vars
   - `llm.py` — `create_llm(settings)` factory returning ChatOpenAI
   - `logging.py` — structlog config (JSON file + human stdout)
   - `di.py` — simple DI container
1. **Update `.env.example`** with LLM config vars
1. **Create Claude rules** for new patterns (logging enforcement, document locations, agent conventions)

### Phase 1b: Persistence layer (SQLAlchemy + PofEAA)

5. **Create `src/app/infrastructure/`**
   - `database.py` — async SQLAlchemy engine + session factory (SQLite at `data/app.db`)
   - `models/conversation.py` — `ConversationModel` ORM model
   - `models/message.py` — `MessageModel` ORM model
1. **Create domain repository interfaces** in `src/app/domain/repositories/`
   - `conversation.py` — `ConversationRepository` protocol (abstract)
1. **Create infrastructure implementations**
   - `repositories/conversation.py` — `SQLConversationRepository` (concrete)
   - `mappers/conversation.py` — `ConversationDataMapper` (ORM ↔ domain)
   - `unit_of_work.py` — `SQLAlchemyUnitOfWork` wrapping session/transaction
1. **Wire DI** — register repository + unit of work in DI container

### Phase 2: Agent system (prompts, skills, rules)

5. **Create prompt templates** in `src/app/agents/prompts/`
   - `system.md` — shared system prompt
   - `output_format.md` — structured output template
   - Agent-specific persona files
1. **Create skill loader** in `src/app/agents/skills/loader.py`
   - Scan skill directories, build catalog
   - `load_skill(name)` and `read_skill_file(name, filename)` as LangChain tools
1. **Create starter skills** with `SKILL.md` + `tools.py`
   - `analyze_image/` — image description using vision model
   - `web_search/` — web search tool
   - `file_ops/` — basic file operations
   - `calculator/` — math evaluation
1. **Create agent rules** in `src/app/agents/rules/`
   - `safety.md` — guardrails
   - `tone.md` — communication style

### Phase 3: Agents (chatbot, researcher, supervisor)

9. **Create chatbot agent** in `src/app/agents/chatbot/`
   - `state.py` — ChatState with messages, images, skill context
   - `nodes.py` — agent node, tool node, skill loading node
   - `graph.py` — compiled StateGraph
1. **Create researcher subagent** in `src/app/agents/researcher/`
   - Web search focused, returns structured findings
1. **Create supervisor** in `src/app/agents/supervisor/`
   - Wires chatbot + researcher
   - Routes based on task type (image analysis → chatbot, research → researcher)

### Phase 4: Domain + Service layer

12. **Create domain entities** in `src/app/domain/`
    - `Message`, `Conversation`, `OptimizedImage`
01. **Create `ChatService`** in `src/app/service/chat.py`
    - `send_message()` — invoke agent, return response
    - `stream_message()` — invoke agent, yield SSE chunks
    - Handles image optimization before passing to agent
    - Verbose logging at every step

### Phase 5: API layer

14. **Create DTOs** in `src/app/api/dto/`
    - `ChatRequestDTO` (message, images, conversation_id)
    - `ChatResponseDTO` (message, metadata, tool_calls)
    - Pydantic models with `alias_generator = to_camel` for JSON camelCase
01. **Create data mappers** in `src/app/api/mappers/`
    - `ChatMapper` — DTO ↔ domain entity conversion
01. **Create routes** in `src/app/api/routes/`
    - `POST /api/chat` — SSE streaming response
    - `WS /api/chat/ws` — WebSocket for real-time chat
    - `GET /health` — existing, moved to routes module
01. **Update `main.py`** — mount API router, configure CORS, init logging
01. **Generate TypeScript types** from OpenAPI spec
    - Add `openapi-typescript` to web devDependencies
    - Add just recipe: `just gen-types` → generates `src/web/src/api/types.ts`

### Phase 6: Frontend chat UI

19. **Create chat components** in `src/web/src/`
    - Chat interface with message list, input, image upload
    - Image preview with client-side resize before upload
    - Streaming response display
    - Tool call visualization

### Phase 7: Just recipes + Claude skills

20. **Add just recipes** for new workflows
    - `just gen-types` — generate TS types from OpenAPI
    - Update `just dev-start` if needed
01. **Create/update Claude skills**
    - Skill for adding new agents
    - Skill for adding new skills
    - Skill for adding new tools
01. **Update Claude rules**
    - Agent development conventions
    - Logging enforcement rule

## Persistence Architecture (PofEAA + DDD + SOLID)

### Layer separation

```
API Layer          Service Layer       Domain Layer         Infrastructure
───────────        ─────────────       ────────────         ──────────────
Routes/DTOs   →    ChatService    →    Conversation    ←    SQLConversationRepo
(camelCase)        (orchestrates)      Message              ConversationDataMapper
                   UnitOfWork          Repository(Protocol)  SQLAlchemyUnitOfWork
```

### Repository pattern (interface in domain, impl in infrastructure)

```python
# src/app/domain/repositories/conversation.py
from typing import Protocol

class ConversationRepository(Protocol):
    async def get_by_id(self, conversation_id: str) -> Conversation | None: ...
    async def save(self, conversation: Conversation) -> None: ...
    async def list_recent(self, limit: int = 20) -> list[Conversation]: ...
```

```python
# src/app/infrastructure/repositories/conversation.py
class SQLConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, conversation_id: str) -> Conversation | None:
        model = await self._session.get(ConversationModel, conversation_id)
        return ConversationDataMapper.to_domain(model) if model else None
```

### Data mapper (Fowler) — ORM ↔ domain (separate from API DTO mapper)

```python
# src/app/infrastructure/mappers/conversation.py
class ConversationDataMapper:
    @staticmethod
    def to_domain(model: ConversationModel) -> Conversation:
        return Conversation(id=model.id, messages=[...], ...)

    @staticmethod
    def to_model(entity: Conversation) -> ConversationModel:
        return ConversationModel(id=entity.id, ...)
```

### Two mapper layers (important distinction)

| Layer          | Mapper                                   | Converts                                       |
| -------------- | ---------------------------------------- | ---------------------------------------------- |
| API            | `api/mappers/chat.py`                    | DTO ↔ domain entity (camelCase ↔ snake_case)   |
| Infrastructure | `infrastructure/mappers/conversation.py` | Domain entity ↔ ORM model (Fowler data mapper) |

### Unit of Work

```python
# src/app/infrastructure/unit_of_work.py
class SQLAlchemyUnitOfWork:
    def __init__(self, session_factory: async_sessionmaker) -> None:
        self._session_factory = session_factory

    async def __aenter__(self) -> Self:
        self._session = self._session_factory()
        self.conversations = SQLConversationRepository(self._session)
        return self

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

    async def __aexit__(self, *args) -> None:
        await self._session.close()
```

## DTO ↔ Domain Mapping Convention

### Python (snake_case internally, camelCase in JSON)

```python
# src/app/api/dto/chat.py
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

class ChatRequestDTO(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    
    message: str
    conversation_id: str | None = None
    images: list[str] = []  # base64 encoded
```

### TypeScript (camelCase — auto-generated from OpenAPI)

```typescript
// src/web/src/api/types.ts (auto-generated)
export interface ChatRequest {
  message: string;
  conversationId?: string;
  images?: string[];
}
```

### Data Mapper (Fowler pattern)

```python
# src/app/api/mappers/chat.py
class ChatMapper:
    @staticmethod
    def to_domain(dto: ChatRequestDTO) -> Message:
        return Message(content=dto.message, images=dto.images)

    @staticmethod
    def to_dto(message: Message) -> ChatResponseDTO:
        return ChatResponseDTO(message=message.content, ...)
```

## Prompt Assembly Pattern

```python
# How prompts are assembled at runtime
system = Path("agents/prompts/system.md").read_text()
persona = Path("agents/prompts/chatbot/persona.md").read_text()
output_fmt = Path("agents/prompts/output_format.md").read_text()
rules = [Path(f).read_text() for f in Path("agents/rules").glob("*.md")]

full_prompt = "\n\n".join([system, persona, *rules, output_fmt])

# Used in LangGraph node
messages = [SystemMessage(content=full_prompt), *state["messages"]]
response = llm.invoke(messages)
```

## LLM Provider Configuration

```env
# .env
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_API_KEY=sk-or-...
LLM_MODEL=anthropic/claude-sonnet-4-20250514

# To switch to OpenAI directly:
# LLM_BASE_URL=https://api.openai.com/v1
# LLM_API_KEY=sk-...
# LLM_MODEL=gpt-4o

# To switch to local Ollama:
# LLM_BASE_URL=http://localhost:11434/v1
# LLM_API_KEY=ollama
# LLM_MODEL=llama3
```

## Dependencies to Add

```toml
# pyproject.toml additions
dependencies = [
    # existing...
    "langgraph>=0.3",
    "langchain-core>=0.3",
    "langchain-openai>=0.3",
    "pydantic-settings>=2",
    "structlog>=24",
    "Pillow>=10",
    "sqlalchemy[asyncio]>=2",
    "aiosqlite>=0.20",
]
```

## Naming Conventions

| Concept             | Python                  | TypeScript                          |
| ------------------- | ----------------------- | ----------------------------------- |
| Variables/functions | `snake_case`            | `camelCase`                         |
| Classes             | `PascalCase`            | `PascalCase`                        |
| Constants           | `UPPER_SNAKE_CASE`      | `UPPER_SNAKE_CASE`                  |
| DTOs                | `ChatRequestDTO`        | `ChatRequest` (no suffix, auto-gen) |
| Agent names         | `snake_case` folders    | N/A (Python only)                   |
| Prompt files        | `snake_case.md`         | N/A                                 |
| API JSON keys       | `camelCase` (via alias) | `camelCase` (native)                |

## Resolved Questions

- [x] **Conversation persistence**: SQLite + SQLAlchemy (full PofEAA: repository, unit of work, data mapper)
- [x] **Search API**: Mock for now (no external API key needed)
- [x] **WebSocket auth**: Simple token-based auth
