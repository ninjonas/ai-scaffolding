import time

import structlog

from app.agents.orchestrator import AgentBroker
from app.agents.tools.knowledge import build_knowledge_catalog
from app.domain.entities.conversation import Conversation
from app.domain.entities.knowledge_file import SCOPE_CONVERSATION, SCOPE_PROJECT
from app.domain.entities.message import Message, MessageRole
from app.infrastructure.unit_of_work import SQLAlchemyUnitOfWork
from app.service.knowledge import KnowledgeService

log = structlog.get_logger()


class ChatService:
    def __init__(
        self,
        broker: AgentBroker,
        unit_of_work: SQLAlchemyUnitOfWork,
        knowledge_service: KnowledgeService,
    ) -> None:
        self._broker = broker
        self._uow = unit_of_work
        self._knowledge_service = knowledge_service

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
        start = time.monotonic()  # timing: operation-level

        async with self._uow as uow:
            conversation = await self._get_or_create(uow, conversation_id)

            project_catalog = await self._knowledge_service.get_catalog(scope=SCOPE_PROJECT)
            conversation_catalog = await self._knowledge_service.get_catalog(
                scope=SCOPE_CONVERSATION,
                conversation_id=conversation.id,
            )
            catalog_entries = project_catalog + conversation_catalog
            knowledge_catalog = build_knowledge_catalog(catalog_entries)
            log.debug(
                "knowledge_catalog_built",
                conversation_id=conversation.id,
                project_count=len(project_catalog),
                conversation_count=len(conversation_catalog),
            )

            user_message = Message(
                content=content,
                role=MessageRole.USER,
                images=images or [],
            )
            conversation.add_message(user_message)

            response = await self._broker.chat_response(
                content,
                images or [],
                knowledge_catalog=knowledge_catalog,
                conversation_id=conversation.id,
                message_count=len(conversation.messages),
            )

            assistant_message = Message(
                content=response["content"],
                role=MessageRole.ASSISTANT,
                tool_calls=response.get("tool_calls", []),
            )
            conversation.add_message(assistant_message)

            await uow.conversations.save(conversation)
            await uow.commit()

        duration = time.monotonic() - start  # timing: operation-level
        log.info(
            "send_message_complete",
            conversation_id=conversation.id,
            duration_s=round(duration, 3),
            response_length=len(assistant_message.content),
        )
        return assistant_message

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
