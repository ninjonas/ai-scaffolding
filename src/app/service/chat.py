import asyncio
import time

import structlog

from app.agents.orchestrator import AgentBroker
from app.agents.tools.image import optimize_images_b64
from app.domain.entities.conversation import Conversation
from app.domain.entities.knowledge_file import SCOPE_CONVERSATION, SCOPE_PROJECT, KnowledgeFile
from app.domain.entities.message import Message, MessageRole
from app.infrastructure.mappers.message_index import MessageIndexMapper
from app.infrastructure.unit_of_work import SQLAlchemyUnitOfWork
from app.infrastructure.vector.message_indexer import MessageIndexer
from app.service.knowledge import KnowledgeService
from app.service.knowledge_context import build_conversation_context, build_project_context
from app.shared.field_keys import FIELD_KEY_INTERRUPT, FIELD_KEY_INTERRUPT_TYPE

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
    ) -> Message | dict:
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
            await uow.conversations.save(conversation)
            await uow.commit()

        uploaded_files = await self._index_images(
            user_message.images,
            image_filenames,
            conversation.id,
        )
        await asyncio.gather(
            *[self._knowledge_service.enrich_metadata(kf.id) for kf in uploaded_files]
        )

        project_files, conversation_files = await asyncio.gather(
            self._knowledge_service.list(scope=SCOPE_PROJECT),
            self._knowledge_service.list(
                scope=SCOPE_CONVERSATION,
                conversation_id=conversation.id,
            ),
        )
        knowledge_context = build_project_context(project_files) + build_conversation_context(
            conversation_files
        )
        log.info(
            "knowledge_context_attached",
            conversation_id=conversation.id,
            project_file_count=len(project_files),
            conversation_file_count=len(conversation_files),
        )

        response = await self._broker.chat_response(
            content,
            optimized,
            conversation_id=conversation.id,
            knowledge_context=knowledge_context,
            message_count=len(conversation.messages),
        )

        if response.get(FIELD_KEY_INTERRUPT):
            log.info(
                "send_message_interrupted",
                conversation_id=conversation.id,
                interrupt_type=response[FIELD_KEY_INTERRUPT].get(FIELD_KEY_INTERRUPT_TYPE),
            )
            return response

        raw_content = response["content"]
        if not raw_content:
            log.warning("chat_empty_response", conversation_id=conversation.id)
            raw_content = "Sorry, I didn't get a response. Please try again."
        assistant_message = Message(
            content=raw_content,
            role=MessageRole.ASSISTANT,
            tool_calls=response.get("tool_calls", []),
        )

        async with self._uow as uow:
            conversation.add_message(assistant_message)
            await uow.conversations.save(conversation)
            await uow.commit()

        if self._message_indexer:
            await self._message_indexer.index(**MessageIndexMapper.to_index_params(user_message))
            await self._message_indexer.index(
                **MessageIndexMapper.to_index_params(assistant_message)
            )

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

    async def _index_images(
        self,
        images: list[str],
        filenames: list[str] | None,
        conversation_id: str,
    ) -> list[KnowledgeFile]:
        """Upload images to knowledge base before the agent sees them."""
        if not images:
            return []
        names = filenames or []
        uploaded = []
        for i, img_b64 in enumerate(images):
            filename = names[i] if i < len(names) else f"image_{i + 1}.jpg"
            kf = await self._knowledge_service.upload(
                filename=filename,
                content=img_b64,
                scope=SCOPE_CONVERSATION,
                conversation_id=conversation_id,
            )
            uploaded.append(kf)
        return uploaded

    async def _get_or_create(
        self,
        uow,
        conversation_id: str | None,
    ) -> Conversation:
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
