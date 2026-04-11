from langgraph.graph import MessagesState


class SupervisorState(MessagesState):
    images: list[str]
    next_agent: str
