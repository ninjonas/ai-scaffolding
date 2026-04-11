---
name: create-doc
description: Create paired functional + technical documentation under docs/functional/ and docs/technical/ following project conventions. Use when asked to add feature docs, capability docs, paired PM/engineering docs, or documentation that matches the NNN-topic paired set pattern.
argument-hint: "<topic-slug>"
---

# Create paired documentation

Produces a matching pair of documents: an executive functional summary and a detailed technical companion, per `.claude/rules/documents.md`.

## When to use

- The user wants **paired** documentation for a feature or capability (`docs/functional/` + `docs/technical/`, same `NNN-topic.md` basename).
- New docs must follow the project’s **numeric prefix** convention and link across folders via **Paired With**.
- Prefer this skill over ad-hoc markdown when the output should match PM/manager/architect vs architect/engineer audiences.

## Workflow

### Step 1: Determine the next `NNN` number

1. List numeric prefixes from **both** `docs/functional/` and `docs/technical/` (e.g. filenames like `001-auth.md`, `042-payments.md`).
2. Parse the leading three-digit number from each matching file.
3. Set `NNN` to the next unused integer, zero-padded to three digits (e.g. if the highest existing is `002`, use `003`). If either folder is missing or empty, treat its max as `0`.
4. Choose a **topic slug** (kebab-case, stable basename) — often from the user’s `argument-hint` or feature name — so the pair is `NNN-topic-slug.md`.

### Step 2: Gather context

- Read relevant **source code**, **OpenAPI** or config, and any **`docs/plans/`** entries that define the feature.
- If the user supplied a spec or ticket, align terminology and scope with it.
- Decide what belongs in the **user-visible flow** (functional) vs **components, sequences, config, files** (technical).

### Step 3: Create `docs/functional/NNN-topic.md`

- Use the **Functional doc template** below.
- Fill **Overview** in plain language; architecture terms OK, **no code**.
- **System Flow**: exactly **one** Mermaid flowchart — user-visible flow only (see `.claude/rules/diagrams.md`).
- Set **Status**, **Date**, and **Paired With** linking to the technical file (`../technical/NNN-topic.md`).

### Step 4: Create `docs/technical/NNN-topic.md`

- Use the **Technical doc template** below.
- **Overview** may reference code or concrete artifacts.
- **Component View**: Mermaid flowchart of system components.
- **Request Flow**: Mermaid `sequenceDiagram`.
- **Key Patterns**: code samples only where non-obvious; **Configuration Reference** and **Source Files** as tables.
- Set **Paired With** linking to the functional file (`../functional/NNN-topic.md`).

### Step 5: Verify pairing

- Both files share the same title (`# <Feature Title>`), same basename (`NNN-topic.md`), and reciprocal **`Paired With`** markdown links.
- All diagrams are **Mermaid** fenced blocks (no Draw.io, Lucidchart, or PlantUML); follow `.claude/rules/diagrams.md` for diagram choice and scope.

---

## Functional doc template

Copy this structure into `docs/functional/NNN-topic.md` and replace placeholders:

```markdown
# <Feature Title>

**Audience**: Product Managers, Managers, Architects
**Status**: Draft | Published
**Date**: YYYY-MM-DD
**Paired With**: [Technical](../technical/NNN-topic.md)

## Overview
One paragraph. Architecture terms OK (API, agent, provider), no code.

## System Flow
One Mermaid flowchart — user-visible flow only.

## What This Enables
3–5 capability bullets.

## Why It Matters
One paragraph on business value.
```

---

## Technical doc template

Copy this structure into `docs/technical/NNN-topic.md` and replace placeholders:

```markdown
# <Feature Title>

**Audience**: Architects, Engineers
**Status**: Draft | Published
**Date**: YYYY-MM-DD
**Paired With**: [Functional](../functional/NNN-topic.md)

## Overview
One paragraph. Code references OK.

## Component View
Mermaid flowchart of system components.

## Request Flow
Mermaid sequenceDiagram.

## Key Patterns
Code examples for non-obvious patterns only.

## Configuration Reference
Variable table.

## Source Files
File → purpose table.
```

---

## Diagrams

All diagrams use **Mermaid** (see `.claude/rules/diagrams.md`): fenced code blocks with the `mermaid` language tag; functional docs use one high-level user flowchart; technical docs include at minimum a component flowchart and a sequence diagram.
