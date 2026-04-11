set working-directory := '..'

fork *args:
    uv run python scripts/lib/fork.py {{args}}
