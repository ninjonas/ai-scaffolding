---
name: code-review
description: "Hybrid code review: runs automated checks on changed files, then delegates semantic review to Codex CLI for architectural violations scripts can't catch."
allowed-tools: Bash(just *) Bash(git *) Bash(gh *) Bash(codex *) Read Glob Grep
---

# Code Review

Hybrid review: automated script checks first (fast, zero false positives), then Codex semantic
pass (architecture violations scripts can't detect).

---

## Step 1 — Determine scope

Get the current branch and its merge-base with main:

```bash
branch=$(git branch --show-current)
ref=$(git merge-base main HEAD)
```

Collect all files touched since branching off main, plus anything staged or unstaged:

```bash
git diff --name-only --diff-filter=d "$ref" -- src/
git diff --name-only --diff-filter=d -- src/
git diff --cached --name-only --diff-filter=d -- src/
```

Deduplicate and split into:
- **Python files** — `*.py` under `src/` (exclude `scripts/`)
- **TypeScript/TSX files** — `*.ts`, `*.tsx`

---

## Step 2 — Script pass (automated checks)

Run the automated checks against changed files only:

```bash
just -f scripts/review.just code "$ref"
```

This runs lint (Python + TypeScript), line limits, DI checks, literal strings, mapper patterns,
and service patterns — all scoped to changed files. Capture the full output.

### Filter findings to changed lines

Build a changed-line map from the diff:

```bash
git diff "$ref"...HEAD --unified=0 -- <file> | grep "^@@"
```

Parse `@@ +N,M @@` hunk headers to build a set of changed line numbers per file:
- `+N` → line N (1 line)
- `+N,M` → lines N through N+M−1 (skip when M=0, pure deletion)

A script finding is **in scope** if its `file:line` falls within any changed range.
Findings outside all changed ranges are **pre-existing** — suppress them but count them.

---

## Step 3 — Semantic pass (Codex review)

### Build review instructions

Read all project rules to build the instruction set for Codex:

```bash
cat .claude/rules/architecture.md \
    .claude/rules/code-conventions.md \
    .claude/rules/agent-conventions.md \
    .claude/rules/logging.md \
    .claude/rules/logging-enforcement.md \
    .claude/rules/project-structure.md \
    .claude/rules/conventions.md
```

### Run Codex review

Pass the project rules as custom instructions to `codex review`:

```bash
codex review \
  --base "$ref" \
  "Review against these project rules. Flag only clear violations, not style opinions.

RULES:
<paste concatenated rules here>

Focus on:
- SOLID / DDD layer violations (domain leaking infrastructure, wrong abstractions)
- Dependency injection violations the regex checker misses
- Missing or incorrect structured logging (structlog for Python, pino for TypeScript)
- Agent convention violations (wrong folder, direct LLM instantiation, prompt assembly)
- Blocking I/O in async functions
- Missing error context in exception handling
- Structural duplication across files"
```

If the diff is large (50+ files), chunk the review into batches of ~10 files by passing
specific file paths after the prompt.

---

## Step 4 — Report

Combine both passes into a structured report:

```markdown
## Code Review — <branch> vs <ref> (<date>)

### Files reviewed
- <list of files>

---

### Script findings

#### ✅ Passed
- <checker>: <file> — no issues

#### ❌ Violations
- <checker>: <file>:<line> — <message>

#### ℹ️ Pre-existing violations suppressed
⚠️ N pre-existing violation(s) suppressed — present in files touched by this branch but on
lines not introduced here. Run `just check` on the full file to see them.
(omit this section entirely if nothing was suppressed)

---

### Semantic findings (Codex)

#### ❌ Violations
- <file>:<line> — [rule name] <description>

#### ⚠️ Questions
- <file>:<line> — <uncertain observation>

#### ⚡ Suggestions
- <file>:<line> — <performance or improvement suggestion>

#### ✅ No architectural violations found
(if clean)

---

### Summary
<N> script violations · <M> semantic violations · <K> questions · <P> pre-existing suppressed
```

If everything is clean, say so clearly — a clean review is a useful signal.

---

## Step 5 — Post to PR (if open)

Check whether the current branch has an open PR:

```bash
gh pr view --json number,headRefOid,url 2>/dev/null
```

If a PR exists, do **both**:

### 5a — Inline review comments for violations

For every violation (script **and** semantic) with a resolvable `file:line`, post as inline
review comments:

```bash
gh api repos/<owner>/<repo>/pulls/<number>/reviews \
  --method POST \
  --field commit_id="<headRefOid>" \
  --field event="COMMENT" \
  --field body="Code review — see inline comments for violations." \
  --field 'comments=[
    {
      "path": "src/app/foo.py",
      "line": 42,
      "side": "RIGHT",
      "body": "**[check-strings]** String literal hardcoded inline — extract to constants."
    }
  ]'
```

Inline comment format:
- Script: `**[<checker-name>]** <message>`
- Semantic: `**[codex · <rule-name>]** <description>`

### 5b — Summary PR comment

```bash
gh pr comment <number> --body "<full markdown report>"
```

Rules:
- Always do both 5a and 5b when a PR is open
- If `gh pr view` fails (no PR), skip silently
- If no violations, skip 5a — only post the summary
