set working-directory := '..'

# Run full code review via Claude Code CLI (automated checks + Codex semantic pass)
all:
    claude -p "/code-review"

# Run automated code-review checks against changed files
code ref='main':
    #!/usr/bin/env bash
    set -uo pipefail

    ref="{{ref}}"

    # Collect changed files (vs ref + any staged/unstaged)
    changed=$(
        {
            git diff --name-only --diff-filter=d "$ref" -- 'src/' 2>/dev/null
            git diff --name-only --diff-filter=d -- 'src/' 2>/dev/null
            git diff --cached --name-only --diff-filter=d -- 'src/' 2>/dev/null
        } | sort -u
    )

    if [ -z "$changed" ]; then
        echo "No reviewable files changed."
        exit 0
    fi

    py_files=$(echo "$changed" | grep '\.py$' || true)
    ts_files=$(echo "$changed" | grep -E '\.(ts|tsx)$' || true)

    echo "## Script Findings"
    echo ""
    echo "**Ref:** $ref"
    echo "**Files:** $(echo "$changed" | wc -l | tr -d ' ') changed"
    echo ""

    # -- Lint Python --
    echo "### Lint — Python"
    if [ -n "$py_files" ]; then
        # shellcheck disable=SC2086
        uv run ruff check $py_files || true
    else
        echo "No Python files changed."
    fi
    echo ""

    # -- Lint TypeScript --
    echo "### Lint — TypeScript"
    if [ -n "$ts_files" ]; then
        # Paths must be relative to src/web for eslint
        web_files=$(echo "$ts_files" | sed 's|^src/web/||')
        # shellcheck disable=SC2086
        (cd src/web && pnpm eslint $web_files) || true
    else
        echo "No TypeScript files changed."
    fi
    echo ""

    # -- Convention checks (Python only) --
    if [ -n "$py_files" ]; then
        echo "### Check — Line Limits"
        # shellcheck disable=SC2086
        bash scripts/lib/check_lines.sh $py_files || true
        echo ""

        echo "### Check — Dependency Injection"
        # shellcheck disable=SC2086
        uv run python scripts/lib/check_di.py $py_files || true
        echo ""

        echo "### Check — Literal Strings"
        # shellcheck disable=SC2086
        uv run python scripts/lib/check_literal_strings.py $py_files || true
        echo ""

        echo "### Check — Mapper Patterns"
        # shellcheck disable=SC2086
        uv run python scripts/lib/check_mapper_patterns.py $py_files || true
        echo ""

        echo "### Check — Service Patterns"
        # shellcheck disable=SC2086
        uv run python scripts/lib/check_service_patterns.py $py_files || true
        echo ""
    fi

    # -- Line limits for TypeScript --
    if [ -n "$ts_files" ]; then
        echo "### Check — Line Limits (TypeScript)"
        # shellcheck disable=SC2086
        bash scripts/lib/check_lines.sh $ts_files || true
        echo ""
    fi
