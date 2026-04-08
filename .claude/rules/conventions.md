## Conventions

- Python 3.12+, managed exclusively with `uv` (never pip/poetry)
- TypeScript managed with pnpm
- Ruff for all Python linting/formatting (not flake8/black/isort)
- ESLint + Prettier for TypeScript
- The root `justfile` is the single entry point for all tasks; see `justfile-conventions.md` for details
- Each `scripts/*.just` file owns one concern (SRP)
