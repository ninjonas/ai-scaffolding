from datetime import datetime

from app.domain.entities.message import Message, MessageRole
from app.infrastructure.mappers.chat import ChatMapper
from app.infrastructure.mappers.conversation import ConversationDataMapper
from app.infrastructure.models.conversation import ConversationModel
from app.infrastructure.models.message import MessageModel

# -- ChatMapper --


def test_chat_mapper_to_response_dto_message_content():
    msg = Message(content="Hello!", role=MessageRole.ASSISTANT)
    dto = ChatMapper.to_response_dto(msg, conversation_id="conv-1")
    assert dto.message == "Hello!"


def test_chat_mapper_to_response_dto_conversation_id():
    msg = Message(content="Hi", role=MessageRole.ASSISTANT)
    dto = ChatMapper.to_response_dto(msg, conversation_id="conv-42")
    assert dto.conversation_id == "conv-42"


def test_chat_mapper_to_response_dto_empty_tool_calls():
    msg = Message(content="Hi", role=MessageRole.ASSISTANT, tool_calls=[])
    dto = ChatMapper.to_response_dto(msg, conversation_id="conv-1")
    assert dto.tool_calls == []


def test_chat_mapper_to_response_dto_with_tool_calls():
    msg = Message(
        content="Used a tool",
        role=MessageRole.ASSISTANT,
        tool_calls=[{"name": "calculate", "args": {"expression": "2+2"}}],
    )
    dto = ChatMapper.to_response_dto(msg, conversation_id="conv-1")
    assert len(dto.tool_calls) == 1
    assert dto.tool_calls[0].name == "calculate"
    assert dto.tool_calls[0].args == {"expression": "2+2"}


def test_chat_mapper_tool_call_missing_fields_defaults_to_empty():
    msg = Message(
        content="Hi",
        role=MessageRole.ASSISTANT,
        tool_calls=[{}],
    )
    dto = ChatMapper.to_response_dto(msg, conversation_id="conv-1")
    assert dto.tool_calls[0].name == ""
    assert dto.tool_calls[0].args == {}


# -- ConversationDataMapper round-trip --


def _make_conversation_model() -> ConversationModel:
    now = datetime(2024, 1, 1, 12, 0, 0)
    model = ConversationModel(
        id="convo-123",
        title="Test Chat",
        created_at=now,
        updated_at=now,
    )
    msg_model = MessageModel(
        id="msg-1",
        conversation_id="convo-123",
        content="Hello world",
        role=MessageRole.USER.value,
        created_at=now,
    )
    msg_model.images = ["img1.png"]
    msg_model.tool_calls = [{"name": "calc", "args": {}}]
    model.messages = [msg_model]
    return model


def test_round_trip_preserves_conversation_id():
    model = _make_conversation_model()
    domain = ConversationDataMapper.to_domain(model)
    restored = ConversationDataMapper.to_model(domain)
    assert restored.id == model.id


def test_round_trip_preserves_title():
    model = _make_conversation_model()
    domain = ConversationDataMapper.to_domain(model)
    restored = ConversationDataMapper.to_model(domain)
    assert restored.title == model.title


def test_round_trip_preserves_message_count():
    model = _make_conversation_model()
    domain = ConversationDataMapper.to_domain(model)
    restored = ConversationDataMapper.to_model(domain)
    assert len(restored.messages) == len(model.messages)


def test_round_trip_preserves_message_content():
    model = _make_conversation_model()
    domain = ConversationDataMapper.to_domain(model)
    restored = ConversationDataMapper.to_model(domain)
    assert restored.messages[0].content == "Hello world"


def test_round_trip_preserves_message_role():
    model = _make_conversation_model()
    domain = ConversationDataMapper.to_domain(model)
    restored = ConversationDataMapper.to_model(domain)
    assert restored.messages[0].role == MessageRole.USER.value


def test_round_trip_preserves_message_images():
    model = _make_conversation_model()
    domain = ConversationDataMapper.to_domain(model)
    restored = ConversationDataMapper.to_model(domain)
    assert restored.messages[0].images == ["img1.png"]


def test_round_trip_preserves_message_tool_calls():
    model = _make_conversation_model()
    domain = ConversationDataMapper.to_domain(model)
    restored = ConversationDataMapper.to_model(domain)
    assert restored.messages[0].tool_calls == [{"name": "calc", "args": {}}]


def test_to_domain_maps_role_enum():
    model = _make_conversation_model()
    domain = ConversationDataMapper.to_domain(model)
    assert domain.messages[0].role is MessageRole.USER


def test_to_domain_with_empty_conversation():
    now = datetime(2024, 6, 1, 0, 0, 0)
    model = ConversationModel(id="empty-id", title="", created_at=now, updated_at=now)
    model.messages = []
    domain = ConversationDataMapper.to_domain(model)
    assert domain.id == "empty-id"
    assert domain.messages == []
