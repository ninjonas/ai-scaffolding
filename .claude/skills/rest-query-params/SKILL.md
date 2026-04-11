---
name: rest-query-params
description: FastAPI pattern for conditional query parameter validation — when one param's value makes another required, return 422 with a clear error. Use when adding or reviewing route handlers with dependent query params.
argument-hint: "<route-file>"
---

# REST Query Parameter Validation

Step-by-step pattern for enforcing conditional required query parameters in FastAPI route handlers.

## Workflow

### 1. Identify the dependency

State the rule explicitly before coding:

> If `scope == "conversation"`, then `conversation_id` is required.

This becomes the guard condition and the error message template.

### 2. Place the guard at the top of the handler

The check goes before logging and before any service call:

```python
from fastapi import APIRouter, HTTPException

@router.get("", response_model=list[KnowledgeFileResponseDTO])
async def list_files(
    knowledge_service: KnowledgeServiceDep,
    scope: str | None = None,
    conversation_id: str | None = None,
) -> list[KnowledgeFileResponseDTO]:
    if scope == "conversation" and not conversation_id:
        raise HTTPException(
            status_code=422,
            detail="conversation_id is required when scope=conversation",
        )
    log.info("knowledge_list_request", scope=scope, conversation_id=conversation_id)
    entities = await knowledge_service.list(scope=scope, conversation_id=conversation_id)
    return [KnowledgeFileApiMapper.to_response_dto(e) for e in entities]
```

### 3. Error message format

Always name both the missing parameter and the triggering condition:

| Pattern | Example |
|---|---|
| `"<param> is required when <condition>"` | `"conversation_id is required when scope=conversation"` |

Never use vague messages like `"missing parameter"` or `"invalid request"`.

### 4. Multiple conditional dependencies

When several params depend on each other, stack the guards in order of specificity:

```python
if scope == "conversation" and not conversation_id:
    raise HTTPException(status_code=422, detail="conversation_id is required when scope=conversation")
if scope == "user" and not user_id:
    raise HTTPException(status_code=422, detail="user_id is required when scope=user")
```

### 5. Keep services unaware

The service method signature accepts the validated value directly. It does not re-validate:

```python
# Route validates, then passes clean args
entities = await knowledge_service.list(scope=scope, conversation_id=conversation_id)

# Service trusts its caller — no re-checking
async def list(self, scope: str | None, conversation_id: str | None) -> list[KnowledgeFile]:
    ...
```

### 6. Test coverage

Write a test for each guard condition:

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_list_knowledge_requires_conversation_id_when_scope_conversation(client: AsyncClient):
    response = await client.get("/api/knowledge?scope=conversation")
    assert response.status_code == 422
    assert "conversation_id" in response.json()["detail"]

@pytest.mark.asyncio
async def test_list_knowledge_scope_conversation_with_id_succeeds(client: AsyncClient):
    response = await client.get("/api/knowledge?scope=conversation&conversation_id=abc123")
    assert response.status_code == 200
```

## Related

- Rule: `.claude/rules/rest-query-params.md`
- Real example: `src/app/api/routes/knowledge.py` — `list_files` handler
