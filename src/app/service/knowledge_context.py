"""Build knowledge context strings injected into agent messages."""

from app.domain.entities.knowledge_file import KnowledgeFile
from app.service.knowledge_frontmatter import is_image

PROJECT_CONTEXT_HEADER = "\n\n[Project knowledge base:]"
PROJECT_FILE_SECTION = "\n### {name}\n{content}"
CONVERSATION_CONTEXT_HEADER = "\n\n[Conversation files:]"
CONVERSATION_FILE_LINE = '- "{name}": {desc}'
KNOWLEDGE_NO_DESCRIPTION = "No description"


def build_project_context(files: list[KnowledgeFile]) -> str:
    """Inject full project file content into agent context."""
    if not files:
        return ""
    sections = [PROJECT_CONTEXT_HEADER]
    for f in files:
        content = f.description if is_image(f.file_type) else f.content
        sections.append(PROJECT_FILE_SECTION.format(name=f.name, content=content))
    return "\n".join(sections)


def build_conversation_context(files: list[KnowledgeFile]) -> str:
    """Build a manifest of conversation files (content is in chat history)."""
    if not files:
        return ""
    lines = [CONVERSATION_CONTEXT_HEADER]
    for f in files:
        desc = f.description or KNOWLEDGE_NO_DESCRIPTION
        lines.append(CONVERSATION_FILE_LINE.format(name=f.name, desc=desc))
    return "\n".join(lines)
