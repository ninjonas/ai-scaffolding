set working-directory := '..'

py *args:
    uv run pytest {{args}}

ts *args:
    cd src/web && pnpm vitest --run {{args}}
