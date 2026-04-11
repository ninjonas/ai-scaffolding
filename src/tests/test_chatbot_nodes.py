"""Unit tests for chatbot agent nodes (invoke_llm, should_continue)."""

from typing import Any, ClassVar

import pytest
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from app.agents.chatbot.nodes import invoke_llm, should_continue
from app.agents.constants import NODE_END, NODE_TOOLS


class FixedAIMessageModel(BaseChatModel):
    """Minimal fake: always returns the configured AIMessage."""

    response: AIMessage
    last_messages: ClassVar[list] = []

    def _generate(
        self,
        messages: list[Any],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        object.__setattr__(self, "last_messages", list(messages))
        return ChatResult(generations=[ChatGeneration(message=self.response)])

    @property
    def _llm_type(self) -> str:
        return "fixed-test-llm"

    def bind_tools(self, tools: Any, **kwargs: Any) -> Any:
        return self


# -- should_continue --


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        ({"messages": [AIMessage(content="done")]}, NODE_END),
        (
            {
                "messages": [
                    AIMessage(
                        content="",
                        tool_calls=[{"name": "calc", "args": {}, "id": "t1", "type": "tool_call"}],
                    )
                ]
            },
            NODE_TOOLS,
        ),
    ],
)
def test_should_continue_routes(state: dict, expected: str) -> None:
    assert should_continue(state) == expected


# -- invoke_llm --


@pytest.mark.asyncio
async def test_invoke_llm_returns_ai_message() -> None:
    llm = FixedAIMessageModel(response=AIMessage(content="hello"))
    state = {
        "messages": [HumanMessage("hi")],
        "images": [],
        "skill_context": "",
        "knowledge_catalog": "",
    }
    out = await invoke_llm(state, llm)
    assert out["messages"][-1].content == "hello"


@pytest.mark.asyncio
async def test_invoke_llm_appends_knowledge_catalog_to_system_prompt() -> None:
    """knowledge_catalog must appear in the SystemMessage passed to the LLM."""
    llm = FixedAIMessageModel(response=AIMessage(content="ok"))
    catalog = "## Knowledge Base\n\n- **notes.md** (md, project): my notes"
    state = {
        "messages": [HumanMessage("question")],
        "images": [],
        "skill_context": "",
        "knowledge_catalog": catalog,
    }
    await invoke_llm(state, llm)

    system_content = llm.last_messages[0].content
    assert catalog in system_content


@pytest.mark.asyncio
async def test_invoke_llm_skips_knowledge_catalog_when_empty() -> None:
    """Empty knowledge_catalog must not add any extra section to the prompt."""
    llm = FixedAIMessageModel(response=AIMessage(content="ok"))
    state = {
        "messages": [HumanMessage("question")],
        "images": [],
        "skill_context": "",
        "knowledge_catalog": "",
    }
    await invoke_llm(state, llm)

    system_content = llm.last_messages[0].content
    assert "## Knowledge Base" not in system_content


@pytest.mark.asyncio
async def test_invoke_llm_skips_knowledge_catalog_when_absent() -> None:
    """Missing knowledge_catalog key must not raise and must not inject catalog text."""
    llm = FixedAIMessageModel(response=AIMessage(content="ok"))
    state = {
        "messages": [HumanMessage("question")],
        "images": [],
        "skill_context": "",
    }
    await invoke_llm(state, llm)

    system_content = llm.last_messages[0].content
    assert "## Knowledge Base" not in system_content
