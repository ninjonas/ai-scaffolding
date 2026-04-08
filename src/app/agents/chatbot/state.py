from langgraph.graph import MessagesState


class ChatbotState(MessagesState):
    images: list[str]
    skill_context: str
