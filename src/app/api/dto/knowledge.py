from datetime import datetime

from pydantic import Field

from app.api.dto.common import CamelModel


class KnowledgeFileUploadDTO(CamelModel):
    filename: str
    content: str
    scope: str  # "project" | "conversation"
    conversation_id: str | None = None


class KnowledgeFileUpdateDTO(CamelModel):
    name: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    content: str | None = None


class KnowledgeFileResponseDTO(CamelModel):
    id: str
    name: str
    description: str
    content: str = ""
    tags: list[str] = Field(default_factory=list)
    file_type: str
    scope: str
    enriched: bool = False
    conversation_id: str | None = None
    created_at: datetime
    updated_at: datetime


class KnowledgeCatalogEntryDTO(CamelModel):
    id: str
    name: str
    description: str
    tags: list[str] = Field(default_factory=list)
    file_type: str
    scope: str
    enriched: bool = False
