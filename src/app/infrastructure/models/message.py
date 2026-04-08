from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.entities.message import MessageRole
from app.infrastructure.models import Base

if TYPE_CHECKING:
    from app.infrastructure.models.conversation import ConversationModel


class MessageModel(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    conversation_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("conversations.id"),
    )
    content: Mapped[str] = mapped_column(Text, default="")
    role: Mapped[str] = mapped_column(String, default=MessageRole.USER)
    images_json: Mapped[str] = mapped_column(Text, default="[]")
    tool_calls_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    conversation: Mapped[ConversationModel] = relationship(
        back_populates="messages",
    )

    @property
    def images(self) -> list[str]:
        return json.loads(self.images_json)

    @images.setter
    def images(self, value: list[str]) -> None:
        self.images_json = json.dumps(value)

    @property
    def tool_calls(self) -> list[dict]:
        return json.loads(self.tool_calls_json)

    @tool_calls.setter
    def tool_calls(self, value: list[dict]) -> None:
        self.tool_calls_json = json.dumps(value)
