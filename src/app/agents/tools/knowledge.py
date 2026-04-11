import structlog
from langchain_core.tools import tool

from app.domain.repositories.knowledge_file import KnowledgeFileRepository
from app.shared.field_keys import (
    FIELD_KEY_DESCRIPTION,
    FIELD_KEY_FILE_TYPE,
    FIELD_KEY_ID,
    FIELD_KEY_NAME,
    FIELD_KEY_SCOPE,
)

log = structlog.get_logger(__name__)

CATALOG_HEADER = (
    "## Knowledge Base\n\n"
    "The following files are in the user's knowledge base. "
    "Each entry includes an id. "
    "Call `read_knowledge_file` with that id directly when a file is relevant. "
    "Do not ask the user for file ids or which file to read; use the ids below.\n"
)

CATALOG_ENTRY_PREFIX = "- **"


def build_knowledge_catalog(catalog: list[dict]) -> str:
    """Format catalog entries into a system prompt section.

    Each entry must have: name, file_type, scope, description, id.
    Returns an empty string when catalog is empty.
    """
    if not catalog:
        return ""
    lines = []
    for entry in catalog:
        name = entry.get(FIELD_KEY_NAME, "")
        file_type = entry.get(FIELD_KEY_FILE_TYPE, "")
        scope = entry.get(FIELD_KEY_SCOPE, "")
        description = entry.get(FIELD_KEY_DESCRIPTION, "")
        file_id = entry.get(FIELD_KEY_ID, "")
        entry_line = (
            f"{CATALOG_ENTRY_PREFIX}{name}** ({file_type}, {scope}): {description} [id: {file_id}]"
        )
        lines.append(entry_line)
    return CATALOG_HEADER + "\n".join(lines)


def make_read_knowledge_file_tool(repository: KnowledgeFileRepository):
    """Factory that closes over a KnowledgeFileRepository and returns the tool."""

    @tool
    async def read_knowledge_file(file_id: str) -> str:
        """Read full contents of a knowledge base file by ID.

        Use when you need detailed information from a file listed in the
        knowledge base catalog. The catalog shows file name, description,
        and tags to help you decide which files are relevant.
        """
        log.info("knowledge_file_read_start", file_id=file_id)
        knowledge_file = await repository.get_by_id(file_id)
        if knowledge_file is None:
            log.warning("knowledge_file_not_found", file_id=file_id)
            return f"Knowledge file '{file_id}' not found."
        log.info(
            "knowledge_file_read_done",
            file_id=file_id,
            name=knowledge_file.name,
            content_length=len(knowledge_file.content),
        )
        return knowledge_file.content

    return read_knowledge_file
