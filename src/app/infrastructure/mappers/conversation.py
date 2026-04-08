from app.domain.entities.conversation import Conversation
from app.domain.entities.message import Message, MessageRole
from app.infrastructure.models.conversation import ConversationModel
from app.infrastructure.models.message import MessageModel


class ConversationDataMapper:
    @staticmethod
    def to_domain(model: ConversationModel) -> Conversation:
        messages = [
            Message(
                content=msg.content,
                role=MessageRole(msg.role),
                id=msg.id,
                conversation_id=msg.conversation_id,
                images=msg.images,
                tool_calls=msg.tool_calls,
                created_at=msg.created_at,
            )
            for msg in model.messages
        ]
        return Conversation(
            id=model.id,
            title=model.title,
            messages=messages,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(entity: Conversation) -> ConversationModel:
        model = ConversationModel(
            id=entity.id,
            title=entity.title,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
        model.messages = [ConversationDataMapper._message_to_model(msg) for msg in entity.messages]
        return model

    @staticmethod
    def _message_to_model(msg: Message) -> MessageModel:
        model = MessageModel(
            id=msg.id,
            conversation_id=msg.conversation_id,
            content=msg.content,
            role=msg.role.value,
            created_at=msg.created_at,
        )
        model.images = msg.images
        model.tool_calls = msg.tool_calls
        return model
