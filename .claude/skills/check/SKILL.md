# Check — Convention Checks

Run project convention checks to validate code quality rules.

## Commands

| Task | Command |
| ---- | ------- |
| Run all checks | `just check` |
| Check file/method line limits | `just check-lines` |
| Check dependency injection (Python) | `just check-di` |
| Check literal string usage | `just check-literal-strings` |

## What each check does

### `just check-lines`
Validates file and method length limits:
- Source files (py/ts/tsx): max 200 lines, warns at 160+
- Test files: max 500 lines, warns at 400+
- Functions/methods: max 50 lines, warns at 40+

### `just check-di`
Python only. Flags:
- Direct instantiation of dependencies (should be injected via constructor)
- Direct `os.getenv()`/`os.environ` access (should use injected Settings)

Skips test files, DI containers, entry points, and database bootstrap code.

### `just check-literal-strings`
Flags:
- String literals appearing 2+ times in `src/app/` (extract to constants)
- String literals in `src/tests/` that match existing constants in `src/app/` (use the constant)

## Passing files

All check commands accept file paths as arguments:
```bash
just check-lines src/app/services/auth.py
just check-di src/app/services/auth.py
just check-literal-strings src/app/services/auth.py
```

## When to run

These checks run automatically in the pre-commit hook via `just git-pre-commit`.
Run `just check` manually before committing if you want early feedback.
