set working-directory := '..'

py *args:
    uv run ruff format src/ {{args}}
    uv run ruff check --fix src/ {{args}}

ts *args:
    cd src/web && pnpm prettier --write src/ {{args}}

md *args:
    uv run mdformat --exclude 'docs/guidelines/*' --exclude 'docs/agents/*' --exclude 'docs/skills/*' docs/ {{args}}
    uv run mdformat CLAUDE.md README.md {{args}}
