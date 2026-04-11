from typing import Annotated

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.api.dto.knowledge import (
    KnowledgeCatalogEntryDTO,
    KnowledgeFileResponseDTO,
    KnowledgeFileUpdateDTO,
    KnowledgeFileUploadDTO,
    KnowledgeListQueryDTO,
)
from app.infrastructure.mappers.knowledge_file import KnowledgeFileApiMapper
from app.service.knowledge import ERR_FILE_NOT_FOUND, KnowledgeService

log = structlog.get_logger()

KNOWLEDGE_ROUTE_PREFIX = "/api/knowledge"
router = APIRouter(prefix=KNOWLEDGE_ROUTE_PREFIX, tags=["knowledge"])


def get_knowledge_service() -> KnowledgeService:
    from app.shared.di import _container

    return _container.knowledge_service


KnowledgeServiceDep = Annotated[KnowledgeService, Depends(get_knowledge_service)]


@router.post("", response_model=KnowledgeFileResponseDTO)
async def upload_file(
    request: KnowledgeFileUploadDTO,
    knowledge_service: KnowledgeServiceDep,
    background_tasks: BackgroundTasks,
) -> KnowledgeFileResponseDTO:
    log.info(
        "knowledge_upload_request",
        method="POST",
        path=KNOWLEDGE_ROUTE_PREFIX,
        filename=request.filename,
        scope=request.scope,
    )
    entity = await knowledge_service.upload(
        filename=request.filename,
        content=request.content,
        scope=request.scope,
        conversation_id=request.conversation_id,
    )
    background_tasks.add_task(knowledge_service.enrich_metadata, entity.id)
    dto = KnowledgeFileApiMapper.to_response_dto(entity)
    log.info("knowledge_upload_response", file_id=dto.id)
    return dto


@router.get("", response_model=list[KnowledgeCatalogEntryDTO])
async def list_files(
    knowledge_service: KnowledgeServiceDep,
    query: Annotated[KnowledgeListQueryDTO, Depends()],
) -> list[KnowledgeCatalogEntryDTO]:
    log.info(
        "knowledge_list_request",
        method="GET",
        path=KNOWLEDGE_ROUTE_PREFIX,
        scope=query.scope,
        conversation_id=query.conversation_id,
    )
    entities = await knowledge_service.list(
        scope=query.scope, conversation_id=query.conversation_id
    )
    log.info("knowledge_list_response", count=len(entities))
    return [KnowledgeFileApiMapper.to_catalog_entry_dto(e) for e in entities]


@router.get("/{file_id}", response_model=KnowledgeFileResponseDTO)
async def get_file(
    file_id: str,
    knowledge_service: KnowledgeServiceDep,
) -> KnowledgeFileResponseDTO:
    log.info("knowledge_get_request", method="GET", path=KNOWLEDGE_ROUTE_PREFIX, file_id=file_id)
    entity = await knowledge_service.get(file_id)
    if entity is None:
        raise HTTPException(status_code=404, detail=f"{ERR_FILE_NOT_FOUND}{file_id}")
    dto = KnowledgeFileApiMapper.to_response_dto(entity)
    log.info("knowledge_get_response", file_id=file_id)
    return dto


@router.put("/{file_id}", response_model=KnowledgeFileResponseDTO)
async def update_file(
    file_id: str,
    request: KnowledgeFileUpdateDTO,
    knowledge_service: KnowledgeServiceDep,
) -> KnowledgeFileResponseDTO:
    log.info(
        "knowledge_update_request", method="PUT", path=KNOWLEDGE_ROUTE_PREFIX, file_id=file_id
    )
    entity = await knowledge_service.update(
        file_id=file_id,
        name=request.name,
        description=request.description,
        tags=request.tags,
        content=request.content,
    )
    dto = KnowledgeFileApiMapper.to_response_dto(entity)
    log.info("knowledge_update_response", file_id=file_id)
    return dto


@router.delete("/{file_id}", status_code=204)
async def delete_file(
    file_id: str,
    knowledge_service: KnowledgeServiceDep,
) -> None:
    log.info(
        "knowledge_delete_request", method="DELETE", path=KNOWLEDGE_ROUTE_PREFIX, file_id=file_id
    )
    await knowledge_service.delete(file_id)
    log.info("knowledge_delete_response", file_id=file_id)
