# Docs tasks.

set working-directory := '..'

DOCS_PORT := env("DOCS_PORT", "8100")

# Start MkDocs dev server
start *args:
    uv run mkdocs serve -a localhost:{{DOCS_PORT}} {{args}} &

# Stop docs server
stop:
    just -f {{justfile_directory()}}/dev.just kill {{DOCS_PORT}}

# Restart docs server
restart:
    just -f {{justfile()}} stop
    just -f {{justfile()}} start

# Build docs
build *args:
    uv run mkdocs build {{args}}
