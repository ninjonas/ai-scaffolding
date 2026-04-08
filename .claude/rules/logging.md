## Logging

### Libraries

- **Python**: `structlog` — structured, JSON-native logging
- **TypeScript**: `pino` — fast, JSON-native structured logging

### Output format

Both Python and TypeScript must use the **same log format**:

- **File output** (`logs/`): JSON structured logs
  ```json
  {"timestamp": "2026-04-07T12:00:00Z", "level": "info", "module": "auth", "message": "User logged in", "user_id": 42}
  ```
- **Stdout** (dev mode): Human-readable text
  ```
  2026-04-07 12:00:00 | INFO | auth | User logged in | user_id=42
  ```

### Rules

- Log files go in `logs/` only — never write logs elsewhere
- Use structured key-value pairs for context, not string interpolation
- Log at appropriate levels: `debug` for internals, `info` for operations, `warning` for recoverable issues, `error` for failures
- Verbose logging is expected — when in doubt, log it
- Never log secrets, tokens, passwords, or PII
- Inject loggers via DI — do not call `getLogger()` or `logging.getLogger()` directly in production code (see code-conventions.md)
