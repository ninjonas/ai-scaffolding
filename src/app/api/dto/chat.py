from pydantic import Field

from app.api.dto.common import CamelModel


class ChatRequestDTO(CamelModel):
    message: str
    conversation_id: str | None = None
    images: list[str] = Field(default_factory=list)
    image_filenames: list[str] = Field(default_factory=list)
    knowledge_file_ids: list[str] = Field(default_factory=list)


class ToolCallDTO(CamelModel):
    name: str
    args: dict


class ChatResponseDTO(CamelModel):
    message: str
    conversation_id: str
    tool_calls: list[ToolCallDTO] = Field(default_factory=list)
    interrupt: dict | None = None


class ResumeRequestDTO(CamelModel):
    approved: bool


class ChatStreamChunkDTO(CamelModel):
    content: str = ""
    done: bool = False
    conversation_id: str = ""
    tool_calls: list[ToolCallDTO] = Field(default_factory=list)
