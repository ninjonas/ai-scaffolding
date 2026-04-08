from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

from app.domain.entities.message import Message


@dataclass
class Conversation:
    id: str = field(default_factory=lambda: str(uuid4()))
    title: str = ""
    messages: list[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def add_message(self, message: Message) -> None:
        message.conversation_id = self.id
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
