"""LLM-powered frontmatter generation for knowledge file uploads."""

import structlog
from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel

log = structlog.get_logger(__name__)

LLM_FRONTMATTER_PROMPT = (
    "You are a file metadata assistant. Given the content and type of a file, "
    "produce structured metadata.\n\n"
    "Rules:\n"
    "- name: a clean, human-readable display name for this file (title case, no extension)\n"
    "- description: exactly one sentence summarising the file's content and purpose\n"
    "- tags: 3 to 8 lowercase kebab-case keywords relevant to the content\n\n"
    "File type: {file_type}\n\n"
    "File content:\n{content}"
)

CONTENT_PREVIEW_CHARS = 4000


class KnowledgeFrontmatterSchema(BaseModel):
    """Structured output schema for LLM-generated file frontmatter."""

    name: str
    description: str
    tags: list[str]


async def llm_generate(
    content: str,
    file_type: str,
    llm: BaseChatModel,
) -> tuple[str, str, list[str]]:
    """Generate file frontmatter using an LLM with structured output.

    Returns (name, description, tags). On any failure returns ("", "", [])
    so the caller can fall back to heuristic generation.
    """
    log.info("knowledge_llm_frontmatter_start", file_type=file_type)
    try:
        structured_llm = llm.with_structured_output(KnowledgeFrontmatterSchema, method="json_mode")
        preview = content[:CONTENT_PREVIEW_CHARS]
        prompt = LLM_FRONTMATTER_PROMPT.format(file_type=file_type, content=preview)
        result: KnowledgeFrontmatterSchema = await structured_llm.ainvoke(prompt)
        log.info(
            "knowledge_llm_frontmatter_done",
            name=result.name,
            tag_count=len(result.tags),
        )
        return result.name, result.description, result.tags
    except Exception as exc:
        log.warning("knowledge_llm_frontmatter_error", error=str(exc), file_type=file_type)
        return "", "", []
