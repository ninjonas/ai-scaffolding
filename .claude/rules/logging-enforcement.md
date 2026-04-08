## Logging Enforcement

When generating or modifying code, **always consider logging**. This is not optional.

### What to log

- **Service layer**: log every method entry/exit with key parameters and duration
- **API routes**: log incoming requests (method, path, status) and outgoing responses
- **Agent nodes**: log every LangGraph node invocation, tool calls, skill loads, and LLM responses (token counts, latency)
- **Errors**: log full exception context with structured fields, never bare `except: pass`
- **Image processing**: log original size, optimized size, format, and duration

### How to log

- Use `structlog` bound loggers — never `print()` or `logging.getLogger()` in production code
- Bind contextual fields early: `log = log.bind(conversation_id=cid, user_id=uid)`
- Use appropriate levels: `debug` for internals, `info` for operations, `warning` for recoverable issues, `error` for failures
- Include timing for any operation that calls an external service (LLM, search API, file I/O)

### Review checklist

Before considering a function complete, verify:

1. Does it log entry with key parameters?
2. Does it log the outcome (success with result summary, or error with context)?
3. Are external calls wrapped with timing logs?
4. Are structured key-value pairs used (not f-strings in messages)?
