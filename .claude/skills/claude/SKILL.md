---
name: claude
description: Run a task via the Claude Code CLI (`claude -p`) in the background and report results back. Use to offload work to a sub-Claude instance while conserving the current session's context.
argument-hint: "<prompt>"
---

# Claude Code CLI Skill

Delegates a task to a headless Claude Code subprocess, waits for completion, then summarizes the result back into the conversation.

## When to use

- The user asks you to run something "in Claude" or "via the claude agent"
- A task would consume excessive context in the current session (long code generation, multi-file refactors)
- You want to parallelize work by having a sub-Claude handle one task while the current session handles another

## How to invoke

### 1. Build the command

```bash
claude -p "<prompt>" --dangerously-skip-permissions --output-format text
```

| Flag | Purpose |
|------|---------|
| `-p` | Non-interactive print mode — required for scripted use |
| `--dangerously-skip-permissions` | Bypass all permission prompts (use in trusted local workspaces only) |
| `--output-format text` | Plain text output — avoids JSON noise in context |

Optional flags to add when relevant:

| Flag | When to add |
|------|-------------|
| `--model <model>` | User specifies a model (e.g. `sonnet`, `opus`, `haiku`, or full ID) |
| `--effort <level>` | Set reasoning effort: `low`, `medium`, `high`, `max` |
| `--continue` | Resume the most recent Claude session in the current directory |
| `--resume[=sessionId]` | Resume a specific previous session |
| `--add-dir <path>` | Grant access to an additional directory |
| `--permission-mode auto` | Auto-approve edits without full bypass (lighter alternative to `--dangerously-skip-permissions`) |
| `--append-system-prompt <prompt>` | Add extra instructions on top of the default system prompt |
| `--agent <agent>` | Use a specific configured agent |

### 2. Run in background, capture output

Use the Bash tool with `run_in_background: true`. Write output to a temp file so you can read it later without flooding context:

```bash
claude -p "<prompt>" --dangerously-skip-permissions --output-format text > /tmp/claude-agent-output.txt 2>&1
```

### 3. Read and report

Once the background task completes, read `/tmp/claude-agent-output.txt` with the Read tool. Then:

- **Summarize** what the Claude agent did (files changed, decisions made, errors encountered)
- **Quote** only the most relevant excerpts — do not dump the full output into the conversation
- **Flag** any errors or unresolved issues that need follow-up

## Context discipline

The entire point of this skill is to save context. Apply these rules strictly:

- Never paste the full raw output into the conversation
- If the output exceeds ~50 lines, summarize by section (what was planned, what was changed, what failed)
- If the task produced file changes, use `git diff --stat` to summarize the scope rather than showing diffs inline

## Example invocations

```bash
# Refactor a file
claude -p "Refactor src/app/shared/llm.py to support a new LLM provider" \
  --dangerously-skip-permissions --output-format text

# Read-only analysis
claude -p "Explain how the skill loader works in src/app/agents/skills/loader.py" \
  --output-format text --permission-mode plan

# Use a specific model with higher effort
claude -p "Add unit tests for GeminiCISChat in src/tests/shared/" \
  --dangerously-skip-permissions --output-format text --model opus --effort high

# Resume previous session
claude -p "Continue the refactor from last time" \
  --dangerously-skip-permissions --output-format text --continue

# Use a specific agent
claude -p "Review this PR for security issues" \
  --dangerously-skip-permissions --output-format text --agent code-review
```
