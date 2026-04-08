from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import uuid4


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


@dataclass
class Message:
    content: str
    role: MessageRole
    id: str = field(default_factory=lambda: str(uuid4()))
    conversation_id: str = ""
    images: list[str] = field(default_factory=list)
    tool_calls: list[dict] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
