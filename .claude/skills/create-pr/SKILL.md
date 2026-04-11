---
name: create-pr
description: Generate GitHub PR titles and descriptions from branch commits. Use when asked to write, create, or generate a PR, pull request, or PR description.
---

# Create PR

Generate a PR title and description from the current branch's commits.

## Workflow

### 1. Gather branch and commit data

```bash
git branch --show-current
git merge-base master HEAD
git log <merge-base>..HEAD --oneline --no-merges --author="<author-email>"
git show <commit> --stat --format=""
```

If the user provides an author email, filter commits with `--author="<email>"`.

### 2. Derive PR title

- Format: short imperative summary (e.g. `feat(api): add GeminiCIS provider`)

### 3. Fill description

Use this template:

```markdown
## Motivation

<!-- What problem does this solve? -->

## Change Overview

<!-- Summarize each commit. Use bullet points. -->

## Validation

<!-- Evidence: unit tests, scripts run locally, agent behavior. Don't invent evidence. -->

<details>
<summary>Integration Test Results</summary>
<!-- Only include this block if the user ran integration tests -->
</details>

## Checklist

- [ ] Tests written?
- [ ] Docs updated?
- [ ] `just check` passes?
```

**Section guidance:**
- **Motivation**: Infer from commits and files changed. State the problem and why.
- **Change Overview**: Summarize commits in order (feat/fix/refactor/docs/chore). Be concise.
- **Validation**: Use placeholder or ask user. Never invent evidence.
- **Integration Tests**: Omit the `<details>` block entirely if user didn't run them.
- **Checklist**: Leave all items unchecked.

### 4. Output

Reply with the PR title (copyable) and full PR description (markdown). Do not create files unless asked.
