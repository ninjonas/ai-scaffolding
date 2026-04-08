import dataclasses
from datetime import datetime

import pytest

from app.domain.entities.conversation import Conversation
from app.domain.entities.message import Message, MessageRole
from app.domain.value_objects.image import OptimizedImage

# -- Message --


def test_message_auto_generates_id():
    msg = Message(content="hello", role=MessageRole.USER)
    assert msg.id
    assert len(msg.id) == 36  # UUID format


def test_message_two_instances_have_different_ids():
    msg1 = Message(content="a", role=MessageRole.USER)
    msg2 = Message(content="b", role=MessageRole.USER)
    assert msg1.id != msg2.id


def test_message_auto_generates_created_at():
    before = datetime.utcnow()
    msg = Message(content="hi", role=MessageRole.USER)
    after = datetime.utcnow()
    assert before <= msg.created_at <= after


def test_message_default_conversation_id_is_empty():
    msg = Message(content="hi", role=MessageRole.USER)
    assert msg.conversation_id == ""


def test_message_default_images_is_empty_list():
    msg = Message(content="hi", role=MessageRole.USER)
    assert msg.images == []


def test_message_default_tool_calls_is_empty_list():
    msg = Message(content="hi", role=MessageRole.USER)
    assert msg.tool_calls == []


# -- MessageRole --


def test_message_role_user_value():
    assert MessageRole.USER.value == MessageRole.USER


def test_message_role_assistant_value():
    assert MessageRole.ASSISTANT.value == MessageRole.ASSISTANT


def test_message_role_system_value():
    assert MessageRole.SYSTEM.value == MessageRole.SYSTEM


def test_message_role_tool_value():
    assert MessageRole.TOOL.value == MessageRole.TOOL


# -- Conversation --


def test_conversation_auto_generates_id():
    convo = Conversation()
    assert convo.id
    assert len(convo.id) == 36


def test_conversation_add_message_sets_conversation_id():
    convo = Conversation()
    msg = Message(content="hello", role=MessageRole.USER)
    convo.add_message(msg)
    assert msg.conversation_id == convo.id


def test_conversation_add_message_appends_to_messages():
    convo = Conversation()
    msg = Message(content="hello", role=MessageRole.USER)
    convo.add_message(msg)
    assert len(convo.messages) == 1
    assert convo.messages[0] is msg


def test_conversation_add_message_updates_updated_at():
    convo = Conversation()
    original_updated_at = convo.updated_at
    msg = Message(content="hello", role=MessageRole.USER)
    convo.add_message(msg)
    assert convo.updated_at >= original_updated_at


def test_conversation_multiple_messages():
    convo = Conversation()
    msg1 = Message(content="first", role=MessageRole.USER)
    msg2 = Message(content="second", role=MessageRole.ASSISTANT)
    convo.add_message(msg1)
    convo.add_message(msg2)
    assert len(convo.messages) == 2
    assert msg1.conversation_id == convo.id
    assert msg2.conversation_id == convo.id


# -- OptimizedImage --


def test_optimized_image_is_frozen():
    img = OptimizedImage(
        data_base64="abc",
        format="jpeg",
        original_width=100,
        original_height=100,
        optimized_width=50,
        optimized_height=50,
        original_bytes=1000,
        optimized_bytes=500,
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        img.format = "png"  # type: ignore[misc]


def test_optimized_image_stores_values():
    img = OptimizedImage(
        data_base64="base64data",
        format="jpeg",
        original_width=800,
        original_height=600,
        optimized_width=400,
        optimized_height=300,
        original_bytes=8000,
        optimized_bytes=2000,
    )
    assert img.data_base64 == "base64data"
    assert img.format == "jpeg"
    assert img.original_width == 800
    assert img.optimized_bytes == 2000
