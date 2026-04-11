from datetime import datetime

from app.domain.entities.knowledge_file import KnowledgeFile
from app.service.chat import SCOPE_PROJECT
from app.service.knowledge import SCOPE_CONVERSATION

_FILE_TYPE_MD = "md"
_FILE_TYPE_JSON = "json"
_FILE_TYPE_TXT = "txt"


def test_knowledge_file_auto_generates_id():
    kf = KnowledgeFile(
        name="x", description="", content="", file_type=_FILE_TYPE_MD, scope=SCOPE_PROJECT
    )
    assert isinstance(kf.id, str)
    assert len(kf.id) == 36  # uuid4


def test_knowledge_file_two_instances_have_different_ids():
    a = KnowledgeFile(
        name="a", description="", content="", file_type=_FILE_TYPE_MD, scope=SCOPE_PROJECT
    )
    b = KnowledgeFile(
        name="b", description="", content="", file_type=_FILE_TYPE_MD, scope=SCOPE_PROJECT
    )
    assert a.id != b.id


def test_knowledge_file_default_tags_is_empty_list():
    kf = KnowledgeFile(
        name="x", description="", content="", file_type=_FILE_TYPE_MD, scope=SCOPE_PROJECT
    )
    assert kf.tags == []


def test_knowledge_file_tags_not_shared_across_instances():
    a = KnowledgeFile(
        name="a", description="", content="", file_type=_FILE_TYPE_MD, scope=SCOPE_PROJECT
    )
    b = KnowledgeFile(
        name="b", description="", content="", file_type=_FILE_TYPE_MD, scope=SCOPE_PROJECT
    )
    a.tags.append("tag")
    assert b.tags == []


def test_knowledge_file_conversation_id_defaults_to_none():
    kf = KnowledgeFile(
        name="x", description="", content="", file_type=_FILE_TYPE_MD, scope=SCOPE_PROJECT
    )
    assert kf.conversation_id is None


def test_knowledge_file_stores_scope_and_file_type():
    kf = KnowledgeFile(
        name="x",
        description="",
        content="body",
        file_type=_FILE_TYPE_JSON,
        scope=SCOPE_CONVERSATION,
    )
    assert kf.file_type == _FILE_TYPE_JSON
    assert kf.scope == SCOPE_CONVERSATION


def test_knowledge_file_created_at_is_datetime():
    kf = KnowledgeFile(
        name="x", description="", content="", file_type=_FILE_TYPE_TXT, scope=SCOPE_PROJECT
    )
    assert isinstance(kf.created_at, datetime)


def test_knowledge_file_explicit_id_is_preserved():
    kf = KnowledgeFile(
        name="x",
        description="",
        content="",
        file_type=_FILE_TYPE_MD,
        scope=SCOPE_PROJECT,
        id="my-id",
    )
    assert kf.id == "my-id"
