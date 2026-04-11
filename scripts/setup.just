set working-directory := '..'

all: dirs brew python node git-hooks claude-plugins
    @echo "Setup complete."

dirs:
    mkdir -p data logs

brew:
    brew install uv node pnpm gh codex

python:
    uv sync --extra dev

node:
    cd src/web && pnpm install

# Install Claude Code plugins from .claude/settings.json (skips already-installed)
claude-plugins:
    #!/bin/bash
    set -euo pipefail
    if ! command -v claude &>/dev/null; then
        echo "ℹ️  claude CLI not found, skipping plugin install."
        exit 0
    fi
    plugins=$(jq -r '.enabledPlugins // {} | keys[]' .claude/settings.json)
    if [ -z "$plugins" ]; then
        echo "ℹ️  No plugins in .claude/settings.json, skipping."
        exit 0
    fi
    echo "Installing Claude Code plugins..."
    while IFS= read -r plugin; do
        echo "  → $plugin"
        claude plugin install "$plugin" 2>/dev/null || true
    done <<< "$plugins"
    echo "✓ Claude Code plugins configured."

# Install git pre-commit and pre-push hooks (skips if already present)
git-hooks:
    #!/bin/bash
    set -euo pipefail
    HOOKS_DIR=".git/hooks"

    # Pre-commit hook
    HOOK="$HOOKS_DIR/pre-commit"
    if [ -f "$HOOK" ] && grep -q "just git-pre-commit" "$HOOK"; then
        echo "ℹ️  pre-commit hook already installed, skipping."
    else
        cat > "$HOOK" << 'HOOKEOF'
    #!/bin/bash
    just git-pre-commit
    HOOKEOF
        chmod +x "$HOOK"
        echo "✓ Installed pre-commit hook."
    fi

    # Pre-push hook
    HOOK="$HOOKS_DIR/pre-push"
    if [ -f "$HOOK" ] && grep -q "just git-pre-push" "$HOOK"; then
        echo "ℹ️  pre-push hook already installed, skipping."
    else
        cat > "$HOOK" << 'HOOKEOF'
    #!/bin/bash
    just git-pre-push
    HOOKEOF
        chmod +x "$HOOK"
        echo "✓ Installed pre-push hook."
    fi
