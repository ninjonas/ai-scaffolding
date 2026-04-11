## Plan Documents

Plans live in `docs/plans/` with numeric prefix: `001-name.md`, `002-name.md`.

### Required sections

1. **Header**: Title, Status, Date, Author
2. **Overview**: One paragraph, what and why
3. **Decisions Made**: Table of choices made during planning
4. **Target Folder Structure**: Tree view of new/changed files
5. **Implementation Phases**: Numbered phases with status and checkbox tasks
6. **Agent Execution Strategy**: How a supervisor agent should execute this plan
7. **Changelog**: Dated log of all document changes
8. **Dependencies**: Additions to pyproject.toml / package.json
9. **Open Questions / Resolved Questions**

### Phase status

Every phase heading includes a status: `Not Started | In Progress | Done`.
Format: `### Phase 1: Foundation \`Not Started\``

### Task checkboxes

Every task within a phase uses checkbox syntax: `- [ ]` or `- [x]`.

### Agent Execution Strategy

Documents how a supervisor orchestrates this plan: parallelism map, sequencing constraints, per-phase agent instructions.

### Changelog

Records every document change: `| Date | Author | Change |` table.
Entry required for every edit after initial creation.

### Rules

- The decisions table is mandatory
- Phases map to reviewable units of work (one PR per phase)
- Code examples are illustrative, not copy-paste
- Update phase statuses and task checkboxes as work progresses

See skill: plan-documents
