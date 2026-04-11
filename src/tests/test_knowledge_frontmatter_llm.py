"""Unit tests for knowledge_frontmatter_llm.llm_generate."""

from typing import Any

import pytest
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.runnables import RunnableLambda

from app.service.knowledge_frontmatter_llm import (
    KnowledgeFrontmatterSchema,
    llm_describe_image,
    llm_generate,
)


class StructuredOutputLLM(BaseChatModel):
    """Fake LLM that returns a fixed schema via with_structured_output."""

    schema_result: Any
    should_raise: bool = False

    def _generate(
        self,
        messages: list[Any],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=""))])

    @property
    def _llm_type(self) -> str:
        return "structured-test-llm"

    def with_structured_output(self, schema: Any, **kwargs: Any) -> Any:  # type: ignore[override]
        if self.should_raise:

            async def _raise(prompt: Any) -> Any:
                raise RuntimeError("LLM failure")

            return RunnableLambda(_raise)
        result = self.schema_result

        async def _return(prompt: Any) -> Any:
            return result

        return RunnableLambda(_return)


def _valid_schema() -> KnowledgeFrontmatterSchema:
    return KnowledgeFrontmatterSchema(
        name="My Document",
        description="A one-sentence description of the file.",
        tags=["python", "tutorial", "guide"],
    )


@pytest.mark.asyncio
async def test_llm_generate_returns_name_description_tags() -> None:
    llm = StructuredOutputLLM(schema_result=_valid_schema())
    name, description, tags = await llm_generate("some content", "md", llm)
    assert name == "My Document"
    assert description == "A one-sentence description of the file."
    assert tags == ["python", "tutorial", "guide"]


@pytest.mark.asyncio
async def test_llm_generate_returns_empty_on_llm_exception() -> None:
    llm = StructuredOutputLLM(schema_result=None, should_raise=True)
    result = await llm_generate("some content", "json", llm)
    assert result == ("", "", [])


def test_coerce_tags_splits_comma_string() -> None:
    schema = KnowledgeFrontmatterSchema(name="Test", description="Desc", tags="python, ml, data")
    assert schema.tags == ["python", "ml", "data"]


def test_coerce_tags_passes_list_through() -> None:
    schema = KnowledgeFrontmatterSchema(name="Test", description="Desc", tags=["a", "b"])
    assert schema.tags == ["a", "b"]


@pytest.mark.asyncio
async def test_llm_describe_image_returns_name_description_tags() -> None:
    schema = KnowledgeFrontmatterSchema(
        name="Sunset Over Mountains",
        description="A vivid landscape photograph showing a sunset over a mountain range.",
        tags=["landscape", "sunset", "mountains", "photography"],
    )
    llm = StructuredOutputLLM(schema_result=schema)
    name, description, tags = await llm_describe_image("base64data", "png", llm)
    assert name == "Sunset Over Mountains"
    assert "sunset" in description.lower()
    assert tags == ["landscape", "sunset", "mountains", "photography"]


@pytest.mark.asyncio
async def test_llm_describe_image_returns_empty_on_failure() -> None:
    llm = StructuredOutputLLM(schema_result=None, should_raise=True)
    result = await llm_describe_image("base64data", "png", llm)
    assert result == ("", "", [])


@pytest.mark.asyncio
async def test_llm_generate_returns_empty_on_invalid_schema() -> None:
    """If structured output returns something that doesn't match expectations, fallback."""
    # Returning a plain dict causes AttributeError on .name access, triggering the fallback.
    llm = StructuredOutputLLM(schema_result={"not": "a schema"})
    result = await llm_generate("some content", "txt", llm)
    assert result == ("", "", [])
