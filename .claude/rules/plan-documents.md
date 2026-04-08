## Plan Documents

Plans live in `docs/plans/` with numeric prefix: `001-name.md`, `002-name.md`.

### Required sections

```markdown
# Plan: <Title>

**Status**: Draft | Approved | In Progress | Done
**Date**: YYYY-MM-DD
**Author**: <who>

## Overview
One paragraph — what and why.

## Decisions Made
| # | Decision | Choice |
Table of choices made during planning (captures the Q&A).

## Target Folder Structure
Tree view of new/changed files.

## Implementation Phases
Numbered phases, each with numbered steps.
Keep phases small enough to review independently.

## <Pattern/Architecture sections>
Code examples showing key patterns (DTOs, mappers, etc.).
Only include patterns that are new or non-obvious.

## Dependencies
What gets added to pyproject.toml / package.json.

## Open Questions / Resolved Questions
Track what's undecided and what got resolved.
```

### Rules

- The decisions table is mandatory — it captures context that code alone cannot
- Phases should map to reviewable units of work (one PR per phase is ideal)
- Code examples in plans are illustrative, not copy-paste — the implementation may differ
- Update the status field as work progresses
