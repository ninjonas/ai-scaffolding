import asyncio
import time

import structlog

from app.agents.orchestrator import AgentBroker
from app.agents.tools.image import optimize_images_b64
from app.domain.entities.conversation import Conversation
from app.domain.entities.knowledge_file import SCOPE_CONVERSATION
from app.domain.entities.message import Message, MessageRole
from app.infrastructure.unit_of_work import SQLAlchemyUnitOfWork
from app.infrastructure.vector.message_indexer import MessageIndexer
from app.service.knowledge import KnowledgeService

log = structlog.get_logger()


class ChatService:
    def __init__(
        self,
        broker: AgentBroker,
        unit_of_work: SQLAlchemyUnitOfWork,
        knowledge_service: KnowledgeService,
        message_indexer: MessageIndexer | None = None,
    ) -> None:
        self._broker = broker
        self._uow = unit_of_work
        self._knowledge_service = knowledge_service
        self._message_indexer = message_indexer

    async def send_message(
        self,
        content: str,
        conversation_id: str | None = None,
        images: list[str] | None = None,
        image_filenames: list[str] | None = None,
        knowledge_file_ids: list[str] | None = None,
    ) -> Message:
        log.info(
            "send_message_start",
            conversation_id=conversation_id,
            has_images=bool(images),
            content_length=len(content),
            knowledge_file_count=len(knowledge_file_ids or []),
        )
        start = time.monotonic()  # timing: operation-level

        optimized = optimize_images_b64(images) if images else []

        async with self._uow as uow:
            conversation = await self._get_or_create(uow, conversation_id)

            user_message = Message(
                content=content,
                role=MessageRole.USER,
                images=optimized,
            )
            conversation.add_message(user_message)

            response = await self._broker.chat_response(
                content,
                optimized,
                conversation_id=conversation.id,
                message_count=len(conversation.messages),
            )

            raw_content = response["content"]
            if not raw_content:
                log.warning("chat_empty_response", conversation_id=conversation.id)
                raw_content = "Sorry, I didn't get a response. Please try again."
            assistant_message = Message(
                content=raw_content,
                role=MessageRole.ASSISTANT,
                tool_calls=response.get("tool_calls", []),
            )
            conversation.add_message(assistant_message)

            await uow.conversations.save(conversation)
            await uow.commit()

        if self._message_indexer:
            await self._message_indexer.index(
                user_message.id, content, MessageRole.USER,
                conversation.id, user_message.created_at,
            )
            await self._message_indexer.index(
                assistant_message.id, raw_content, MessageRole.ASSISTANT,
                conversation.id, assistant_message.created_at,
            )

        uploaded_files = []
        filenames = image_filenames or []
        for i, img_b64 in enumerate(user_message.images):
            filename = filenames[i] if i < len(filenames) else f"image_{i + 1}.jpg"
            kf = await self._knowledge_service.upload(
                filename=filename,
                content=img_b64,
                scope=SCOPE_CONVERSATION,
                conversation_id=conversation.id,
            )
            uploaded_files.append(kf)

        _enrich_tasks = [
            asyncio.create_task(self._knowledge_service.enrich_metadata(kf.id))
            for kf in uploaded_files
        ]

        duration = time.monotonic() - start  # timing: operation-level
        log.info(
            "send_message_complete",
            conversation_id=conversation.id,
            duration_s=round(duration, 3),
            response_length=len(assistant_message.content),
        )
        return assistant_message

    async def resume(self, conversation_id: str, approved: bool) -> dict:
        """Resume a paused conversation thread.

        Args:
            conversation_id: The thread to resume.
            approved: Whether the pending action is approved.

        Returns:
            Dict with 'content' and 'tool_calls' keys from the agent.
        """
        log.info("resume_start", conversation_id=conversation_id, approved=approved)
        result = await self._broker.resume(conversation_id, approved)
        log.info("resume_complete", conversation_id=conversation_id)
        return result

    async def _get_or_create(self, uow, conversation_id: str | None) -> Conversation:
        log.debug("get_or_create_conversation", conversation_id=conversation_id)
        if conversation_id:
            convo = await uow.conversations.get_by_id(conversation_id)
            if convo:
                log.debug("conversation_loaded", id=conversation_id)
                return convo
            log.warning("conversation_not_found", id=conversation_id)

        conversation = Conversation()
        log.info("conversation_created", id=conversation.id)
        return conversation
