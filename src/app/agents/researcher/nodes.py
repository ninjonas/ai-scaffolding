import time

import structlog
from langchain_core.messages import AIMessage, SystemMessage

from app.agents.constants import AGENT_RESEARCHER, NODE_END, NODE_TOOLS, PROMPTS_DIR, RULES_DIR
from app.agents.researcher.state import ResearcherState
from app.agents.skills.web_search.tools import search_web

log = structlog.get_logger()

RESEARCHER_TOOLS = [search_web]


def _build_system_prompt() -> str:
    system = (PROMPTS_DIR / "system.md").read_text()
    persona = (PROMPTS_DIR / AGENT_RESEARCHER / "persona.md").read_text()
    output_fmt = (PROMPTS_DIR / "output_format.md").read_text()
    rules = [p.read_text() for p in sorted(RULES_DIR.glob("*.md"))]
    return "\n\n".join([system, persona, *rules, output_fmt])


async def invoke_researcher(state: ResearcherState, llm) -> dict:
    log.info("researcher_invoke_llm", message_count=len(state["messages"]))

    system_prompt = _build_system_prompt()
    messages = [SystemMessage(content=system_prompt), *state["messages"]]
    llm_with_tools = llm.bind_tools(RESEARCHER_TOOLS)
    start = time.monotonic()
    response = await llm_with_tools.ainvoke(messages)

    log.info(
        "researcher_llm_response",
        has_tool_calls=bool(response.tool_calls),
        content_length=len(response.content) if response.content else 0,
        duration_s=round(time.monotonic() - start, 3),
    )
    return {"messages": [response]}


def should_continue(state: ResearcherState) -> str:
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        log.debug("researcher_routing_to_tools", tool_count=len(last.tool_calls))
        return NODE_TOOLS
    return NODE_END
