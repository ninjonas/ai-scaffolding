import structlog
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from app.agents.chatbot.nodes import ALL_TOOLS, invoke_llm, should_continue
from app.agents.chatbot.state import ChatbotState
from app.agents.constants import NODE_END, NODE_LLM, NODE_TOOLS

log = structlog.get_logger()


def create_chatbot_graph(
    llm: ChatOpenAI, extra_tools: list | None = None, checkpointer: object | None = None
) -> StateGraph:
    log.info("creating_chatbot_graph")

    all_tools = ALL_TOOLS + (extra_tools or [])
    tool_node = ToolNode(all_tools)

    async def llm_node(state: ChatbotState) -> dict:
        return await invoke_llm(state, llm, extra_tools=extra_tools)

    graph = StateGraph(ChatbotState)
    graph.add_node(NODE_LLM, llm_node)
    graph.add_node(NODE_TOOLS, tool_node)

    graph.set_entry_point(NODE_LLM)
    graph.add_conditional_edges(
        NODE_LLM,
        should_continue,
        {NODE_TOOLS: NODE_TOOLS, NODE_END: END},
    )
    graph.add_edge(NODE_TOOLS, NODE_LLM)

    log.info("chatbot_graph_created")
    return graph.compile(checkpointer=checkpointer)
