from app.domain.entities.knowledge_file import KnowledgeFile
from app.infrastructure.models.knowledge_file import KnowledgeFileModel
from app.shared.field_keys import (
    FIELD_KEY_DESCRIPTION,
    FIELD_KEY_FILE_TYPE,
    FIELD_KEY_ID,
    FIELD_KEY_NAME,
    FIELD_KEY_SCOPE,
)

FIELD_TAGS = "tags"


class KnowledgeFileDataMapper:
    @staticmethod
    def to_domain(model: KnowledgeFileModel) -> KnowledgeFile:
        return KnowledgeFile(
            id=model.id,
            name=model.name,
            filename=model.filename,
            description=model.description,
            content=model.content,
            file_type=model.file_type,
            scope=model.scope,
            tags=model.tags,
            enriched=model.enriched,
            conversation_id=model.conversation_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(entity: KnowledgeFile) -> KnowledgeFileModel:
        model = KnowledgeFileModel(
            id=entity.id,
            name=entity.name,
            filename=entity.filename,
            description=entity.description,
            content=entity.content,
            file_type=entity.file_type,
            scope=entity.scope,
            enriched=entity.enriched,
            conversation_id=entity.conversation_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
        model.tags = entity.tags
        return model

    @staticmethod
    def to_catalog_dict(entity: KnowledgeFile) -> dict:
        """Map entity to agent-facing catalog dict for build_knowledge_catalog."""
        return {
            FIELD_KEY_ID: entity.id,
            FIELD_KEY_NAME: entity.name,
            FIELD_KEY_DESCRIPTION: entity.description,
            FIELD_TAGS: entity.tags,
            FIELD_KEY_FILE_TYPE: entity.file_type,
            FIELD_KEY_SCOPE: entity.scope,
        }
