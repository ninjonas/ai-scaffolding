# Plan: ChromaDB RAG — Semantic Knowledge and Memory Search

**Status**: Draft
**Date**: 2026-04-11
**Author**: Jonas + Claude

## Overview

Upgrade the knowledge base and chat history system to Full RAG using ChromaDB. Knowledge files are
chunked on upload and embedded into ChromaDB. Messages are embedded after each exchange. The agent
gains two new tools: `search_knowledge` (semantic search over uploaded documents) and
`search_memory` (semantic search over past conversations across all sessions). Cross-conversation
retrieval is HITL-gated: the agent runs a silent relevance check first, and only interrupts the
user with a confirmation prompt when it judges past context would meaningfully change its answer.
SQLite remains the source of truth for all structured data. ChromaDB is a search index only.
The existing catalog injection pattern from plan 005 is dropped in favour of semantic retrieval.

## Decisions Made

| #   | Decision                  | Choice                                                                                                                                                                                                                                                                                                                                                 |
| --- | ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | Vector store              | ChromaDB (persistent, embedded, SQLite-backed)                                                                                                                                                                                                                                                                                                         |
| 2   | Scope                     | Documents + chat history + cross-conversation search                                                                                                                                                                                                                                                                                                   |
| 3   | HITL trigger              | On read only — agent-decided, surfaces confirmation only when relevance check passes                                                                                                                                                                                                                                                                   |
| 4   | Source of truth           | SQLite via SQLAlchemy (unchanged)                                                                                                                                                                                                                                                                                                                      |
| 5   | Catalog injection         | Dropped — replaced by `search_knowledge` semantic tool                                                                                                                                                                                                                                                                                                 |
| 6   | Embedding model           | OpenAI `text-embedding-3-small` via existing LLM factory / OpenRouter                                                                                                                                                                                                                                                                                  |
| 7   | Chunking strategy         | Fixed-size with overlap: 512 tokens, 64-token overlap                                                                                                                                                                                                                                                                                                  |
| 8   | ChromaDB collections      | Two collections: `knowledge_files` and `chat_messages`                                                                                                                                                                                                                                                                                                 |
| 9   | HITL mechanism            | Node-level `interrupt()` in LangGraph (not tool-level) — avoids double-execution on resume                                                                                                                                                                                                                                                             |
| 10  | Cross-conversation search | Spans all conversations for the project scope                                                                                                                                                                                                                                                                                                          |
| 11  | Checkpointing             | SqliteSaver (dev) — required prerequisite for interrupt/resume to function                                                                                                                                                                                                                                                                             |
| 12  | Embedding indexing        | FastAPI BackgroundTasks — fire-and-forget, decoupled from chat response path                                                                                                                                                                                                                                                                           |
| 13  | RAG strategy              | Hybrid — always retrieve for `search_knowledge`; agent-decided for `search_memory`                                                                                                                                                                                                                                                                     |
| 14  | Indexing content          | LLM-enriched metadata (name, description, tags) is the primary searchable document for all file types. Text files additionally index content chunks for detail queries. Images index only the LLM summary (no raw content); the image is a reference to the upload context (conversation_id, uploaded_at). Follows the Multi-Vector Retriever pattern. |
| 15  | Search scope fallback     | `search_knowledge` queries both project AND conversation scopes (combined), not one or the other. Ensures project knowledge is always reachable from conversation context.                                                                                                                                                                             |

## Target Folder Structure

