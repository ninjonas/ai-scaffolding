"""Singleton factory for ChromaDB PersistentClient."""

from typing import Any

import structlog

log = structlog.get_logger()

_client: Any = None


def get_chroma_client(settings: Any) -> Any:
    """Return the singleton ChromaDB PersistentClient, initializing on first call.

    Args:
        settings: Application Settings instance providing chroma_path.

    Returns:
        chromadb.PersistentClient instance.
    """
    global _client
    if _client is not None:
        return _client

    import chromadb

    chroma_path = settings.chroma_path
    log.info("chroma_client_init", chroma_path=chroma_path)
    _client = chromadb.PersistentClient(path=chroma_path)
    log.info("chroma_client_ready", chroma_path=chroma_path)
    return _client
