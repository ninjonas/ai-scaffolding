set working-directory := '..'
set quiet

all: dirs brew python node git-hooks claude-cli claude-plugins
    @echo ""
    @echo "✅ Setup complete."

dirs:
    @echo "── Project ──"
    @echo "📁 Creating directories..."
    @mkdir -p data logs
    @if [ -f .env ]; then echo "📄 .env already exists, skipping."; else cp .env.example .env && echo "📄 Created .env from .env.example"; fi

brew:
    @echo ""
    @echo "── Dependencies ──"
    @echo "🍺 Installing Homebrew packages..."
    @brew install uv node pnpm gh codex 2>&1 | grep -vE "^(Warning:|To reinstall|  brew reinstall|Not upgrading|✔︎|$)" || true

python:
    @echo "🐍 Installing Python dependencies..."
    @uv sync --extra dev --quiet

node:
    @echo "📦 Installing Node dependencies..."
    @cd src/web && pnpm install 1>/dev/null

# Install git pre-commit and pre-push hooks (skips if already present)
git-hooks:
    #!/bin/bash
    set -euo pipefail
    echo ""
    echo "── Git ──"
    HOOKS_DIR=".git/hooks"

    # Pre-commit hook
    HOOK="$HOOKS_DIR/pre-commit"
    if [ -f "$HOOK" ] && grep -q "just git-pre-commit" "$HOOK"; then
        echo "🪝 pre-commit hook already installed, skipping."
    else
        cat > "$HOOK" << 'HOOKEOF'
    #!/bin/bash
    just git-pre-commit
    HOOKEOF
        chmod +x "$HOOK"
        echo "🪝 Installed pre-commit hook."
    fi

    # Pre-push hook
    HOOK="$HOOKS_DIR/pre-push"
    if [ -f "$HOOK" ] && grep -q "just git-pre-push" "$HOOK"; then
        echo "🪝 pre-push hook already installed, skipping."
    else
        cat > "$HOOK" << 'HOOKEOF'
    #!/bin/bash
    just git-pre-push
    HOOKEOF
        chmod +x "$HOOK"
        echo "🪝 Installed pre-push hook."
    fi

# Install Claude Code CLI if not present
claude-cli:
    #!/bin/bash
    set -euo pipefail
    echo ""
    echo "── Claude Code ──"
    if command -v claude &>/dev/null; then
        echo "🤖 CLI already installed."
    else
        echo "🤖 Installing CLI..."
        curl -fsSL https://claude.ai/install.sh | bash
        echo "🤖 CLI installed."
    fi

# Install Claude Code plugins from .claude/settings.json (skips already-installed)
claude-plugins:
    #!/bin/bash
    set -euo pipefail
    plugins=$(jq -r '.enabledPlugins // {} | keys[]' .claude/settings.json)
    if [ -z "$plugins" ]; then
        echo "🔌 No plugins in .claude/settings.json, skipping."
        exit 0
    fi
    # Ensure third-party marketplaces are registered before installing
    mp_sources=".claude/plugin-marketplaces.json"
    marketplaces=$(echo "$plugins" | sed -n 's/.*@//p' | sort -u)
    while IFS= read -r mp; do
        [ -z "$mp" ] && continue
        if claude plugin marketplace list 2>/dev/null | grep -q "$mp"; then
            echo "  ✅ marketplace '$mp' already registered"
        else
            repo=$(jq -r --arg mp "$mp" '.[$mp] // empty' "$mp_sources")
            if [ -z "$repo" ]; then
                echo "  ⚠️  marketplace '$mp' not found in $mp_sources, skipping"
                continue
            fi
            echo "  🔗 adding marketplace '$mp' ($repo)..."
            claude plugin marketplace add "$repo" 1>/dev/null || true
        fi
    done <<< "$marketplaces"

    installed=$(claude plugin list 2>/dev/null)
    echo "🔌 Installing plugins..."
    while IFS= read -r plugin; do
        if echo "$installed" | grep -q "$plugin"; then
            echo "  ✅ $plugin already installed"
        else
            echo "  📥 $plugin"
            claude plugin install "$plugin" 1>/dev/null || true
        fi
    done <<< "$plugins"
