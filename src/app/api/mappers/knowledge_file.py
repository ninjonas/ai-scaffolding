from app.api.dto.knowledge import KnowledgeCatalogEntryDTO, KnowledgeFileResponseDTO
from app.domain.entities.knowledge_file import KnowledgeFile


class KnowledgeFileApiMapper:
    @staticmethod
    def to_response_dto(entity: KnowledgeFile) -> KnowledgeFileResponseDTO:
        return KnowledgeFileResponseDTO(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            content=entity.content,
            tags=entity.tags,
            file_type=entity.file_type,
            scope=entity.scope,
            enriched=entity.enriched,
            conversation_id=entity.conversation_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    @staticmethod
    def to_catalog_entry_dto(entity: KnowledgeFile) -> KnowledgeCatalogEntryDTO:
        return KnowledgeCatalogEntryDTO(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            tags=entity.tags,
            file_type=entity.file_type,
            scope=entity.scope,
            enriched=entity.enriched,
        )
