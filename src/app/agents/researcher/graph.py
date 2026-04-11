import structlog
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from app.agents.constants import NODE_END, NODE_LLM, NODE_TOOLS
from app.agents.researcher.nodes import (
    RESEARCHER_TOOLS,
    invoke_researcher,
    should_continue,
)
from app.agents.researcher.state import ResearcherState

log = structlog.get_logger()


def create_researcher_graph(llm: ChatOpenAI) -> StateGraph:
    log.info("creating_researcher_graph")

    tool_node = ToolNode(RESEARCHER_TOOLS)

    async def llm_node(state: ResearcherState) -> dict:
        return await invoke_researcher(state, llm)

    graph = StateGraph(ResearcherState)
    graph.add_node(NODE_LLM, llm_node)
    graph.add_node(NODE_TOOLS, tool_node)

    graph.set_entry_point(NODE_LLM)
    graph.add_conditional_edges(
        NODE_LLM,
        should_continue,
        {NODE_TOOLS: NODE_TOOLS, NODE_END: END},
    )
    graph.add_edge(NODE_TOOLS, NODE_LLM)

    log.info("researcher_graph_created")
    return graph.compile()
