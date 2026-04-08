# Scaffolding

A monorepo with a Python (FastAPI) backend and a Vite React TypeScript frontend.

## Prerequisites

- [Homebrew](https://brew.sh)
- [just](https://github.com/casey/just) — install with `brew install just`

## Installation

```sh
just setup
```

This installs system dependencies (uv, node, pnpm), Python packages, and Node packages.

See [docs/SETUP.md](docs/SETUP.md) for a detailed walkthrough.

## Quick reference

| Task              | Command            |
| ----------------- | ------------------ |
| Run all tests     | `just test`        |
| Run all lints     | `just lint`        |
| Format all        | `just fmt`         |
| Start dev servers | `just dev-start`   |
| Stop dev servers  | `just dev-stop`    |
| Restart dev       | `just dev-restart` |
| Start docs        | `just docs-start`  |
| First-time setup  | `just setup`       |
