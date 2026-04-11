from typing import Annotated

import structlog
from fastapi import APIRouter, Depends

from app.api.dto.chat import ChatRequestDTO, ChatResponseDTO
from app.infrastructure.mappers.chat import ChatMapper
from app.service.chat import ChatService

log = structlog.get_logger()

CHAT_ROUTE_PREFIX = "/api/chat"
router = APIRouter(prefix=CHAT_ROUTE_PREFIX, tags=["chat"])


def get_chat_service() -> ChatService:
    from app.shared.di import _container

    return _container.chat_service


ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]


@router.post("", response_model=ChatResponseDTO)
async def send_message(
    request: ChatRequestDTO,
    chat_service: ChatServiceDep,
) -> ChatResponseDTO:
    log.info(
        "chat_request",
        method="POST",
        path=CHAT_ROUTE_PREFIX,
        conversation_id=request.conversation_id,
        has_images=bool(request.images),
    )

    response_message = await chat_service.send_message(
        content=request.message,
        conversation_id=request.conversation_id,
        images=request.images,
        image_filenames=request.image_filenames,
        knowledge_file_ids=request.knowledge_file_ids,
    )

    dto = ChatMapper.to_response_dto(
        response_message,
        conversation_id=response_message.conversation_id,
    )
    log.info("chat_response_sent", conversation_id=dto.conversation_id)
    return dto
