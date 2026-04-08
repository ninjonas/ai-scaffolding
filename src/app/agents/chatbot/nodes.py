import time

import structlog
from langchain_core.messages import AIMessage, SystemMessage

from app.agents.chatbot.state import ChatbotState
from app.agents.constants import AGENT_CHATBOT, NODE_END, NODE_TOOLS, PROMPTS_DIR, RULES_DIR
from app.agents.skills.analyze_image.tools import describe_image
from app.agents.skills.calculator.tools import calculate
from app.agents.skills.file_ops.tools import list_directory, read_file
from app.agents.skills.loader import build_skill_catalog, load_skill, read_skill_file
from app.agents.skills.web_search.tools import search_web

log = structlog.get_logger()

ALL_TOOLS = [
    describe_image,
    search_web,
    read_file,
    list_directory,
    calculate,
    load_skill,
    read_skill_file,
]


def _build_system_prompt() -> str:
    system = (PROMPTS_DIR / "system.md").read_text()
    persona = (PROMPTS_DIR / AGENT_CHATBOT / "persona.md").read_text()
    output_fmt = (PROMPTS_DIR / "output_format.md").read_text()
    rules = [p.read_text() for p in sorted(RULES_DIR.glob("*.md"))]

    catalog = build_skill_catalog()
    skill_list = "\n".join(f"- **{s['name']}**: {s['description']}" for s in catalog)
    skill_hint = "Use the `load_skill` tool to get detailed instructions."
    skills_section = f"## Available Skills\n\n{skill_list}\n\n{skill_hint}"

    return "\n\n".join([system, persona, *rules, skills_section, output_fmt])


async def invoke_llm(state: ChatbotState, llm) -> dict:
    log.info("chatbot_invoke_llm", message_count=len(state["messages"]))

    system_prompt = _build_system_prompt()
    if state.get("skill_context"):
        system_prompt += f"\n\n## Loaded Skill Context\n\n{state['skill_context']}"

    messages = [SystemMessage(content=system_prompt), *state["messages"]]
    llm_with_tools = llm.bind_tools(ALL_TOOLS)
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
