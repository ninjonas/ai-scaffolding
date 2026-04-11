# Plan: Streaming LLM Responses

**Status**: Draft
**Date**: 2026-04-11
**Author**: Jonas + Claude

## Overview

Add Server-Sent Events (SSE) streaming to the chat API so users see LLM tokens as they generate instead of waiting for the full response. The chatbot response is the primary target (3-8s end-to-end latency today, ~500ms to first token with streaming). Streaming is additive: existing request-response endpoints remain untouched. A new streaming rule and skill enforce the pattern for all future agentic API work, so every new agent capability goes through a stream-or-not decision gate.

## Decisions Made

| #   | Decision                   | Choice                                                                                                                                                       |
| --- | -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | Transport                  | SSE via `sse-starlette` (`EventSourceResponse`). Unidirectional, proxy-friendly, auto-reconnect. WebSocket rejected as unnecessary complexity.               |
| 2   | LangGraph streaming API    | `astream_events(version="v2")` on compiled graph. Provides typed events with `langgraph_node` metadata for filtering.                                        |
| 3   | Event filtering            | Server-side only. Forward `on_chat_model_stream` from the responding agent node. Suppress supervisor routing, tool arguments, and internal chain-of-thought. |
| 4   | SSE event types            | `token` (text chunk), `tool_status` (tool name + start/end), `interrupt` (HITL pause), `error` (structured), `done` (clean termination).                     |
| 5   | Frontend streaming client  | `fetch()` + `ReadableStream.getReader()`. Not `EventSource` (lacks auth header support). Use `@microsoft/fetch-event-source` or manual SSE parser.           |
| 6   | Token buffering (frontend) | Accumulate in `useRef`, flush to React state on `requestAnimationFrame` to avoid per-token re-renders.                                                       |
| 7   | Message persistence        | Deferred until `done` event. Accumulate full response server-side, save to DB after stream completes. Message indexing fires as BackgroundTask after save.   |
| 8   | Interrupt mid-stream       | Stream stops cleanly at interrupt point. Client receives `interrupt` event, shows confirmation UI. Resume uses existing `/resume` endpoint (not streamed).   |
| 9   | Existing endpoints         | Unchanged. `POST /api/chat` and `POST /api/chat/{id}/resume` remain request-response. Streaming is a new route alongside them.                               |
| 10  | Streaming decision rule    | New `.claude/rules/streaming.md` and `.claude/skills/streaming/SKILL.md` enforce that every new agentic API capability declares stream-or-not.               |
| 11  | What streams               | Chatbot LLM text (P0), Researcher synthesis (P1), tool status indicators (P1). Everything else: no streaming.                                                |
| 12  | What does NOT stream       | Supervisor routing, calculator, file ops, image analysis, memory confirm interrupt flow, voice transcription.                                                |

## Target Folder Structure

```
src/app/
  agents/
    orchestrator/
      orchestrator.py           # Updated: add stream_with_telemetry() async generator
      broker.py                 # Updated: add chat_response_stream() async generator
      stream_filter.py          # New: filter astream_events by node name + event type
  api/
    routes/
      chat.py                   # Updated: add POST /api/chat/stream SSE route
    dto/
      chat.py                   # Updated: expand ChatStreamChunkDTO with event_type field
  service/
    chat.py                     # Updated: add stream_message() async generator

src/web/src/
  api/
    chat.ts                     # Updated: add sendMessageStream() with SSE reader
    sse.ts                      # New: SSE stream parser utility
  components/
    useChatSend.ts              # Updated: add streaming state management (useRef + rAF flush)

.claude/
  rules/
    streaming.md                # New: streaming decision rule
  skills/
    streaming/
      SKILL.md                  # New: streaming implementation skill
```

## Implementation Phases

### Phase 1: Streaming rule and skill `Not Started`

Establish the decision framework before writing any streaming code. Every future agentic API capability must pass through this gate.

- [ ] Create `.claude/rules/streaming.md`: defines when to stream (user-facing LLM text generation with >1s latency) vs when not to (sub-second tools, internal routing, blocking HITL flows). Documents SSE event types, interrupt semantics, and the filter-server-side principle.
- [ ] Create `.claude/skills/streaming/SKILL.md`: step-by-step checklist for adding streaming to a new agent capability. Covers orchestrator, broker, service, route, frontend, and testing layers. References the rule for decision criteria.
- [ ] Add `See skill: streaming` pointer in the rule file.

### Phase 2: Orchestrator streaming infrastructure `Not Started`

Add streaming capability to the agent infrastructure layer without changing any existing methods.

