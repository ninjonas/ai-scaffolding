#!/bin/bash
# Enforce project conventions:
# 1. Block wrong package managers (pip/npm/yarn/poetry)
# 2. Block direct tool invocations — use just recipes instead
#
# Uses exit code 2 to force-block even when Bash(*) is in the allow list.

COMMAND=$(jq -r '.tool_input.command' < /dev/stdin)

deny() {
  echo "BLOCKED: $1" >&2
  exit 2
}

# --- Package manager enforcement ---

if echo "$COMMAND" | grep -qE '(^|[[:space:]]|&&|\|)(pip|pip3)[[:space:]]+install'; then
  deny "Use uv, not pip. Run: uv add <package>"
fi

if echo "$COMMAND" | grep -qE '(^|[[:space:]]|&&|\|)npm[[:space:]]+install'; then
  deny "Use pnpm, not npm. Run: pnpm add <package>"
fi

if echo "$COMMAND" | grep -qE '(^|[[:space:]]|&&|\|)yarn[[:space:]]+(add|install)'; then
  deny "Use pnpm, not yarn. Run: pnpm add <package>"
fi

if echo "$COMMAND" | grep -qE '(^|[[:space:]]|&&|\|)poetry[[:space:]]+(add|install)'; then
  deny "Use uv, not poetry. Run: uv add <package>"
fi

# --- Just recipe enforcement ---

if echo "$COMMAND" | grep -qE '(^|[[:space:]]|&&|\|)(uv run )?pytest([[:space:]]|$)'; then
  deny "Use just test-py, not pytest directly."
fi

if echo "$COMMAND" | grep -qE '(^|[[:space:]]|&&|\|)pnpm (exec )?vitest([[:space:]]|$)'; then
  deny "Use just test-ts, not vitest directly."
fi

if echo "$COMMAND" | grep -qE '(^|[[:space:]]|&&|\|)(uv run )?ruff (check|format)([[:space:]]|$)'; then
  deny "Use just lint-py or just fmt-py, not ruff directly."
fi

if echo "$COMMAND" | grep -qE '(^|[[:space:]]|&&|\|)pnpm (exec )?eslint([[:space:]]|$)'; then
  deny "Use just lint-ts, not eslint directly."
fi

if echo "$COMMAND" | grep -qE '(^|[[:space:]]|&&|\|)pnpm (exec )?prettier([[:space:]]|$)'; then
  deny "Use just fmt-ts, not prettier directly."
fi

if echo "$COMMAND" | grep -qE '(^|[[:space:]]|&&|\|)(uv run )?mdformat([[:space:]]|$)'; then
  deny "Use just fmt-md or just lint-md, not mdformat directly."
fi

exit 0
