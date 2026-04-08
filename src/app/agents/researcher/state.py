from langgraph.graph import MessagesState


class ResearcherState(MessagesState):
    query: str
    findings: list[str]
