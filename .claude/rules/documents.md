## Documents

### Where documents go

| Type | Location |
| ---- | -------- |
| Plans / design docs | `docs/plans/` |
| User-facing docs (MkDocs) | `docs/` |
| ADRs / architecture decisions | `docs/decisions/` |
| Runbooks / how-tos | `docs/guides/` |
| API documentation | Auto-generated from OpenAPI spec |

### Rules

- Never put documentation in the project root (except `README.md` and `CLAUDE.md`)
- Plans use numeric prefix: `001-name.md`, `002-name.md`
- Plans include a **Status** field: `Draft`, `Approved`, `In Progress`, `Done`
- Keep docs close to what they describe — if it's agent-specific, consider `docs/plans/` not inline
