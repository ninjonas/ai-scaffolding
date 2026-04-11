#!/bin/bash
# Compact emoji status line for Claude Code with oh-my-zsh theme colors

# ANSI color codes (using $'...' for real escape chars)
ORANGE=$'\033[38;5;214m'
CYAN=$'\033[38;5;51m'
GREEN=$'\033[38;5;46m'
RED=$'\033[38;5;196m'
RESET=$'\033[0m'

# Git branch
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
BRANCH_DISPLAY=""
if [ -n "$BRANCH" ] && [ "$BRANCH" != "HEAD" ]; then
  BRANCH_DISPLAY="${ORANGE}▿${RESET} $BRANCH"
fi

# Git status
GIT_STATUS=""
if [ -n "$BRANCH" ]; then
  if git diff --quiet 2>/dev/null && git diff --cached --quiet 2>/dev/null; then
    GIT_STATUS="${GREEN}•${RESET}"
  else
    GIT_STATUS="${RED}•${RESET}"
  fi
fi

# Model (abbreviated)
MODEL="${CLAUDE_CODE_MODEL:-haiku}"
MODEL_SHORT=$(echo "$MODEL" | sed 's/claude-//' | sed 's/-.*$//')
MODEL_DISPLAY="${CYAN}⚙${RESET} $MODEL_SHORT"

# Build status line
if [ -n "$BRANCH_DISPLAY" ]; then
  printf "%b %b %b\n" "$BRANCH_DISPLAY" "$GIT_STATUS" "$MODEL_DISPLAY"
else
  printf "%b\n" "$MODEL_DISPLAY"
fi
