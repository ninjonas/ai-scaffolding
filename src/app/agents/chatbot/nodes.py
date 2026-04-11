import time

import structlog
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.types import interrupt

from app.agents.chatbot.state import ChatbotState
from app.agents.constants import (
    AGENT_CHATBOT,
    NODE_END,
    NODE_TOOLS,
    PROMPT_GLOB_RULES,
    PROMPT_OUTPUT_FORMAT,
    PROMPT_PERSONA,
    PROMPT_SYSTEM,
    PROMPTS_DIR,
    RULES_DIR,
)
from app.agents.skills.calculator.tools import calculate
from app.agents.skills.file_ops.tools import list_directory, read_file
from app.agents.skills.loader import build_skill_catalog, load_skill, read_skill_file
from app.agents.skills.web_search.tools import search_web
from app.agents.tools.image import BASE64_JPEG_PREFIX
from app.shared.field_keys import CONTENT_TYPE_IMAGE_URL, CONTENT_TYPE_TEXT

log = structlog.get_logger()

ALL_TOOLS = [
    search_web,
    read_file,
    list_directory,
    calculate,
    load_skill,
    read_skill_file,
]


def _build_system_prompt() -> str:
    system = (PROMPTS_DIR / PROMPT_SYSTEM).read_text()
    persona = (PROMPTS_DIR / AGENT_CHATBOT / PROMPT_PERSONA).read_text()
    output_fmt = (PROMPTS_DIR / PROMPT_OUTPUT_FORMAT).read_text()
    rules = [p.read_text() for p in sorted(RULES_DIR.glob(PROMPT_GLOB_RULES))]

    catalog = build_skill_catalog()
    skill_list = "\n".join(f"- **{s['name']}**: {s['description']}" for s in catalog)
    skill_hint = "Use the `load_skill` tool to get detailed instructions."
    skills_section = f"## Available Skills\n\n{skill_list}\n\n{skill_hint}"

    return "\n\n".join([system, persona, *rules, skills_section, output_fmt])


async def invoke_llm(state: ChatbotState, llm, extra_tools: list | None = None) -> dict:
    log.info("chatbot_invoke_llm", message_count=len(state["messages"]))

    system_prompt = _build_system_prompt()
    if state.get("skill_context"):
        system_prompt += f"\n\n## Loaded Skill Context\n\n{state['skill_context']}"

    chat_messages = list(state["messages"])
    images = state.get("images") or []
    is_first_pass = not any(isinstance(m, AIMessage) for m in chat_messages)
    if images and is_first_pass:
        log.info("chatbot_attaching_images", count=len(images))
        last_human = next(
            (
                i
                for i in range(len(chat_messages) - 1, -1, -1)
                if isinstance(chat_messages[i], HumanMessage)
            ),
            None,
        )
        if last_human is not None:
            text = chat_messages[last_human].content or ""
            content_parts = [{"type": CONTENT_TYPE_TEXT, "text": text}]
            for img in images:
                content_parts.append(
                    {
                        "type": CONTENT_TYPE_IMAGE_URL,
                        "image_url": {"url": f"{BASE64_JPEG_PREFIX}{img}"},
                    }
                )
            chat_messages[last_human] = HumanMessage(content=content_parts)

    tools = ALL_TOOLS + (extra_tools or [])
    messages = [SystemMessage(content=system_prompt), *chat_messages]
    llm_with_tools = llm.bind_tools(tools)
    start = time.monotonic()
    response = await llm_with_tools.ainvoke(messages)

    log.info(
        "chatbot_llm_response",
        has_tool_calls=bool(response.tool_calls),
        content_length=len(response.content) if response.content else 0,
        duration_s=round(time.monotonic() - start, 3),
    )
    return {"messages": [response]}


def should_continue(state: ChatbotState) -> str:
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        log.debug("chatbot_routing_to_tools", tool_count=len(last.tool_calls))
        return NODE_TOOLS
    return NODE_END


async def await_memory_confirm(state: ChatbotState) -> dict:
    results = state.get("memory_results")
    if not results:
        return {}
    confirmed = interrupt(
        {
            "type": "memory_confirm",
            "results": results,
            "prompt": "I found relevant context from past conversations. Use it?",
        }
    )
    if confirmed:
        context = "\n\n".join(
            f"[{r['conversation_id']} | {r['created_at']}]\n{r['excerpt']}" for r in results
        )
        return {
            "messages": [SystemMessage(content=f"## Past Context\n\n{context}")],
            "memory_results": [],
            "memory_confirmed": True,
        }
    return {"memory_results": [], "memory_confirmed": False}