```
src/app/
  agents/
    tools/
      knowledge.py           # Updated: add search_knowledge tool, remove catalog injection
      memory.py              # New: search_memory tool with HITL interrupt
    chatbot/
      nodes.py               # Updated: register search_knowledge + search_memory, add await_memory_confirm node, remove catalog injection
      state.py               # Updated: add memory_results + memory_confirmed fields for HITL state
      graph.py               # Updated: add await_memory_confirm node + conditional edge for HITL routing
  infrastructure/
    vector/
      __init__.py
      client.py              # ChromaDB client factory (persistent client, path from settings)
      knowledge_indexer.py   # Chunk + embed knowledge files into chromadb
      message_indexer.py     # Embed messages into chromadb after each exchange
      knowledge_searcher.py  # Semantic search over knowledge_files collection
      memory_searcher.py     # Semantic search over chat_messages collection
  service/
    knowledge.py             # Updated: call knowledge_indexer on upload/delete
    chat.py                  # Updated: call message_indexer after assistant reply, remove catalog fetch
  shared/
    settings.py              # Updated: add CHROMA_PATH setting
```

## Implementation Phases

### Phase 0: LangGraph checkpointing `Not Started`

Required prerequisite — `interrupt()`/resume cannot function without a checkpointer.

- [ ] Add `langgraph-checkpoint-sqlite` to `pyproject.toml`.
- [ ] Create `src/app/shared/checkpointer.py`: factory returning `AsyncSqliteSaver` using a path from `Settings` (default: `./data/checkpoints.db`). Singleton per process.
- [ ] Update graph factory in `src/app/agents/chatbot/graph.py`: compile graph with `checkpointer=get_checkpointer(settings)`.
- [ ] Update `AgentBroker.chat_response()`: pass `config={"configurable": {"thread_id": conversation_id}}` on every `ainvoke` call so the checkpointer can save/restore state per conversation.
- [ ] Update `POST /api/chat/{conversation_id}/resume` route (create if not exists): loads graph, calls `ainvoke` with same `thread_id` and resume payload to continue an interrupted run.
- [ ] Verify interrupt/resume round-trip with a minimal test before proceeding to other phases.

### Phase 1: ChromaDB infrastructure `Not Started`

- [ ] Add `chromadb` and `openai` to `pyproject.toml` dependencies.
- [ ] Add `CHROMA_PATH` to `Settings` (default: `./data/chroma`).
- [ ] Create `src/app/infrastructure/vector/client.py`: factory returning a `chromadb.PersistentClient` using `settings.chroma_path`. Singleton pattern — one client per process.
- [ ] Create `src/app/infrastructure/vector/knowledge_indexer.py`: indexes two document types per file. (1) A **summary chunk**: composed from LLM-enriched name + description + tags (`"{name}. {description} Tags: {tags}"`), always indexed for all file types. (2) **Content chunks** (text files only): raw content chunked at 512 tokens / 64-token overlap. Images get only the summary chunk; the image is a reference to its upload context. All chunks share metadata: `file_id`, `chunk_index`, `name`, `file_type`, `scope`, `conversation_id`, `doc_type` (`"summary"` or `"chunk"`). Embeds via OpenAI `text-embedding-3-small`. Upserts into `knowledge_files` collection.
- [ ] Create `src/app/infrastructure/vector/message_indexer.py`: accepts message id, content, role, conversation_id, timestamp. Embeds via same model. Upserts into `chat_messages` collection with metadata: `message_id`, `conversation_id`, `role`, `created_at`.
- [ ] Create `src/app/infrastructure/vector/knowledge_searcher.py`: `search(query, scope, conversation_id, top_k=5) -> list[dict]`. Queries `knowledge_files` collection. When scope is `conversation`, queries both conversation-scoped docs (filtered by conversation_id) AND project-scoped docs in a single pass using ChromaDB `$or` filter (decision 15). Deduplicates by file_id, keeping highest score.
- [ ] Create `src/app/infrastructure/vector/memory_searcher.py`: `search(query, current_conversation_id, top_k=5) -> list[dict]`. Queries `chat_messages` collection, excludes current conversation_id, returns ranked results with conversation_id and timestamp metadata.

### Phase 2: Knowledge service integration `Not Started`

