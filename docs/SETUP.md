# Setup guide

## Prerequisites

You need [Homebrew](https://brew.sh) and [just](https://github.com/casey/just) installed before anything else.

Install just:

```sh
brew install just
```

## One-command setup

From the repo root:

```sh
just setup
```

This runs through three steps:

1. **System tools** — `brew install uv node pnpm`
1. **Python** — `uv sync --extra dev` (creates `.venv/`, installs FastAPI, pytest, ruff, mdformat, etc.)
1. **Node** — `cd src/web && pnpm install` (installs React, Vite, ESLint, Prettier, Vitest, etc.)

## Manual setup

If you prefer to run each step yourself:

```sh
# System tools
brew install uv node pnpm

# Python
uv sync --extra dev

# Node
cd src/web && pnpm install
```

## Verify everything works

```sh
just lint    # ruff, eslint, mdformat — all should pass
just test    # pytest + vitest — all should pass
```

## Running the app

```sh
just dev-start    # starts API (localhost:8000) + frontend (localhost:3000)
just dev-stop     # stops both
just dev-restart   # stop + start
```

Ports are configured in `.env` (see `.env.example` for defaults).

**Docs server:**

```sh
just docs-start   # MkDocs on localhost:8100
just docs-stop
```

## Project structure

```
src/app/       Python library + FastAPI backend
src/web/       Vite React TypeScript frontend
src/tests/     Python tests (pytest)
scripts/        Child justfiles (one per concern)
docs/          Documentation (MkDocs site)
logs/          Log output
tmp/           Scratch / spike output
```
