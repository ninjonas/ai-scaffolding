import time

import structlog
from langchain_core.messages import SystemMessage

from app.agents.constants import AGENT_CHATBOT, AGENT_RESEARCHER, PROMPTS_DIR
from app.agents.supervisor.state import SupervisorState

log = structlog.get_logger()


async def route_task(state: SupervisorState, llm) -> dict:
    log.info("supervisor_routing", message_count=len(state["messages"]))

    route_prompt = (PROMPTS_DIR / "supervisor" / "route.md").read_text()
    messages = [SystemMessage(content=route_prompt), *state["messages"]]
    start = time.monotonic()
    response = await llm.ainvoke(messages)

    log.info("supervisor_llm_response", duration_s=round(time.monotonic() - start, 3))

    next_agent = response.content.strip().lower()
    if next_agent not in (AGENT_CHATBOT, AGENT_RESEARCHER):
        log.warning("supervisor_invalid_route", raw=next_agent)
        next_agent = AGENT_CHATBOT

    log.info("supervisor_routed", next_agent=next_agent)
    return {"next_agent": next_agent}


def decide_next(state: SupervisorState) -> str:
    next_agent = state.get("next_agent", AGENT_CHATBOT)
    log.debug("supervisor_decide_next", next_agent=next_agent)
    has_response = next_agent != AGENT_CHATBOT
    log.debug("supervisor_decided", next_agent=next_agent, has_response=has_response)
    return next_agent
