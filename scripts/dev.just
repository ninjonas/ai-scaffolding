# Dev utilities.

set working-directory := '..'

API_PORT := env("API_PORT", "8000")
WEB_PORT := env("WEB_PORT", "3000")

# Kill process(es) on a given port
kill port:
    #!/bin/bash
    set -euo pipefail
    PORT="{{port}}"
    if ! lsof -ti:"$PORT" >/dev/null 2>&1; then
        echo "ℹ️  No process found running on port $PORT"
        exit 0
    fi
    echo "Processes using port $PORT:"
    lsof -ti:"$PORT" | while read -r PID; do
        ps -p "$PID" -o pid=,comm=,args= 2>/dev/null | awk '{print "  PID " $1 " - " $2 " (" substr($0, index($0,$3)) ")"}'
    done
    pids=$(lsof -ti:"$PORT")
    count=$(echo "$pids" | wc -w | tr -d '[:space:]')
    for PID in $pids; do
        kill -9 "$PID" 2>/dev/null || true
    done
    if [ "$count" = "1" ]; then
        echo "✓ Killed $count process on port $PORT"
    else
        echo "✓ Killed $count processes on port $PORT"
    fi

# Start API + web dev servers
start:
    #!/usr/bin/env bash
    rm -f logs/api.log logs/web.log
    nohup uv run uvicorn app.main:app --reload --host 0.0.0.0 --port {{API_PORT}} > logs/api.log 2>&1 &
    echo "API server started on port {{API_PORT}} (PID $!)"
    nohup sh -c 'cd src/web && pnpm run dev --port {{WEB_PORT}}' > logs/web.log 2>&1 &
    echo "Web server started on port {{WEB_PORT}} (PID $!)"

# Stop dev servers
stop:
    just -f {{justfile()}} kill {{API_PORT}}
    just -f {{justfile()}} kill {{WEB_PORT}}

# Restart dev servers
restart:
    just -f {{justfile()}} stop
    just -f {{justfile()}} start

# Build web frontend
build-web:
    cd src/web && pnpm run build
