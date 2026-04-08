set working-directory := '..'

py *args:
    uv run ruff check src/ {{args}}

ts *args:
    cd src/web && pnpm eslint . {{args}}

md *args:
    uv run mdformat --check --exclude 'docs/guidelines/*' --exclude 'docs/agents/*' --exclude 'docs/skills/*' docs/ {{args}}
    uv run mdformat --check CLAUDE.md README.md {{args}}
