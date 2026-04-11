## REST Query Parameter Validation

### Conditional required parameters

When a query parameter's value implies another parameter is required, the API must enforce it explicitly:

- Return `422 Unprocessable Entity` with a descriptive error message
- Never silently ignore the missing parameter or return unfiltered data
- Document the dependency: if param `A` has value `X`, param `B` is required

### Validation location

Validate conditional query parameters in the **route handler**, not the service layer.

- Routes own input contract enforcement
- Services assume valid, complete input
- This keeps service signatures clean and avoids domain-layer leakage of HTTP concerns

### Implementation

Use `HTTPException(status_code=422)` from FastAPI:

```python
if scope == "conversation" and not conversation_id:
    raise HTTPException(
        status_code=422,
        detail="conversation_id is required when scope=conversation",
    )
```

Place the guard at the top of the handler, before any logging or service calls.

### Error message format

Messages must name both the required parameter and the condition that triggers it:

- Good: `"conversation_id is required when scope=conversation"`
- Bad: `"missing parameter"`, `"invalid request"`

See skill: rest-query-params