- [ ] Fix `knowledge_frontmatter_llm.py`: LLM image description fails with `OutputParserException` on escaped newlines in JSON. Switch from `json_mode` to Pydantic structured output (already using `KnowledgeFrontmatterSchema`) so parsing is handled by LangChain, not manual JSON decode.
- [ ] Update `KnowledgeService.upload()`: after saving to SQLite, call `knowledge_indexer.index(file)`. Log indexing start/done with chunk count.
- [ ] Update `KnowledgeService.delete()`: after removing from SQLite, delete all chunks for `file_id` from `knowledge_files` ChromaDB collection.
- [ ] Update `KnowledgeService.update()`: re-index on content change (delete old chunks, index new content).
- [ ] Remove `get_catalog()` method and `build_knowledge_catalog()` utility — no longer used.

### Phase 3: Agent tools and HITL node `Not Started`

Node-level interrupt is used instead of tool-level to avoid the double-execution bug (on resume,
nodes re-run from the top — a tool-level interrupt would fire the tool twice).

- [ ] Replace `read_knowledge_file` tool in `src/app/agents/tools/knowledge.py` with `search_knowledge`: takes `query: str`, calls `knowledge_searcher.search()`, returns top-k chunk results formatted as a ranked list with file name, chunk excerpt, and relevance score. Always retrieves (hybrid strategy) — no agent gate on this tool.
- [ ] Create `src/app/agents/tools/memory.py`: `search_memory` tool. Takes `query: str`. Calls `memory_searcher.search()`, stores results in state (`memory_results`), returns a sentinel string `"MEMORY_RESULTS_PENDING"`. Does NOT call `interrupt()` — that happens in the node.
- [ ] Add `await_memory_confirm` node in `chatbot/nodes.py`: checks if `state["memory_results"]` is set. If set, calls `interrupt({"type": "memory_confirm", "results": state["memory_results"], "prompt": "..."})`. On resume, reads `memory_confirmed` from state. If approved, formats results and appends as a `SystemMessage` to messages. If denied, clears `memory_results` and continues.
- [ ] Add conditional edge in `chatbot/graph.py`: after `run_tools`, route to `await_memory_confirm` if `memory_results` is set, else back to `invoke_llm`.
- [ ] Update `ALL_TOOLS` in `chatbot/nodes.py`: add `search_knowledge` and `search_memory`, remove `read_knowledge_file`.
- [ ] Update `ChatbotState` in `chatbot/state.py`: add `memory_results: list[dict]` and `memory_confirmed: bool | None` fields.
- [ ] Remove catalog injection from `invoke_llm` in `chatbot/nodes.py`: delete `knowledge_catalog` state field read and system prompt append.

### Phase 4: Chat service integration `Not Started`

- [ ] Update the chat route handler in `src/app/api/routes/chat.py`: after saving messages, enqueue indexing via FastAPI `BackgroundTasks` — `background_tasks.add_task(message_indexer.index, message)` for both user and assistant messages. Indexing is fire-and-forget; response is not blocked.
- [ ] Remove `knowledge_catalog` fetch from `ChatService.send_message()`.
- [ ] Update `AgentBroker.chat_response()`: remove `knowledge_catalog` parameter.
- [ ] Remove `knowledge_catalog` field from `ChatbotState`.
- [ ] Update `KnowledgeService.upload()` route handler similarly: enqueue `knowledge_indexer.index` via `BackgroundTasks` after the file is saved to SQLite.

### Phase 5: Frontend HITL confirmation UI `Not Started`

- [ ] Detect `interrupt` event in the chat stream response (backend signals interrupt via a new SSE event type `memory_confirm`).
- [ ] When `memory_confirm` arrives, render an inline confirmation card in the chat thread showing: "I found relevant context from past conversations. Use it?" with a summary of the top results (conversation date, excerpt), and Approve / Skip buttons.
- [ ] On Approve: send `POST /api/chat/{id}/resume` with `approved: true`. On Skip: send with `approved: false`.
- [ ] Add `POST /api/chat/{conversation_id}/resume` route in `src/app/api/routes/chat.py` that resumes the interrupted LangGraph run.
- [ ] Show a subtle "Searching memory..." indicator in the chat while the agent is running the relevance check (before the interrupt fires).

