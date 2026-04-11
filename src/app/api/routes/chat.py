from typing import Annotated

import structlog
from fastapi import APIRouter, Depends

from app.api.dto.chat import ChatRequestDTO, ChatResponseDTO, ResumeRequestDTO
from app.infrastructure.mappers.chat import ChatMapper
from app.service.chat import ChatService
from app.shared.field_keys import FIELD_KEY_INTERRUPT, FIELD_KEY_INTERRUPT_TYPE

log = structlog.get_logger()

CHAT_ROUTE_PREFIX = "/api/chat"
HTTP_METHOD_POST = "POST"

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
        method=HTTP_METHOD_POST,
        path=CHAT_ROUTE_PREFIX,
        conversation_id=request.conversation_id,
        has_images=bool(request.images),
    )

    result = await chat_service.send_message(
        content=request.message,
        conversation_id=request.conversation_id,
        images=request.images,
        image_filenames=request.image_filenames,
        knowledge_file_ids=request.knowledge_file_ids,
    )

    if isinstance(result, dict) and result.get(FIELD_KEY_INTERRUPT):
        interrupt_data = result[FIELD_KEY_INTERRUPT]
        dto = ChatResponseDTO(
            message="",
            conversation_id=request.conversation_id or "",
            interrupt=interrupt_data,
        )
        log.info(
            "chat_interrupt_sent",
            conversation_id=request.conversation_id,
            interrupt_type=interrupt_data.get(FIELD_KEY_INTERRUPT_TYPE),
        )
        return dto

    dto = ChatMapper.to_response_dto(
        result,
        conversation_id=result.conversation_id,
    )
    log.info("chat_response_sent", conversation_id=dto.conversation_id)
    return dto


@router.post("/{conversation_id}/resume", response_model=ChatResponseDTO)
async def resume_conversation(
    conversation_id: str,
    request: ResumeRequestDTO,
    chat_service: ChatServiceDep,
) -> ChatResponseDTO:
    log.info(
        "chat_resume_request",
        method=HTTP_METHOD_POST,
        path=f"{CHAT_ROUTE_PREFIX}/{conversation_id}/resume",
        conversation_id=conversation_id,
        approved=request.approved,
    )

    result = await chat_service.resume(conversation_id, request.approved)

    if result.get(FIELD_KEY_INTERRUPT):
        dto = ChatResponseDTO(
            message="",
            conversation_id=conversation_id,
            interrupt=result[FIELD_KEY_INTERRUPT],
        )
    else:
        content = result.get("content", "")
        tool_calls = result.get("tool_calls", [])
        dto = ChatResponseDTO(
            message=content, conversation_id=conversation_id, tool_calls=tool_calls
        )
    log.info("chat_resume_response_sent", conversation_id=conversation_id)
    return dto
