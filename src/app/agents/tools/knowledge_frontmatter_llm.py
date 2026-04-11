"""LLM-powered frontmatter generation for knowledge file uploads."""

import structlog
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from app.shared.field_keys import CONTENT_TYPE_IMAGE_URL, CONTENT_TYPE_TEXT

log = structlog.get_logger(__name__)

LLM_STRUCTURED_OUTPUT_METHOD = "json_mode"

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


IMAGE_DESCRIBE_PROMPT = (
    "You are a file metadata assistant. Analyze this image and produce structured metadata.\n\n"
    "Rules:\n"
    "- name: a clean, human-readable display name for this image (title case, no extension)\n"
    "- description: exactly one sentence describing what is shown in the image\n"
    "- tags: 3 to 8 lowercase kebab-case keywords relevant to the image content\n\n"
    "File type: {file_type}"
)


async def llm_describe_image(
    image_b64: str,
    file_type: str,
    llm: BaseChatModel,
) -> tuple[str, str, list[str]]:
    """Generate frontmatter for an image using the LLM's vision capability.

    Returns (name, description, tags). On any failure returns ("", "", [])
    so the caller can fall back to heuristic generation.
    """
    log.info("knowledge_llm_image_describe_start", file_type=file_type)
    try:
        structured_llm = llm.with_structured_output(
            KnowledgeFrontmatterSchema, method=LLM_STRUCTURED_OUTPUT_METHOD
        )
        prompt = IMAGE_DESCRIBE_PROMPT.format(file_type=file_type)
        message = HumanMessage(
            content=[
                {"type": CONTENT_TYPE_TEXT, "text": prompt},
                {
                    "type": CONTENT_TYPE_IMAGE_URL,
                    "image_url": {"url": f"data:image/{file_type};base64,{image_b64}"},
                },
            ]
        )
        result: KnowledgeFrontmatterSchema = await structured_llm.ainvoke([message])
        log.info(
            "knowledge_llm_image_describe_done",
            name=result.name,
            description_length=len(result.description),
            tag_count=len(result.tags),
        )
        return result.name, result.description, result.tags
    except Exception as exc:
        log.warning("knowledge_llm_image_describe_error", error=str(exc), file_type=file_type)
        return "", "", []


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
        structured_llm = llm.with_structured_output(
            KnowledgeFrontmatterSchema, method=LLM_STRUCTURED_OUTPUT_METHOD
        )
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
