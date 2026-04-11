---
name: plan-documents
description: Create or update plan documents in docs/plans/ with phase statuses, task checkboxes, agent execution strategy, and changelog. Use when creating new plans or updating existing ones.
argument-hint: "<plan-slug>"
---

# Plan Documents

Creates and updates implementation plans following the conventions in `.claude/rules/plan-documents.md`.

## When to use

- Creating a new implementation plan in `docs/plans/`
- Updating an existing plan (phase status, task completion, new phases)
- Converting an older plan to current format

## Workflow

### Step 1: Determine the plan number

1. List existing files in `docs/plans/` and find the highest numeric prefix.
2. Set the next number, zero-padded to three digits.
3. Choose a kebab-case slug from the user's description.

### Step 2: Gather context

- Read relevant source code, config, and existing plans.
- Ask clarifying questions per CLAUDE.md before proceeding.
- Identify which phases can run in parallel vs sequentially for the agent execution strategy.

### Step 3: Write the plan

Use the template below. Every section is required.

### Step 4: On updates

- Update phase statuses (`Not Started` / `In Progress` / `Done`) in the heading.
- Check off completed tasks (`- [ ]` to `- [x]`).
- Add a row to the Changelog table for every edit after initial creation.
- Never remove changelog history.

### Step 5: Verify

- [ ] Every phase has a status in the heading.
- [ ] Every task is a checkbox item.
- [ ] Agent Execution Strategy section exists and describes parallel/sequential orchestration.
- [ ] Changelog section exists (empty table for new plans, populated for updates).
- [ ] Decisions Made table is present.

---

## Plan template

```markdown
# Plan: <Title>

**Status**: Draft | Approved | In Progress | Done
**Date**: YYYY-MM-DD
**Author**: <who>

## Overview

One paragraph: what and why.

## Decisions Made

| # | Decision | Choice |
|---|----------|--------|
| 1 | ...      | ...    |

## Target Folder Structure

\```
tree view of new/changed files
\```

## Implementation Phases

### Phase 1: <Name> `Not Started`

- [ ] First task description
- [ ] Second task description
- [ ] Third task description

### Phase 2: <Name> `Not Started`

- [ ] First task description
- [ ] Second task description

## Agent Execution Strategy

Describes how a supervisor agent should execute this plan with parallel sub-agents.

### Parallelism map

| Phase | Depends on | Agent type | Notes |
|-------|-----------|------------|-------|
| 1     | None      | backend    | Can start immediately |
| 2     | Phase 1   | backend    | Needs entities from Phase 1 |
| 3     | Phase 1   | backend    | Can run parallel with Phase 2 |
| 4     | 2, 3      | fullstack  | Needs service + agent layers |

### Sequencing constraints

- Phases 2 and 3 can run in parallel after Phase 1 completes.
- Phase 4 blocks on both Phase 2 and Phase 3.

### Agent instructions

Brief instructions a supervisor would give each agent for its assigned phase. Include key decisions and patterns to follow, referencing the Decisions Made table and any architecture sections.

## <Pattern/Architecture sections>

Code examples showing key patterns (DTOs, mappers, etc.).
Only include patterns that are new or non-obvious.

## Dependencies

What gets added to pyproject.toml / package.json.

## Open Questions / Resolved Questions

Track what's undecided and what got resolved.

## Changelog

| Date | Author | Change |
|------|--------|--------|
| YYYY-MM-DD | <author> | Initial draft |
```

---

## Phase status values

Use exactly one of these values in backticks after the phase name:

- `` `Not Started` `` : no work has begun
- `` `In Progress` `` : actively being worked on
- `` `Done` `` : all tasks checked off, phase complete

Example: `### Phase 2: API layer \`In Progress\``

---

## Agent Execution Strategy guidance

This section tells a supervisor agent how to break the plan into parallelizable work units. Include:

1. **Parallelism map**: table showing phase dependencies and which agent type handles each.
2. **Sequencing constraints**: prose describing what blocks what and what can run concurrently.
3. **Agent instructions**: brief per-phase instructions a supervisor would delegate to each sub-agent, referencing decisions and patterns from the plan.

The goal is that a supervisor agent can read this section alone and know how to dispatch parallel agents for execution.
