from app.api.dto.knowledge import KnowledgeCatalogEntryDTO, KnowledgeFileResponseDTO
from app.domain.entities.knowledge_file import KnowledgeFile
from app.infrastructure.models.knowledge_file import KnowledgeFileModel


class KnowledgeFileDataMapper:
    @staticmethod
    def to_domain(model: KnowledgeFileModel) -> KnowledgeFile:
        return KnowledgeFile(
            id=model.id,
            name=model.name,
            description=model.description,
            content=model.content,
            file_type=model.file_type,
            scope=model.scope,
            tags=model.tags,
            conversation_id=model.conversation_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(entity: KnowledgeFile) -> KnowledgeFileModel:
        model = KnowledgeFileModel(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            content=entity.content,
            file_type=entity.file_type,
            scope=entity.scope,
            conversation_id=entity.conversation_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
        model.tags = entity.tags
        return model

    @staticmethod
    def to_response_dto(entity: KnowledgeFile) -> KnowledgeFileResponseDTO:
        return KnowledgeFileResponseDTO(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            tags=entity.tags,
            file_type=entity.file_type,
            scope=entity.scope,
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
        )
