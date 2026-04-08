#!/bin/bash
# Block pip/npm — this project uses uv and pnpm exclusively.

COMMAND=$(jq -r '.tool_input.command' < /dev/stdin)

if echo "$COMMAND" | grep -qE '(^|\s|&&|\|)(pip|pip3)\s+install'; then
  echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Use uv, not pip. Run: uv add <package>"}}'
  exit 0
fi

if echo "$COMMAND" | grep -qE '(^|\s|&&|\|)npm\s+install'; then
  echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Use pnpm, not npm. Run: pnpm add <package>"}}'
  exit 0
fi

if echo "$COMMAND" | grep -qE '(^|\s|&&|\|)yarn\s+(add|install)'; then
  echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Use pnpm, not yarn. Run: pnpm add <package>"}}'
  exit 0
fi

if echo "$COMMAND" | grep -qE '(^|\s|&&|\|)poetry\s+(add|install)'; then
  echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Use uv, not poetry. Run: uv add <package>"}}'
  exit 0
fi

exit 0