### Phase 6: Backfill existing data `Not Started`

- [ ] Create `scripts/lib/backfill_chroma.py`: loads all `KnowledgeFile` records from SQLite, indexes each into `knowledge_files` collection. Loads all `Message` records, indexes into `chat_messages` collection. Idempotent (upsert). Logs progress.
- [ ] Add `just chroma-backfill` recipe in `scripts/setup.just` delegating to `backfill_chroma.py`.
- [ ] Document backfill step in `README.md` under setup.

## Agent Execution Strategy

### Parallelism map

| Phase | Depends on | Agent type | Notes                                                     |
| ----- | ---------- | ---------- | --------------------------------------------------------- |
| 0     | None       | backend    | Checkpointing prerequisite — must complete before Phase 3 |
| 1     | None       | backend    | Pure infrastructure, can run parallel with Phase 0        |
| 2     | Phase 1    | backend    | Needs indexer/searcher from Phase 1                       |
| 3     | 0, 1       | backend    | Needs checkpointer (Phase 0) and searcher (Phase 1)       |
| 4     | 2, 3       | backend    | Needs updated service (Phase 2) and tools/nodes (Phase 3) |
| 5     | Phase 4    | frontend   | Needs resume route and SSE event from Phase 4             |
| 6     | Phase 1    | backend    | Independent of Phases 2-5, can run parallel with Phase 2  |

### Sequencing constraints

- Phases 0 and 1 can run in parallel — they are fully independent.
- Phase 3 blocks on both Phase 0 (checkpointer required for interrupt) and Phase 1 (searcher required for tools).
- Phases 2 and 3 can run in parallel once their respective prerequisites complete.
- Phase 4 blocks on both Phase 2 and Phase 3.
- Phase 5 (frontend) blocks on Phase 4 (needs the resume endpoint and SSE event).
- Phase 6 (backfill) only needs Phase 1 and can run concurrently with Phases 2-4.

### Agent instructions

- **Backend agent (Phase 1)**: Build ChromaDB infrastructure only — no app layer changes. Use
  `chromadb.PersistentClient`. Two collections: `knowledge_files` and `chat_messages`. Embedding
  via OpenAI `text-embedding-3-small`. Chunking: 512 tokens, 64-token overlap using
  `tiktoken`. Follow DI conventions: inject `Settings` for path, inject embedding function.
- **Backend agent (Phase 2)**: Update `KnowledgeService` to call indexer on upload/update/delete.
  Remove `get_catalog()` and `build_knowledge_catalog()`. Follow existing service patterns —
  use `AgentOrchestrator` if async indexing is needed.
- **Backend agent (Phase 3)**: Replace `read_knowledge_file` with `search_knowledge`. Add
  `search_memory` with `interrupt()`. Mirror existing tool factory pattern
  (`make_read_knowledge_file_tool`) for dependency injection. `search_memory` docstring is the
  model contract — make it explicit about when to call it.
- **Backend agent (Phase 4)**: Wire indexing into `ChatService`. Remove catalog fetch and
  `knowledge_catalog` state field end-to-end. Add `POST /api/chat/{id}/resume` route.
- **Frontend agent (Phase 5)**: Add `memory_confirm` SSE event handling. Inline confirmation card
  in the chat thread. Approve/Skip buttons call the resume endpoint. Match existing chat UI
  patterns and motion conventions from plan 005.
- **Backend agent (Phase 6)**: Backfill script only. Idempotent upserts. Progress logging.
  No production code changes.

## Key Patterns

### ChromaDB client factory

```python
# src/app/infrastructure/vector/client.py
import chromadb
from app.shared.settings import Settings

_client: chromadb.PersistentClient | None = None

def get_chroma_client(settings: Settings) -> chromadb.PersistentClient:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=str(settings.chroma_path))
    return _client
```

