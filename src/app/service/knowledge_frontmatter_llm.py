"""LLM-powered frontmatter generation for knowledge file uploads."""

import structlog
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, field_validator

from app.shared.field_keys import CONTENT_TYPE_IMAGE_URL, CONTENT_TYPE_TEXT

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

    @field_validator("tags", mode="before")
    @classmethod
    def coerce_tags(cls, v: object) -> list[str]:
        """LLMs sometimes return tags as a comma-separated string."""
        if isinstance(v, str):
            return [t.strip() for t in v.split(",") if t.strip()]
        return v  # type: ignore[return-value]


IMAGE_DESCRIBE_PROMPT = (
    "You are a visual analysis assistant. Analyze this image in detail and produce "
    "structured metadata optimized for search and retrieval.\n\n"
    "Rules:\n"
    "- name: a clean, human-readable display name (title case, no extension)\n"
    "- description: a comprehensive multi-paragraph analysis covering ALL of the following "
    "that apply. Write in plain prose, not bullet points:\n"
    "  1. Subject matter: what is depicted, number of figures/objects, their poses, "
    "expressions, gestures, and relationships\n"
    "  2. Composition: layout, framing, focal points, use of space, symmetry or asymmetry\n"
    "  3. Color and light: dominant palette, color temperature, contrast, light sources, "
    "shadows, highlights\n"
    "  4. Technique and medium: visible brushwork, texture, layering, drips, mixed media, "
    "photographic qualities, digital artifacts\n"
    "  5. Style and influences: art movement, period references, historical or contemporary "
    "influences, genre\n"
    "  6. Mood and atmosphere: emotional tone, symbolism, narrative implied\n"
    "  7. Context clues: text, signatures, framing, setting, identifiable references\n"
    "- tags: 8 to 15 lowercase kebab-case keywords covering subject, style, technique, "
    "mood, and color\n\n"
    "Write the description as if cataloging the image for a searchable archive. "
    "Be specific and factual. Avoid vague language.\n\n"
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
            KnowledgeFrontmatterSchema,
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
        log.warning("knowledge_llm_image_describe_error", error=str(exc), file_type=file_type, exc_info=exc)
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
            KnowledgeFrontmatterSchema,
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
        log.warning("knowledge_llm_frontmatter_error", error=str(exc), file_type=file_type, exc_info=exc)
        return "", "", []
