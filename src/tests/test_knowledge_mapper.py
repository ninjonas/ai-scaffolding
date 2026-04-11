import json
from datetime import datetime

from app.api.mappers.knowledge_file import KnowledgeFileApiMapper
from app.domain.entities.knowledge_file import (
    SCOPE_CONVERSATION,
    SCOPE_PROJECT,
    KnowledgeFile,
)
from app.infrastructure.mappers.knowledge_file import KnowledgeFileDataMapper
from app.infrastructure.models.knowledge_file import KnowledgeFileModel
from app.shared.field_keys import (
    FIELD_KEY_DESCRIPTION,
    FIELD_KEY_NAME,
)
from app.shared.field_keys import (
    FIELD_KEY_FILE_TYPE as FIELD_FILE_TYPE,
)
from app.shared.field_keys import (
    FIELD_KEY_ID as FIELD_ID,
)
from app.shared.field_keys import (
    FIELD_KEY_SCOPE as FIELD_SCOPE,
)

_FILE_TYPE_MD = "md"
_FILE_TYPE_TXT = "txt"
_NOW = datetime(2025, 1, 1, 12, 0, 0)


def _make_entity(**kwargs) -> KnowledgeFile:
    defaults = dict(
        id="test-id",
        name="Test File",
        description="A test file",
        content="hello",
        file_type=_FILE_TYPE_MD,
        scope=SCOPE_PROJECT,
        tags=["a", "b"],
        conversation_id=None,
        created_at=_NOW,
        updated_at=_NOW,
    )
    defaults.update(kwargs)
    return KnowledgeFile(**defaults)


def _make_model(**kwargs) -> KnowledgeFileModel:
    m = KnowledgeFileModel(
        id="model-id",
        name="Model File",
        description="desc",
        content="body",
        file_type=_FILE_TYPE_TXT,
        scope=SCOPE_CONVERSATION,
        conversation_id="conv-1",
        created_at=_NOW,
        updated_at=_NOW,
    )
    m.tags_json = json.dumps(["x", "y"])
    for k, v in kwargs.items():
        setattr(m, k, v)
    return m


# -- to_domain --


def test_to_domain_preserves_id():
    model = _make_model()
    entity = KnowledgeFileDataMapper.to_domain(model)
    assert entity.id == "model-id"


def test_to_domain_preserves_name():
    model = _make_model()
    entity = KnowledgeFileDataMapper.to_domain(model)
    assert entity.name == "Model File"


def test_to_domain_parses_tags_from_json():
    model = _make_model()
    entity = KnowledgeFileDataMapper.to_domain(model)
    assert entity.tags == ["x", "y"]


def test_to_domain_preserves_conversation_id():
    model = _make_model()
    entity = KnowledgeFileDataMapper.to_domain(model)
    assert entity.conversation_id == "conv-1"


# -- to_model --


def test_to_model_preserves_id():
    entity = _make_entity()
    model = KnowledgeFileDataMapper.to_model(entity)
    assert model.id == "test-id"


def test_to_model_serializes_tags_to_json():
    entity = _make_entity()
    model = KnowledgeFileDataMapper.to_model(entity)
    assert json.loads(model.tags_json) == ["a", "b"]


def test_to_model_preserves_content():
    entity = _make_entity(content="rich content")
    model = KnowledgeFileDataMapper.to_model(entity)
    assert model.content == "rich content"


# -- to_response_dto --


def test_to_response_dto_has_name():
    entity = _make_entity()
    dto = KnowledgeFileApiMapper.to_response_dto(entity)
    assert getattr(dto, FIELD_KEY_NAME) == "Test File"


def test_to_response_dto_has_description():
    entity = _make_entity()
    dto = KnowledgeFileApiMapper.to_response_dto(entity)
    assert getattr(dto, FIELD_KEY_DESCRIPTION) == "A test file"


def test_to_response_dto_has_tags():
    entity = _make_entity()
    dto = KnowledgeFileApiMapper.to_response_dto(entity)
    assert dto.tags == ["a", "b"]


def test_to_response_dto_has_file_type():
    entity = _make_entity()
    dto = KnowledgeFileApiMapper.to_response_dto(entity)
    assert dto.file_type == _FILE_TYPE_MD


# -- to_catalog_entry_dto --


def test_to_catalog_entry_dto_has_id():
    entity = _make_entity()
    dto = KnowledgeFileApiMapper.to_catalog_entry_dto(entity)
    assert dto.id == "test-id"


def test_to_catalog_entry_dto_has_scope():
    entity = _make_entity()
    dto = KnowledgeFileApiMapper.to_catalog_entry_dto(entity)
    assert dto.scope == SCOPE_PROJECT


def test_to_catalog_entry_dto_has_no_content():
    entity = _make_entity()
    dto = KnowledgeFileApiMapper.to_catalog_entry_dto(entity)
    assert not hasattr(dto, "content")


# -- to_catalog_dict --


def test_to_catalog_dict_has_required_keys():
    entity = _make_entity()
    d = KnowledgeFileDataMapper.to_catalog_dict(entity)
    assert FIELD_ID in d
    assert FIELD_KEY_NAME in d
    assert FIELD_KEY_DESCRIPTION in d
    assert FIELD_FILE_TYPE in d
    assert FIELD_SCOPE in d


def test_to_catalog_dict_values_match_entity():
    entity = _make_entity()
    d = KnowledgeFileDataMapper.to_catalog_dict(entity)
    assert d[FIELD_ID] == "test-id"
    assert d[FIELD_KEY_NAME] == "Test File"
    assert d[FIELD_SCOPE] == SCOPE_PROJECT
