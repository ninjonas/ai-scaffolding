# Justfile Conventions

## Architecture

- **Root `justfile`** is a thin dispatcher. It defines port variables and `set dotenv-load`, then delegates every recipe to a child justfile via `just -f scripts/<concern>.just <recipe> {{args}}`.
- **Never put inline shell logic in the root justfile** (except trivial one-liners like `@just --list`).
- All implementation lives in **`scripts/*.just`** files, one file per concern (SRP): `lint.just`, `fmt.just`, `test.just`, `dev.just`, `setup.just`, `docs.just`, etc.

## Child justfile rules

- Every child justfile **must** start with `set working-directory := '..'` so paths resolve from repo root.
- Port configuration uses `env("VAR", "default")` inside the child file when needed.
- Recipe names inside child files are short verbs/nouns (`py`, `ts`, `md`, `all`, `kill`).

## Root justfile rules

- Port variables are defined at the top: `API_PORT := env("API_PORT", "8000")`, etc.
- Delegating recipes use the pattern: `recipe-name *args:` followed by `just -f scripts/<concern>.just <sub-recipe> {{args}}`.
- Aggregate recipes (`lint`, `test`, `fmt`) call sub-recipes sequentially on one line.
- Recipes are grouped under comment headers: `# -- Python --`, `# -- All --`, etc.

## Naming conventions

- Root recipes: `{concern}-{action}` (e.g., `dev-start`, `docs-build`, `lint-py`, `fmt-ts`).
- Aggregate recipes are plain names: `lint`, `test`, `fmt`.

## Adding a new recipe

1. Identify or create the appropriate `scripts/{concern}.just` file.
2. Add the implementation recipe there (with `set working-directory := '..'`).
3. Add a delegating recipe in the root `justfile` under the correct section header.
4. If adding a new concern, create both the child file and a new section in root.
