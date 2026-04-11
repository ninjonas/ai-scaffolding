import structlog
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from app.agents.chatbot.graph import create_chatbot_graph
from app.agents.constants import AGENT_CHATBOT, AGENT_RESEARCHER, NODE_ROUTER
from app.agents.researcher.graph import create_researcher_graph
from app.agents.supervisor.nodes import decide_next, route_task
from app.agents.supervisor.state import SupervisorState

log = structlog.get_logger()


def create_supervisor_graph(
    llm: ChatOpenAI, extra_tools: list | None = None, checkpointer: object | None = None
) -> StateGraph:
    log.info("creating_supervisor_graph")

    chatbot = create_chatbot_graph(llm, extra_tools=extra_tools)
    researcher = create_researcher_graph(llm)

    async def router_node(state: SupervisorState) -> dict:
        return await route_task(state, llm)

    async def chatbot_node(state: SupervisorState) -> dict:
        log.info("supervisor_delegating", agent=AGENT_CHATBOT)
        result = await chatbot.ainvoke(
            {
                "messages": state["messages"],
                "images": state.get("images", []),
                "skill_context": "",
            }
        )
        return {"messages": result["messages"]}

    async def researcher_node(state: SupervisorState) -> dict:
        log.info("supervisor_delegating", agent=AGENT_RESEARCHER)
        result = await researcher.ainvoke(
            {
                "messages": state["messages"],
                "query": "",
                "findings": [],
            }
        )
        return {"messages": result["messages"]}

    graph = StateGraph(SupervisorState)
    graph.add_node(NODE_ROUTER, router_node)
    graph.add_node(AGENT_CHATBOT, chatbot_node)
    graph.add_node(AGENT_RESEARCHER, researcher_node)

    graph.set_entry_point(NODE_ROUTER)
    graph.add_conditional_edges(
        NODE_ROUTER,
        decide_next,
        {AGENT_CHATBOT: AGENT_CHATBOT, AGENT_RESEARCHER: AGENT_RESEARCHER},
    )
    graph.add_edge(AGENT_CHATBOT, END)
    graph.add_edge(AGENT_RESEARCHER, END)

    log.info("supervisor_graph_created")
    return graph.compile(checkpointer=checkpointer)
