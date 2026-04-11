import pytest

from app.agents.tools.knowledge import build_knowledge_catalog, make_read_knowledge_file_tool
from app.domain.entities.knowledge_file import SCOPE_PROJECT, KnowledgeFile
from app.shared.field_keys import FIELD_KEY_DESCRIPTION, FIELD_KEY_NAME

_FILE_TYPE_MD = "md"

_ENTRY = {
    FIELD_KEY_NAME: "My Doc",
    "file_type": _FILE_TYPE_MD,
    "scope": SCOPE_PROJECT,
    FIELD_KEY_DESCRIPTION: "A useful document",
    "id": "abc-123",
}


# -- build_knowledge_catalog --


def test_build_knowledge_catalog_empty_returns_empty_string():
    assert build_knowledge_catalog([]) == ""


def test_build_knowledge_catalog_includes_header():
    result = build_knowledge_catalog([_ENTRY])
    assert "## Knowledge Base" in result


def test_build_knowledge_catalog_includes_file_name():
    result = build_knowledge_catalog([_ENTRY])
    assert "My Doc" in result


def test_build_knowledge_catalog_includes_file_type():
    result = build_knowledge_catalog([_ENTRY])
    assert _FILE_TYPE_MD in result


def test_build_knowledge_catalog_includes_scope():
    result = build_knowledge_catalog([_ENTRY])
    assert SCOPE_PROJECT in result


def test_build_knowledge_catalog_includes_description():
    result = build_knowledge_catalog([_ENTRY])
    assert "A useful document" in result


def test_build_knowledge_catalog_includes_id():
    result = build_knowledge_catalog([_ENTRY])
    assert "abc-123" in result


def test_build_knowledge_catalog_multiple_entries():
    entries = [
        {**_ENTRY, FIELD_KEY_NAME: "Doc A", "id": "id-a"},
        {**_ENTRY, FIELD_KEY_NAME: "Doc B", "id": "id-b"},
    ]
    result = build_knowledge_catalog(entries)
    assert "Doc A" in result
    assert "Doc B" in result


# -- make_read_knowledge_file_tool --


class _FakeRepo:
    def __init__(self, files: dict[str, KnowledgeFile]):
        self._files = files

    async def get_by_id(self, file_id: str) -> KnowledgeFile | None:
        return self._files.get(file_id)


def _make_file(file_id: str, content: str) -> KnowledgeFile:
    return KnowledgeFile(
        id=file_id,
        name="Test",
        description="",
        content=content,
        file_type=_FILE_TYPE_MD,
        scope=SCOPE_PROJECT,
    )


@pytest.mark.asyncio
async def test_read_knowledge_file_returns_content():
    kf = _make_file("f1", "hello world")
    repo = _FakeRepo({"f1": kf})
    tool = make_read_knowledge_file_tool(lambda: repo)
    result = await tool.ainvoke({"file_id": "f1"})
    assert result == "hello world"


@pytest.mark.asyncio
async def test_read_knowledge_file_not_found_returns_message():
    repo = _FakeRepo({})
    tool = make_read_knowledge_file_tool(lambda: repo)
    result = await tool.ainvoke({"file_id": "missing"})
    assert "not found" in result.lower()