### search_memory tool + await_memory_confirm node (node-level HITL)

Tool-level `interrupt()` causes double-execution: when the graph resumes, the node re-runs from
the top and the tool fires again. The fix is to store results in state from the tool, then
interrupt in a dedicated node — nodes are idempotent on resume.

```python
# src/app/agents/tools/memory.py
from langchain_core.tools import tool

@tool
async def search_memory(query: str) -> dict:
    """Search past conversations for context relevant to the current question.

    Call this only when cross-conversation context would meaningfully change your
    answer. The user will be asked to confirm before retrieved context is used.
    Results are stored in state — interrupt happens in await_memory_confirm node.
    """
    results = await memory_searcher.search(query, current_conversation_id)
    return {"memory_results": results}


# src/app/agents/chatbot/nodes.py
from langgraph.types import interrupt
from langchain_core.messages import SystemMessage

async def await_memory_confirm(state: ChatbotState) -> dict:
    results = state.get("memory_results")
    if not results:
        return {}

    confirmed = interrupt({
        "type": "memory_confirm",
        "results": results,
        "prompt": "I found relevant context from past conversations. Use it?",
    })

    if confirmed:
        context = format_memory_results(results)
        return {
            "messages": [SystemMessage(content=f"## Past Context\n\n{context}")],
            "memory_results": [],
            "memory_confirmed": True,
        }
    return {"memory_results": [], "memory_confirmed": False}
```

### SSE event for frontend

```
event: memory_confirm
data: {"results": [...], "prompt": "I found relevant context from past conversations. Use it?"}
```

## Dependencies

### Python (pyproject.toml)

```toml
chromadb = ">=0.5"
tiktoken = ">=0.7"
langgraph-checkpoint-sqlite = ">=2.0"
```

### TypeScript (package.json)

No new dependencies.

## Resolved Questions

1. **Embedding latency on critical path** — resolved: use FastAPI `BackgroundTasks` in route
   handlers to decouple indexing from the response path. No standard fire-and-forget pattern
   exists in ChromaDB itself; background tasks are the accepted approach (decision 12).
1. **Checkpointing required for interrupt/resume** — resolved: confirmed by LangGraph docs.
   `AsyncSqliteSaver` added as Phase 0 prerequisite (decision 11).
1. **Tool-level vs node-level HITL** — resolved: node-level preferred; tool-level has a
   double-execution bug on resume. `await_memory_confirm` node added to Phase 3 (decision 9).
1. **RAG strategy** — resolved: hybrid. `search_knowledge` always retrieves (no agent gate);
   `search_memory` is agent-decided (model calls it only when cross-conversation context
   is judged relevant). Aligns with 2026 production pattern (decision 13).

## Open Questions

1. **ChromaDB concurrency**: embedded mode has write serialization under multi-worker FastAPI.
   If `uvicorn --workers > 1`, each worker gets its own client pointing at the same path —
   this may cause corruption. Evaluate before production deploy; ChromaDB server mode resolves it.
1. **Stale chunks on edit**: delete-then-reindex must be atomic enough under the current UoW
   pattern. Confirm ChromaDB delete by `file_id` metadata filter completes before re-index starts.

## Changelog

| Date       | Author         | Change                                                                                                                                                                                                                 |
| ---------- | -------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-04-11 | Jonas + Claude | Initial draft                                                                                                                                                                                                          |
| 2026-04-11 | Claude         | Architecture review: added Phase 0 (checkpointing), node-level HITL pattern, hybrid RAG strategy, BackgroundTasks for indexing, resolved 3 open questions                                                              |
| 2026-04-11 | Jonas + Claude | Added decisions 14-15: LLM-enriched metadata as primary indexable content (Multi-Vector pattern), scope fallback for conversation search. Updated Phase 1 indexer/searcher tasks. Added LLM JSON parse fix to Phase 2. |
