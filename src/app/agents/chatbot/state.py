from langgraph.graph import MessagesState


class ChatbotState(MessagesState):
    images: list[str]
    skill_context: str
    knowledge_catalog: str
