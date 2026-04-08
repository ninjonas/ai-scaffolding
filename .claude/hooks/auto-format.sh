#!/bin/bash
# Auto-format files after Write/Edit.

FILE_PATH=$(jq -r '.tool_input.file_path // empty' < /dev/stdin)

if [ -z "$FILE_PATH" ] || [ ! -f "$FILE_PATH" ]; then
  exit 0
fi

case "$FILE_PATH" in
  *.py)
    ruff check --fix --quiet "$FILE_PATH" 2>/dev/null
    ruff format --quiet "$FILE_PATH" 2>/dev/null
    ;;
  *.ts|*.tsx|*.js|*.jsx|*.json|*.css|*.html)
    npx --yes prettier --write --log-level error "$FILE_PATH" 2>/dev/null
    ;;
esac

exit 0
