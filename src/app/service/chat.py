import time
from typing import Any

import structlog

from app.domain.entities.conversation import Conversation
from app.domain.entities.message import Message, MessageRole
from app.infrastructure.unit_of_work import SQLAlchemyUnitOfWork

log = structlog.get_logger()


class ChatService:
    def __init__(self, agent_graph: Any, unit_of_work: SQLAlchemyUnitOfWork) -> None:
        self._agent_graph = agent_graph
        self._uow = unit_of_work

    async def send_message(
        self,
        content: str,
        conversation_id: str | None = None,
        images: list[str] | None = None,
    ) -> Message:
        log.info(
            "send_message_start",
            conversation_id=conversation_id,
            has_images=bool(images),
            content_length=len(content),
        )
        start = time.monotonic()

        async with self._uow as uow:
            conversation = await self._get_or_create(uow, conversation_id)

            user_message = Message(
                content=content,
                role=MessageRole.USER,
                images=images or [],
            )
            conversation.add_message(user_message)

            response = await self._invoke_agent(content, images or [], conversation)

            assistant_message = Message(
                content=response["content"],
                role=MessageRole.ASSISTANT,
                tool_calls=response.get("tool_calls", []),
            )
            conversation.add_message(assistant_message)

            await uow.conversations.save(conversation)
            await uow.commit()

        duration = time.monotonic() - start
        log.info(
            "send_message_complete",
            conversation_id=conversation.id,
            duration_s=round(duration, 3),
            response_length=len(assistant_message.content),
        )
        return assistant_message

    async def _get_or_create(self, uow, conversation_id: str | None) -> Conversation:
        if conversation_id:
            convo = await uow.conversations.get_by_id(conversation_id)
            if convo:
                log.debug("conversation_loaded", id=conversation_id)
                return convo
            log.warning("conversation_not_found", id=conversation_id)

        conversation = Conversation()
        log.info("conversation_created", id=conversation.id)
        return conversation

    async def _invoke_agent(
        self,
        content: str,
        images: list[str],
        conversation: Conversation,
    ) -> dict:
        log.info(
            "invoking_agent",
            conversation_id=conversation.id,
            message_count=len(conversation.messages),
        )
        start = time.monotonic()

        result = await self._agent_graph.ainvoke(
            {
                "messages": [{"role": MessageRole.USER, "content": content}],
                "images": images,
            }
        )

        duration = time.monotonic() - start
        last_message = result["messages"][-1]
        log.info(
            "agent_invocation_complete",
            conversation_id=conversation.id,
            duration_s=round(duration, 3),
        )

        return {
            "content": last_message.content,
            "tool_calls": getattr(last_message, "tool_calls", []),
        }
