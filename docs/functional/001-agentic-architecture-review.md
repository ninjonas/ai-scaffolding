# Agentic Architecture Review

**Status:** Published
**Date:** 2026-04-11
**Author:** Claude (research review)
**Paired With:** [Technical: 001-agentic-architecture-review](../technical/001-agentic-architecture-review.md)

## Overview

This document summarizes an architecture review of the scaffolding project's LangGraph-based multi-agent system. The review compares the current implementation against production-grade patterns documented in LangGraph/LangSmith official guidance, reputable open-source references, and enterprise deployment patterns. It identifies what the project does well, where gaps exist, and what alternatives are worth considering.

## Current Architecture

The system runs three agents orchestrated by a supervisor:

- **Supervisor**: routes user messages to either chatbot or researcher based on intent
- **Chatbot**: general-purpose assistant with tool-calling loop (file ops, calculator, web search, skills, knowledge base)
- **Researcher**: focused research agent with web search capability

Supporting infrastructure includes a knowledge base (file upload, LLM-enriched metadata, catalog injection into prompts), an orchestrator/broker layer abstracting agent invocation from services, and a skill system for progressive capability loading.

## Strengths

The project follows several patterns that align with official LangGraph recommendations: supervisor-based routing with subgraph composition, `MessagesState` subclassing, partial dict returns from nodes, separated node responsibilities (routing vs LLM vs tools), and a clean service layer with DI. The knowledge base feature with LLM-powered frontmatter enrichment is a solid foundation for context management.

## Key Gaps

| Gap                                           | Impact                                                                    | Effort |
| --------------------------------------------- | ------------------------------------------------------------------------- | ------ |
| No LangGraph checkpointing                    | No conversation memory, no resume-after-failure, no time-travel debugging | Medium |
| Knowledge base uses prompt injection, not RAG | Catalog size is capped by context window; no semantic search              | High   |
| No tool error handling on ToolNode            | Tool failures crash the graph instead of letting the LLM recover          | Low    |
| No agent loop safety (max_steps)              | Runaway tool-calling loops possible                                       | Low    |
| No streaming support                          | Users wait for full response before seeing output                         | Medium |
| No LangSmith tracing                          | Limited production observability beyond structlog                         | Low    |
| Mock web search                               | Researcher agent has no real search capability                            | Medium |
| No human-in-the-loop patterns                 | No approval workflows for sensitive operations                            | Medium |

## Recommendations (Priority Order)

1. **Add checkpointing** with `SqliteSaver` (dev) and `PostgresSaver` (production) for conversation persistence and fault recovery ([LangGraph Persistence Concepts](https://langchain-ai.github.io/langgraph/concepts/persistence/))
1. **Enable `handle_tool_errors=True`** on all ToolNode instances and add `max_steps` to agent states ([ToolNode API Reference](https://langchain-ai.github.io/langgraph/reference/prebuilt/), [Recursion Limit How-To](https://langchain-ai.github.io/langgraph/how-tos/recursion-limit/))
1. **Integrate LangSmith tracing** for production observability alongside structlog ([LangSmith Observability](https://docs.smith.langchain.com/observability), [Tracing LangGraph](https://docs.smith.langchain.com/observability/how_to_guides/trace_with_langgraph))
1. **Implement RAG** for the knowledge base using vector store retrieval instead of full catalog prompt injection ([RAG vs Long Context Tradeoffs](https://redis.io/blog/rag-vs-large-context-window-ai-apps/), [Adaptive RAG Tutorial](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_adaptive_rag/))
1. **Add streaming** via LangGraph's built-in stream modes for real-time user feedback ([LangGraph Streaming Concepts](https://langchain-ai.github.io/langgraph/cloud/concepts/streaming/))
1. **Replace mock web search** with a real provider (Tavily, SerpAPI, or Brave Search) ([Tavily + LangChain Integration](https://python.langchain.com/docs/integrations/tools/tavily_search/))

## Decision Points

These recommendations surface several decisions that need stakeholder input before implementation:

- SQLite vs PostgreSQL for checkpointing (depends on deployment target)
- Which vector store for RAG (ChromaDB for simplicity, PGVector for consolidation)
- Whether to add LangSmith (cost/privacy trade-off vs self-hosted observability)
- Streaming protocol (SSE vs WebSocket, depends on frontend architecture)

## Key References

- [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) (Anthropic): workflow vs agent tradeoffs, prompt chaining, routing, orchestrator-worker patterns
- [LangGraph Persistence](https://langchain-ai.github.io/langgraph/concepts/persistence/): checkpointing, thread-based state, fault recovery
- [LangGraph Multi-Agent Concepts](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/hierarchical_agent_teams/): supervisor and hierarchical patterns
- [LangSmith Observability](https://docs.smith.langchain.com/observability): tracing, evaluation, production monitoring
- [Adaptive RAG with LangGraph](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_adaptive_rag/): query-routed retrieval with self-correction
