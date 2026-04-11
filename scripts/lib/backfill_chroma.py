"""Backfill ChromaDB with existing knowledge files and chat messages from SQLite.

Run: uv run python scripts/lib/backfill_chroma.py [--dry-run]

Idempotent: uses upsert so re-running is safe.
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Allow imports from src/
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import structlog
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.infrastructure.models.knowledge_file import KnowledgeFileModel
from app.infrastructure.models.message import MessageModel
from app.infrastructure.vector.client import get_chroma_client
from app.infrastructure.vector.knowledge_indexer import KnowledgeIndexer
from app.infrastructure.vector.message_indexer import MessageIndexer
from app.shared.config import Settings
from app.shared.logging import configure_logging

log = structlog.get_logger()

MESSAGE_BATCH_SIZE = 100


def _sync_database_url(url: str) -> str:
    """Strip +aiosqlite from URL for sync engine."""
    return url.replace("+aiosqlite", "")


async def backfill_knowledge(
    session: Session, indexer: KnowledgeIndexer, dry_run: bool
) -> int:
    files = session.execute(select(KnowledgeFileModel)).scalars().all()
    log.info("backfill_knowledge_files_found", count=len(files))
    indexed = 0
    for f in files:
        if dry_run:
            log.info("dry_run_knowledge", file_id=f.id, name=f.name)
            continue
        chunk_count = await indexer.index(
            f.id, f.name, f.content, f.file_type, f.scope, f.conversation_id,
            f.description, f.tags,
        )
        log.info("backfill_knowledge_indexed", file_id=f.id, chunk_count=chunk_count)
        indexed += 1
    return indexed


async def backfill_messages(
    session: Session, indexer: MessageIndexer, dry_run: bool
) -> int:
    messages = session.execute(select(MessageModel)).scalars().all()
    log.info("backfill_messages_found", count=len(messages))
    indexed = 0
    for i, m in enumerate(messages):
        if dry_run:
            log.info("dry_run_message", message_id=m.id, role=m.role)
            continue
        created_at = m.created_at.isoformat() if m.created_at else ""
        await indexer.index(m.id, m.content, m.role, m.conversation_id, created_at)
        indexed += 1
        if (i + 1) % MESSAGE_BATCH_SIZE == 0:
            log.info("backfill_messages_progress", indexed=indexed, total=len(messages))
    return indexed


async def main(dry_run: bool) -> None:
    configure_logging(log_level="INFO", log_json=False)
    settings = Settings()

    sync_url = _sync_database_url(settings.database_url)
    engine = create_engine(sync_url)

    chroma_client = get_chroma_client(settings)
    knowledge_indexer = KnowledgeIndexer(chroma_client, settings)
    message_indexer = MessageIndexer(chroma_client, settings)

    with Session(engine) as session:
        k_count = await backfill_knowledge(session, knowledge_indexer, dry_run)
        m_count = await backfill_messages(session, message_indexer, dry_run)

    if dry_run:
        log.info("dry_run_complete", note="no data was written")
    else:
        log.info("backfill_complete", knowledge_files=k_count, messages=m_count)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill ChromaDB from SQLite")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log what would be indexed without writing to ChromaDB",
    )
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run))
