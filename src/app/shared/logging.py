import logging
import sys
from pathlib import Path

import structlog

LOGS_DIR = Path("logs")


def _apply_structlog_formatters(
    shared_processors: list[structlog.types.Processor],
    renderer: structlog.types.Processor,
    file_handler: logging.FileHandler,
    console_handler: logging.StreamHandler,
) -> None:
    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    json_formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
    )
    console_formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )
    file_handler.setFormatter(json_formatter)
    console_handler.setFormatter(console_formatter)


def configure_logging(*, log_level: str = "INFO", log_json: bool = False) -> None:
    LOGS_DIR.mkdir(exist_ok=True)

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    file_handler = logging.FileHandler(LOGS_DIR / "app.log")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter("%(message)s"))

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    logging.basicConfig(level=log_level, handlers=[file_handler, console_handler], force=True)

    if log_json:
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        # Avoid ANSI in captured stdout (e.g. `uvicorn ... > logs/api.log`): only color a real TTY.
        renderer = structlog.dev.ConsoleRenderer(colors=sys.stdout.isatty())

    _apply_structlog_formatters(shared_processors, renderer, file_handler, console_handler)
