import structlog
from langchain_core.language_models import BaseChatModel
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from app.agents.chatbot.nodes import ALL_TOOLS, await_memory_confirm, invoke_llm, should_continue
from app.agents.chatbot.state import ChatbotState
from app.agents.constants import NODE_END, NODE_LLM, NODE_TOOLS

log = structlog.get_logger()

NODE_MEMORY_CONFIRM = "await_memory_confirm"


def route_after_tools(state: ChatbotState) -> str:
    """Route to memory confirmation if results are pending, otherwise back to LLM."""
    if state.get("memory_results"):
        return NODE_MEMORY_CONFIRM
    return NODE_LLM


def create_chatbot_graph(
    llm: BaseChatModel, extra_tools: list | None = None, checkpointer: object | None = None
) -> StateGraph:
    log.info("creating_chatbot_graph")

    all_tools = ALL_TOOLS + (extra_tools or [])
    tool_node = ToolNode(all_tools)

    async def llm_node(state: ChatbotState) -> dict:
        return await invoke_llm(state, llm, extra_tools=extra_tools)

    graph = StateGraph(ChatbotState)
    graph.add_node(NODE_LLM, llm_node)
    graph.add_node(NODE_TOOLS, tool_node)
    graph.add_node(NODE_MEMORY_CONFIRM, await_memory_confirm)

    graph.set_entry_point(NODE_LLM)
    graph.add_conditional_edges(
        NODE_LLM,
        should_continue,
        {NODE_TOOLS: NODE_TOOLS, NODE_END: END},
    )
    graph.add_conditional_edges(
        NODE_TOOLS,
        route_after_tools,
        {NODE_MEMORY_CONFIRM: NODE_MEMORY_CONFIRM, NODE_LLM: NODE_LLM},
    )
    graph.add_edge(NODE_MEMORY_CONFIRM, NODE_LLM)

    log.info("chatbot_graph_created")
    return graph.compile(checkpointer=checkpointer)
