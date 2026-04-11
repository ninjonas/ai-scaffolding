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

1. **Add checkpointing** with `SqliteSaver` (dev) and `PostgresSaver` (production) for conversation persistence and fault recovery
1. **Enable `handle_tool_errors=True`** on all ToolNode instances and add `max_steps` to agent states
1. **Integrate LangSmith tracing** for production observability alongside structlog
1. **Implement RAG** for the knowledge base using vector store retrieval instead of full catalog prompt injection
1. **Add streaming** via LangGraph's built-in stream modes for real-time user feedback
1. **Replace mock web search** with a real provider (Tavily, SerpAPI, or Brave Search)

## Decision Points

These recommendations surface several decisions that need stakeholder input before implementation:

- SQLite vs PostgreSQL for checkpointing (depends on deployment target)
- Which vector store for RAG (ChromaDB for simplicity, PGVector for consolidation)
- Whether to add LangSmith (cost/privacy trade-off vs self-hosted observability)
- Streaming protocol (SSE vs WebSocket, depends on frontend architecture)
