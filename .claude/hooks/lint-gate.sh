#!/bin/bash
# Run linters before Claude stops. If lint fails, tell Claude to fix it.

cd "$CLAUDE_PROJECT_DIR" || exit 0

OUTPUT=$(just lint 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
  echo "$OUTPUT" >&2
  exit 2
fi

exit 0
