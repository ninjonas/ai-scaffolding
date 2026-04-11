from typing import Annotated

from langgraph.graph import MessagesState


class ChatbotState(MessagesState):
    images: list[str]
    skill_context: str
    # memory_results: overwrite reducer (b replaces a) so nodes can clear the list
    memory_results: Annotated[list[dict], lambda a, b: b]
    memory_confirmed: bool | None
