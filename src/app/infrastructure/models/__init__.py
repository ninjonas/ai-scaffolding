from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from app.infrastructure.models.conversation import ConversationModel  # noqa: E402, F401
from app.infrastructure.models.knowledge_file import KnowledgeFileModel  # noqa: E402, F401
from app.infrastructure.models.message import MessageModel  # noqa: E402, F401
