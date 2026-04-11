from app.api.dto.chat import ChatResponseDTO, ToolCallDTO
from app.domain.entities.message import Message


class ChatMapper:
    @staticmethod
    def to_response_dto(message: Message, conversation_id: str) -> ChatResponseDTO:
        tool_calls = [
            ToolCallDTO(name=tc.get("name", ""), args=tc.get("args", {}))
            for tc in message.tool_calls
        ]
        return ChatResponseDTO(
            message=message.content,
            conversation_id=conversation_id,
            tool_calls=tool_calls,
        )
