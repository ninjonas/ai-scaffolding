## Common commands

| Task              | Command                  |
| ----------------- | ------------------------ |
| Run all tests     | `just test`              |
| Run all lints     | `just lint`              |
| Format all        | `just fmt`               |
| Run all checks    | `just check`             |
| Check line limits | `just check-lines`       |
| Check DI          | `just check-di`          |
| Check literals    | `just check-literal-strings` |
| Start dev servers | `just dev-start`         |
| Stop dev servers  | `just dev-stop`          |
| Start docs        | `just docs-start`        |
| First-time setup  | `just setup`             |

## Testing

- Python: `just test-py` (pytest, async with httpx)
- TypeScript: `just test-ts` (vitest, jsdom, testing-library)

## Before committing

Git hooks run automatically (installed via `just setup`):
- **Pre-commit**: `just lint` + `just fmt` + `just check`
- **Pre-push**: `just test`

To run manually: `just git-pre-commit` or `just git-pre-push`.
