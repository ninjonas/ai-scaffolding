set working-directory := '..'

py *args:
    uv run ruff format src/ {{args}}
    uv run ruff check --fix src/ {{args}}

ts *args:
    cd src/web && pnpm prettier --write src/ {{args}}

md *args:
    uv run mdformat docs/ AGENT.md CLAUDE.md README.md {{args}}
