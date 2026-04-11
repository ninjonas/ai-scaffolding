# Plan: LLM-Powered Knowledge Frontmatter

**Status**: In Progress
**Date**: 2026-04-11
**Author**: Jonas + Claude
**Branch**: feat/005-knowledge-base

**Paired With**: N/A (implementation plan only)

## Overview

The heuristic frontmatter generator introduced in Plan 005 produces poor metadata for structured files (JSON/YAML keys as description, generic tags). This plan replaces it with LLM-powered generation using structured output via function calling. The LLM runs as a fire-and-forget background task after upload — the upload response returns immediately with heuristic metadata, and the LLM enrichment patches the record within seconds. An `enriched` flag on each file tracks generation status, and the frontend shows a transient badge while enrichment is pending.

## Decisions Made

| #   | Decision                   | Choice                                                          |
| --- | -------------------------- | --------------------------------------------------------------- |
| 1   | When to run LLM            | Async background task after upload (non-blocking)               |
| 2   | Structured output          | `with_structured_output(Pydantic)` via LangChain                |
| 3   | Fallback on LLM failure    | Keep heuristic result — upload must never fail                  |
| 4   | Job runner                 | FastAPI `BackgroundTasks` — no queue infra needed at this scale |
| 5   | Enrichment status tracking | `enriched: bool` column on `knowledge_files` table              |
| 6   | Re-enrichment              | Allowed — user can trigger from edit panel                      |
| 7   | Frontend polling           | 1x delayed poll after upload (not an interval)                  |
| 8   | LLM injection              | Via DI — never instantiate in service code                      |

## Target Folder Structure

```
src/app/
  agents/
    tools/
      knowledge.py                      # existing — CATALOG_HEADER prompt update
      knowledge_frontmatter_llm.py      # NEW — KnowledgeFrontmatterSchema + llm_generate()
  domain/
    entities/
      knowledge_file.py                 # add enriched: bool field
  infrastructure/
    models/
      knowledge_file.py                 # add enriched column + migration
    mappers/
      knowledge_file.py                 # map enriched field
  service/
    knowledge.py                        # add enrich_metadata(file_id)
    knowledge_frontmatter.py            # existing heuristic — keep as fallback
  api/
    routes/
      knowledge.py                      # fire BackgroundTask on upload
    dtos/
      knowledge.py                      # add enriched field to response DTO

src/web/src/
  api/
    knowledge.ts                        # add enriched to KnowledgeCatalogEntry type
  components/
    KnowledgeFileRow.tsx                # show "enriching..." badge when enriched=false
    useKnowledgeUpload.ts               # 1x delayed poll after upload

src/tests/
  test_knowledge_frontmatter_llm.py     # NEW — unit tests
  test_knowledge_enrich.py              # NEW — service + route tests
```

## Implementation Phases

### Phase 1: LLM Frontmatter Service `In Progress`

- [ ] Create `src/app/agents/tools/knowledge_frontmatter_llm.py`
  - `KnowledgeFrontmatterSchema(BaseModel)`: `name: str`, `description: str`, `tags: list[str]`
  - `llm_generate(content: str, file_type: str, llm: BaseChatModel) -> tuple[str, str, list[str]]`
  - Use `llm.with_structured_output(KnowledgeFrontmatterSchema)`
  - Prompt: file content + file_type, constrain to 1 sentence description, 3–8 lowercase kebab-case tags
  - On any exception: log warning, return `("", "", [])` so caller falls back to heuristic
- [ ] Add `enriched: bool = False` to `KnowledgeFile` domain entity
- [ ] Add `enriched` column (boolean, default False) to `KnowledgeFileModel`
- [ ] Update `KnowledgeFileDataMapper` to map `enriched` field
- [ ] Add `enriched` field to response DTOs and `KnowledgeFileApiMapper`
- [ ] Add `enrich_metadata(file_id: str) -> None` to `KnowledgeService`
  - Fetch file by id
  - Call `llm_generate(file.content, file.file_type, self._llm)`
  - If result non-empty: call `update(file_id, name=..., description=..., tags=...)` + set `enriched=True`
  - If LLM fails: log error, set `enriched=True` anyway (heuristic result stands, no retry loop)
- [ ] Inject `llm: BaseChatModel` into `KnowledgeService` via DI
- [ ] Fire `enrich_metadata` as `BackgroundTasks` task in upload route

### Phase 2: Frontend Enrichment Badge `Not Started`

- [ ] Add `enriched: boolean` to `KnowledgeCatalogEntry` type in `src/web/src/api/knowledge.ts`
- [ ] Show subtle "enriching..." badge in `KnowledgeFileRow` when `enriched === false`
- [ ] In `useKnowledgeUpload`: after successful upload, schedule 1x delayed poll (3s) to refresh catalog
- [ ] Badge disappears once catalog refresh returns `enriched: true`

### Phase 3: Tests `Not Started`

- [ ] `test_knowledge_frontmatter_llm.py`
  - `llm_generate` returns correct tuple from structured output
  - `llm_generate` returns empty tuple on LLM exception (fallback path)
  - Schema validates description is a string, tags is a list
- [ ] `test_knowledge_enrich.py`
  - `enrich_metadata` patches name/description/tags and sets `enriched=True`
  - `enrich_metadata` sets `enriched=True` even when LLM fails (heuristic preserved)
  - Upload route fires background task (check `BackgroundTasks.add_task` called)

### Phase 4: Review `Not Started`

- [ ] Reviewer checks all output against `.claude/rules/`

## Agent Execution Strategy

```
Wave 1 (parallel where possible):
  graphs  — knowledge_frontmatter_llm.py (new LLM module)
  database — entity + model + mapper (enriched field)
  api      — KnowledgeService.enrich_metadata + upload route + DTOs + DI wiring

  Sequencing constraint:
    database writes domain entity first (enriched field)
    api picks up updated entity

Wave 2:
  ui — frontend badge + poll logic

Wave 3:
  test — test_knowledge_frontmatter_llm.py + test_knowledge_enrich.py

Wave 4:
  reviewer — all changed files
```

## Dependencies

No new packages required. Uses existing:

- `langchain-core` — `BaseChatModel`, `with_structured_output`
- `pydantic` — `BaseModel` for schema
- `fastapi` — `BackgroundTasks`

## Open Questions

| #   | Question                                                                                           | Status |
| --- | -------------------------------------------------------------------------------------------------- | ------ |
| 1   | Should re-enrichment be triggered manually (edit panel button) or automatically on content update? | Open   |
| 2   | Should we cap LLM enrichment to files under a size threshold (e.g. 10KB)?                          | Open   |
| 3   | Should enrichment run for conversation-scoped files too, or only project-scoped?                   | Open   |

## Changelog

| Date       | Author         | Change        |
| ---------- | -------------- | ------------- |
| 2026-04-11 | Jonas + Claude | Initial draft |