- [ ] Add `sse-starlette` to `pyproject.toml` dependencies.
- [ ] Create `src/app/agents/orchestrator/stream_filter.py`: `StreamEventFilter` class. Accepts a set of allowed node names and event types. Exposes `filter(event) -> ChatStreamChunkDTO | None` that maps `astream_events` output to typed SSE chunks. Filters out supervisor routing, tool arguments, and raw metadata. Maps `on_chat_model_stream` to `token` events, `on_tool_start`/`on_tool_end` to `tool_status` events.
- [ ] Add `stream_with_telemetry()` async generator to `AgentOrchestrator`. Calls `self._agent_graph.astream_events(state_dict, version="v2", config=config)`. Yields filtered events via `StreamEventFilter`. Logs start/done/error with timing. Catches `GraphInterrupt` and yields an `interrupt` event before stopping. Yields `done` as final event.
- [ ] Add `chat_response_stream()` async generator to `AgentBroker`. Builds state dict (same as `chat_response()`), delegates to `self._orchestrator.stream_with_telemetry()` with `chat` stream filter config. Yields `ChatStreamChunkDTO` instances.
- [ ] Update `ChatStreamChunkDTO`: add `event_type: str = "token"` field to distinguish `token`, `tool_status`, `interrupt`, `error`, `done` events.

### Phase 3: Service and API layer `Not Started`

Wire streaming through the service and expose an SSE endpoint.

- [ ] Add `stream_message()` async generator to `ChatService`. Handles pre-flight work (get/create conversation, save user message, optimize images, build knowledge context) same as `send_message()`. Then yields chunks from `self._broker.chat_response_stream()`. After stream completes (receives `done`), saves the accumulated assistant message to DB and enqueues message indexing as BackgroundTask.
- [ ] Add `POST /api/chat/stream` route in `chat.py`. Accepts `ChatRequestDTO`. Returns `EventSourceResponse` wrapping an async generator that calls `chat_service.stream_message()` and formats each `ChatStreamChunkDTO` as SSE: `event: {event_type}\ndata: {json}\n\n`. Sets `Cache-Control: no-cache` and `X-Accel-Buffering: no` headers.
- [ ] Handle interrupt mid-stream: when `ChatService.stream_message()` yields an `interrupt` chunk, the SSE stream sends it and terminates. Client uses existing `POST /api/chat/{id}/resume` (non-streaming) to continue.

### Phase 4: Frontend streaming `Not Started`

Add SSE consumption to the React frontend alongside the existing request-response path.

- [ ] Create `src/web/src/api/sse.ts`: utility that takes a `Request` config, calls `fetch()` with streaming, reads the `ReadableStream` via `getReader()`, parses SSE lines (`event:`, `data:`), and yields typed chunk objects. Handles reconnection on network error with exponential backoff (max 3 retries).
- [ ] Add `sendMessageStream()` to `chat.ts`: calls the SSE utility targeting `POST /api/chat/stream`. Returns an `AsyncIterable<ChatStreamChunk>` where each chunk has `eventType`, `content`, `conversationId`, `toolCalls`, `done`.
- [ ] Update `useChatSend.ts`: add `handleSendStream()` that immediately appends a placeholder assistant message with empty content. As `token` chunks arrive, accumulates content in a `useRef<string>` and flushes to `messages` state on `requestAnimationFrame`. On `tool_status` events, shows a status indicator (e.g., "Searching knowledge..."). On `interrupt` event, renders the memory confirm card (existing pattern). On `done`, finalizes the message. On `error`, sets the error state. Keeps `handleSend()` as fallback.
- [ ] Update `ChatMessage` type: add optional `streaming: boolean` flag so the UI can show a cursor/typing indicator on the in-progress message.
- [ ] Switch `handleSend` in `useChatSend` to use `handleSendStream` as the default path. Keep `sendMessage()` (non-streaming) available for fallback.

### Phase 5: Researcher streaming `Not Started`

Extend streaming to the researcher agent's synthesis output.

- [ ] Update `StreamEventFilter` to accept researcher node name in addition to chatbot.
- [ ] Add `research_response_stream()` to `AgentBroker`. Same pattern as `chat_response_stream()` but with researcher filter config.
- [ ] Update supervisor graph streaming: when the supervisor delegates to the researcher, stream the researcher's LLM synthesis tokens. Filter out the web search tool's raw results (only stream the LLM-generated synthesis).
- [ ] Frontend already handles `token` events generically, no changes needed.

### Phase 6: Testing `Not Started`

- [ ] Unit test `StreamEventFilter`: parametrize with various `astream_events` event types, verify correct filtering and mapping.
- [ ] Unit test `AgentOrchestrator.stream_with_telemetry()`: use fake `BaseChatModel` that yields deterministic tokens. Verify event sequence: start log, token events, done event, timing log.
- [ ] Unit test `ChatService.stream_message()`: verify conversation creation, user message save, chunk yielding, and deferred assistant message save after stream completes.
- [ ] Integration test: `POST /api/chat/stream` with httpx `AsyncClient`. Verify SSE format, event types, and `done` termination.
- [ ] Integration test: interrupt mid-stream. Verify stream stops at `interrupt` event, resume via `/resume` returns full response.

