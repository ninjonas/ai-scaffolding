from app.domain.entities.message import Message


class MessageIndexMapper:
    @staticmethod
    def to_index_params(message: Message) -> dict:
        """Map a Message entity to keyword arguments for MessageIndexer.index."""
        return {
            "message_id": message.id,
            "content": message.content,
            "role": str(message.role),
            "conversation_id": message.conversation_id,
            "created_at": message.created_at.isoformat(),
        }
