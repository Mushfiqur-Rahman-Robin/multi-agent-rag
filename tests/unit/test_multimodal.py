import pytest
from src.multi_agent_rag.core.multimodal import create_multimodal_message
from langchain_core.messages import HumanMessage

def test_create_multimodal_message_text_only():
    message = "Hello world"
    human_msg = create_multimodal_message(message)

    assert isinstance(human_msg, HumanMessage)
    assert len(human_msg.content) == 1
    assert human_msg.content[0]["type"] == "text"
    assert human_msg.content[0]["text"] == "Hello world"

def test_create_multimodal_message_with_empty_files():
    message = "Hello"
    human_msg = create_multimodal_message(message, file_paths=[])
    assert len(human_msg.content) == 1
