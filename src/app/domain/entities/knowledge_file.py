from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

SCOPE_PROJECT = "project"
SCOPE_CONVERSATION = "conversation"


@dataclass
class KnowledgeFile:
    name: str
    description: str
    content: str
    file_type: str  # "md" | "txt" | "json" | "yml"
    scope: str  # "project" | "conversation"
    filename: str = ""
    tags: list[str] = field(default_factory=list)
    enriched: bool = False
    id: str = field(default_factory=lambda: str(uuid4()))
    conversation_id: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
