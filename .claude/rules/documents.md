## Documents

### Where documents go

| Type | Location |
| ---- | -------- |
| Plans / design docs | `docs/plans/` |
| Functional docs (PM/Manager/Architect) | `docs/functional/` |
| Technical docs (Architect/Engineer) | `docs/technical/` |
| User-facing docs (MkDocs) | `docs/` |
| ADRs / architecture decisions | `docs/decisions/` |
| Runbooks / how-tos | `docs/guides/` |
| API documentation | Auto-generated from OpenAPI spec |

### Paired documents

Every feature or capability document comes in a **paired set**: one functional, one technical — same filename, different folder.

- `docs/functional/NNN-topic.md` — executive summary for PMs, managers, architects
- `docs/technical/NNN-topic.md` — full detail for architects and engineers

Both files must declare `**Paired With**:` linking to the other.

See skill: create-doc for document templates and creation workflow

### Rules

- Never put documentation in the project root (except `README.md`, `CLAUDE.md`, and `AGENT.md`)
- Plans use numeric prefix: `001-name.md`, `002-name.md`
- Paired docs use the same numeric prefix: `001-topic.md` in both `functional/` and `technical/`
- Plans include a **Status** field: `Draft`, `Approved`, `In Progress`, `Done`
- Paired docs use **Status**: `Draft` or `Published`
- Keep docs close to what they describe — if it's agent-specific, consider `docs/plans/` not inline
- Use Mermaid for all diagrams (see `diagrams.md`)