## Agent Execution Strategy

### Parallelism map

| Phase | Depends on | Agent type | Notes                                                     |
| ----- | ---------- | ---------- | --------------------------------------------------------- |
| 1     | None       | docs       | Rule + skill only, no code changes                        |
| 2     | None       | backend    | Can run parallel with Phase 1                             |
| 3     | Phase 2    | backend    | Needs orchestrator streaming methods from Phase 2         |
| 4     | Phase 3    | frontend   | Needs SSE endpoint from Phase 3                           |
| 5     | Phase 2    | backend    | Needs stream filter infrastructure, can run after Phase 2 |
| 6     | 3, 4       | testing    | Needs both backend and frontend streaming in place        |

### Sequencing constraints

- Phases 1 and 2 can run in parallel: one is docs, the other is backend infrastructure.
- Phase 3 blocks on Phase 2 (needs `stream_with_telemetry()` and `chat_response_stream()`).
- Phase 4 blocks on Phase 3 (needs the SSE endpoint).
- Phase 5 can start after Phase 2 completes, independent of Phases 3-4.
- Phase 6 blocks on Phases 3 and 4 (needs full stack to test).

### Agent instructions

- **Docs agent (Phase 1)**: Create the streaming rule under `.claude/rules/streaming.md` (under 50 lines per rule-conventions.md). Create the companion skill at `.claude/skills/streaming/SKILL.md`. The rule defines the decision criteria (stream: user-facing LLM text >1s; don't stream: tools \<1s, internal routing, HITL blocking). The skill provides the implementation checklist for adding streaming to a new capability. Reference existing patterns in `service-layer-patterns.md` and `agent-conventions.md`.
- **Backend agent (Phase 2)**: Build streaming infrastructure in the orchestrator layer only. Do not touch routes or services. `stream_with_telemetry()` wraps `astream_events(version="v2")`. `StreamEventFilter` is a pure class with no I/O. Follow existing DI patterns: `AgentOrchestrator` receives the graph via constructor, `AgentBroker` receives the orchestrator. Update `ChatStreamChunkDTO` with `event_type` field.
- **Backend agent (Phase 3)**: Wire streaming through `ChatService.stream_message()` and add the SSE route. The service's pre-flight work (conversation creation, image optimization, knowledge context) runs before streaming starts. The route returns `EventSourceResponse`. Follow existing route patterns in `chat.py`. Do not modify the existing `send_message` endpoint.
- **Frontend agent (Phase 4)**: Add SSE consumption. The SSE parser in `sse.ts` is a pure utility with no React dependency. `sendMessageStream()` in `chat.ts` uses it. State management in `useChatSend.ts` uses `useRef` for accumulation, `requestAnimationFrame` for flushing. Match existing code style (no new dependencies except possibly `@microsoft/fetch-event-source`).
- **Backend agent (Phase 5)**: Extend streaming to the researcher. The `StreamEventFilter` already supports configurable node names. Add the researcher's LLM node to the allowed set. The supervisor graph's streaming should forward researcher tokens when the supervisor routes to it.
- **Testing agent (Phase 6)**: Follow `langgraph-testing.md` conventions. Use fake `BaseChatModel` for unit tests. Node isolation. Parametrize `StreamEventFilter` tests. Integration tests use httpx `AsyncClient` with `stream=True`.

## Key Patterns

### SSE event format

```
event: token
data: {"content": "Hello", "done": false, "conversationId": "abc-123", "eventType": "token"}

event: tool_status
data: {"content": "search_knowledge", "done": false, "conversationId": "abc-123", "eventType": "tool_status"}

event: interrupt
data: {"content": "", "done": false, "conversationId": "abc-123", "eventType": "interrupt", "interrupt": {...}}

event: done
data: {"content": "", "done": true, "conversationId": "abc-123", "eventType": "done"}
```

### Stream filter (server-side)

```python
# src/app/agents/orchestrator/stream_filter.py
from app.api.dto.chat import ChatStreamChunkDTO

STREAM_EVENT_TOKEN = "token"
STREAM_EVENT_TOOL_STATUS = "tool_status"
STREAM_EVENT_DONE = "done"

class StreamEventFilter:
    def __init__(self, allowed_nodes: set[str]) -> None:
        self._allowed_nodes = allowed_nodes

    def filter(self, event: dict) -> ChatStreamChunkDTO | None:
        node = event.get("metadata", {}).get("langgraph_node")
        kind = event.get("event")

        if kind == "on_chat_model_stream" and node in self._allowed_nodes:
            chunk = event["data"]["chunk"]
            return ChatStreamChunkDTO(
                content=chunk.content or "",
                event_type=STREAM_EVENT_TOKEN,
            )

        if kind == "on_tool_start" and node in self._allowed_nodes:
            return ChatStreamChunkDTO(
                content=event["name"],
                event_type=STREAM_EVENT_TOOL_STATUS,
            )

        return None
```

### Orchestrator streaming method

```python
# Added to AgentOrchestrator
async def stream_with_telemetry(
    self,
    operation_name: str,
    state_dict: dict,
    stream_filter: StreamEventFilter,
    config: dict | None = None,
    **log_context: Any,
) -> AsyncGenerator[ChatStreamChunkDTO, None]:
    bound_log = log.bind(**log_context)
    bound_log.info(f"{operation_name}_stream_start")
    start = time.monotonic()

    try:
        async for event in self._agent_graph.astream_events(
            state_dict, version="v2", config=config
        ):
            chunk = stream_filter.filter(event)
            if chunk:
                yield chunk
    except GraphInterrupt as exc:
        interrupt_data = exc.args[0][0] if exc.args and exc.args[0] else {}
        yield ChatStreamChunkDTO(event_type="interrupt", interrupt=interrupt_data)
    except Exception as exc:
        bound_log.error(f"{operation_name}_stream_error", error=str(exc))
        yield ChatStreamChunkDTO(event_type="error", content=str(exc))
        raise
    finally:
        duration_s = time.monotonic() - start
        bound_log.info(f"{operation_name}_stream_done", duration_s=round(duration_s, 3))
        yield ChatStreamChunkDTO(event_type="done", done=True)
```

### Frontend SSE consumption

```typescript
// src/web/src/api/sse.ts
export interface SSEChunk {
  eventType: string;
  content: string;
  conversationId: string;
  done: boolean;
  toolCalls?: ToolCall[];
  interrupt?: MemoryConfirmInterrupt;
}

export async function* streamSSE(url: string, body: object): AsyncGenerator<SSEChunk> {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    let currentEvent = '';
    for (const line of lines) {
      if (line.startsWith('event: ')) currentEvent = line.slice(7);
      else if (line.startsWith('data: ') && currentEvent) {
        yield JSON.parse(line.slice(6));
        currentEvent = '';
      }
    }
  }
}
```

## Dependencies

### Python (pyproject.toml)

```toml
sse-starlette = ">=2.0"
```

### TypeScript (package.json)

No required additions. Optional: `@microsoft/fetch-event-source` if manual SSE parsing proves insufficient.

## Resolved Questions

1. **SSE vs WebSocket**: SSE chosen. LLM streaming is unidirectional (server-to-client). SSE auto-reconnects, works through CDNs/proxies, and is simpler. WebSocket adds bidirectional complexity with no benefit here.
1. **Which LangGraph streaming API**: `astream_events(v=2)` over `astream()`. Provides typed events with node metadata, enabling server-side filtering by agent. Required for multi-agent supervisor pattern.
1. **Frontend EventSource vs fetch**: `fetch()` + `getReader()` chosen. Native `EventSource` doesn't support POST requests or custom headers (auth). Manual parsing or `@microsoft/fetch-event-source` handles this.
1. **What to stream**: Only user-facing LLM text generation with >1s latency. Tool calls emit status indicators only (name, not arguments). Internal routing and sub-second operations don't stream.
1. **Interrupt handling**: Stream stops at interrupt, client receives `interrupt` event, shows HITL UI. Resume uses the existing non-streaming `/resume` endpoint. No need to stream the resume response (it's typically fast).
1. **Message persistence timing**: Deferred to stream completion. Full response accumulated server-side, saved to DB after `done`. Message indexing fires as BackgroundTask. Consistent with existing pattern from plan 007.

## Open Questions

1. **`astream_events` compatibility with checkpointer**: Verify that `astream_events(v=2)` works correctly with `AsyncSqliteSaver` checkpointer. The `ainvoke` path is tested, but `astream_events` may interact differently with checkpoint save timing. Test in Phase 2 before building service layer.
1. **Token batching**: Should the server batch multiple tokens into a single SSE event (e.g., every 50ms) to reduce event volume? Or send every token individually? Individual tokens give lowest latency but higher overhead. Benchmark in Phase 3 and decide.
1. **Resume streaming**: Should `POST /api/chat/{id}/resume` also support streaming? Post-interrupt responses are typically short (agent already has context), so the latency gain may not justify the complexity. Revisit after Phase 4 based on real usage.

## Changelog

| Date       | Author         | Change        |
| ---------- | -------------- | ------------- |
| 2026-04-11 | Jonas + Claude | Initial draft |
