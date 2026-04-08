# Docs tasks.

set working-directory := '..'

DOCS_PORT := env("DOCS_PORT", "8100")

# Sync .claude/ markdown into docs/ and update mkdocs.yml nav
sync-docs:
    uv run python scripts/lib/sync_docs.py

# Start MkDocs dev server
start *args: sync-docs
    #!/usr/bin/env bash
    rm -f logs/docs.log
    nohup uv run mkdocs serve -a localhost:{{DOCS_PORT}} {{args}} > logs/docs.log 2>&1 &
    echo "Docs server started on port {{DOCS_PORT}} (PID $!)"

# Stop docs server
stop:
    just -f {{justfile_directory()}}/dev.just kill {{DOCS_PORT}}

# Restart docs server
restart:
    just -f {{justfile()}} stop
    just -f {{justfile()}} start

# Build docs
build *args: sync-docs
    uv run mkdocs build {{args}}
