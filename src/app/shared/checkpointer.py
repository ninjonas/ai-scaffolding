"""Singleton factory for LangGraph AsyncSqliteSaver checkpointer."""

from pathlib import Path
from typing import Any

import structlog

log = structlog.get_logger()

_checkpointer: Any = None


async def get_checkpointer(settings: Any) -> Any:
    """Return the singleton AsyncSqliteSaver, initializing it on first call.

    Args:
        settings: Application Settings instance providing checkpoint_db_path.

    Returns:
        Initialized AsyncSqliteSaver instance.
    """
    global _checkpointer
    if _checkpointer is not None:
        return _checkpointer

    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

    db_path = settings.checkpoint_db_path
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    log.info("checkpointer_init", db_path=db_path)

    checkpointer = AsyncSqliteSaver.from_conn_string(db_path)
    await checkpointer.__aenter__()
    _checkpointer = checkpointer
    log.info("checkpointer_ready", db_path=db_path)
    return _checkpointer
