from app.api.dto.chat import ChatRequestDTO, ChatResponseDTO, ToolCallDTO
from app.api.dto.common import CamelModel, ErrorDTO

# -- CamelModel alias generation --


def test_camel_model_alias_generator_snake_to_camel():
    class SampleModel(CamelModel):
        my_field: str

    instance = SampleModel(my_field="value")
    serialized = instance.model_dump(by_alias=True)
    assert "myField" in serialized


def test_camel_model_populate_by_name_accepts_snake_case():
    class SampleModel(CamelModel):
        my_field: str

    instance = SampleModel(my_field="value")
    assert instance.my_field == "value"


# -- ChatRequestDTO --


def test_chat_request_dto_accepts_snake_case():
    dto = ChatRequestDTO(message="Hello", conversation_id="conv-1")
    assert dto.message == "Hello"
    assert dto.conversation_id == "conv-1"


def test_chat_request_dto_accepts_camel_case():
    dto = ChatRequestDTO.model_validate({"message": "Hi", "conversationId": "conv-2"})
    assert dto.conversation_id == "conv-2"


def test_chat_request_dto_conversation_id_optional():
    dto = ChatRequestDTO(message="Hello")
    assert dto.conversation_id is None


def test_chat_request_dto_images_defaults_to_empty_list():
    dto = ChatRequestDTO(message="Hello")
    assert dto.images == []


def test_chat_request_dto_accepts_images():
    dto = ChatRequestDTO(message="Hello", images=["img1.png", "img2.png"])
    assert len(dto.images) == 2


def test_chat_request_dto_camel_case_images():
    dto = ChatRequestDTO.model_validate({"message": "Hi", "images": ["img.png"]})
    assert dto.images == ["img.png"]


# -- ChatResponseDTO --


def test_chat_response_dto_serializes_to_camel_case():
    dto = ChatResponseDTO(message="Hello", conversation_id="conv-1")
    serialized = dto.model_dump(by_alias=True)
    assert "conversationId" in serialized
    assert "message" in serialized


def test_chat_response_dto_message_value():
    dto = ChatResponseDTO(message="Response text", conversation_id="conv-5")
    assert dto.message == "Response text"


def test_chat_response_dto_tool_calls_defaults_empty():
    dto = ChatResponseDTO(message="Hi", conversation_id="conv-1")
    assert dto.tool_calls == []


def test_chat_response_dto_with_tool_calls():
    tc = ToolCallDTO(name="search", args={"query": "test"})
    dto = ChatResponseDTO(message="Hi", conversation_id="conv-1", tool_calls=[tc])
    assert len(dto.tool_calls) == 1
    assert dto.tool_calls[0].name == "search"


def test_chat_response_dto_tool_calls_serialized_as_camel():
    tc = ToolCallDTO(name="calc", args={"expr": "1+1"})
    dto = ChatResponseDTO(message="done", conversation_id="c1", tool_calls=[tc])
    serialized = dto.model_dump(by_alias=True)
    assert "toolCalls" in serialized


# -- ErrorDTO --


def test_error_dto_stores_detail_and_status_code():
    err = ErrorDTO(detail="Not found", status_code=404)
    assert err.detail == "Not found"
    assert err.status_code == 404


def test_error_dto_serializes_status_code_as_camel():
    err = ErrorDTO(detail="err", status_code=500)
    serialized = err.model_dump(by_alias=True)
    assert "statusCode" in serialized
