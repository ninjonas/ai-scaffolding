## Code Conventions

### Line limits

| Scope | Warn | Fail |
| ----- | ---- | ---- |
| Source file (py/ts/tsx) | 160 lines | 200 lines |
| Test file | 400 lines | 500 lines |
| Function/method | 40 lines | 50 lines |

If a file or method is approaching the limit, refactor:
- Extract helper functions or classes
- Split large files into focused modules
- Move test utilities to shared fixtures/helpers

Run `just check-lines` to verify.

### Constants for literal strings

- **Never use repeated string literals in `src/app/`** — extract them to module-level constants (`UPPER_SNAKE_CASE`).
- **Tests must use app constants** — if a string is defined as a constant in `src/app/`, tests must import and use that constant, not re-type the raw string.
- Exempt: logging messages, decorator arguments, type hints, local dict keys, docstrings.

Run `just check-literal-strings` to verify.

### Dependency injection (Python)

- All dependencies must be received via constructor injection — never instantiate them directly.
- Use injected `Settings` for configuration — never call `os.getenv()` or `os.environ` in production code.
- Exceptions: DI container files, entry points, database bootstrapping, test files.

Run `just check-di` to verify.

### Aggregate check

Run `just check` to run all convention checks at once (lines, DI, literal-strings).

### Scripts

- Shell scripts supporting just recipes live in `scripts/lib/`.
- Complex checks use Python (`scripts/lib/*.py`), simple checks use shell (`scripts/lib/*.sh`).