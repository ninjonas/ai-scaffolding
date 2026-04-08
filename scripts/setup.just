set working-directory := '..'

all: dirs brew python node git-hooks
    @echo "Setup complete."

dirs:
    mkdir -p data logs

brew:
    brew install uv node pnpm gh

python:
    uv sync --extra dev

node:
    cd src/web && pnpm install

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
