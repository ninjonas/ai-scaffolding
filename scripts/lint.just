set working-directory := '..'

py *args:
    uv run ruff check src/ {{args}}

ts *args:
    cd src/web && pnpm eslint . {{args}}

md *args:
    uv run mdformat --check docs/ AGENT.md CLAUDE.md README.md {{args}}
