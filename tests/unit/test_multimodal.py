import pytest
from unittest.mock import patch
from src.multi_agent_rag.core.multimodal import create_multimodal_message
from langchain_core.messages import HumanMessage

@pytest.mark.asyncio
async def test_create_multimodal_message_text_only():
    message = "Hello world"
    human_msg = await create_multimodal_message(message)

    assert isinstance(human_msg, HumanMessage)
    assert len(human_msg.content) == 1
    assert human_msg.content[0]["type"] == "text"
    assert human_msg.content[0]["text"] == "Hello world"

@pytest.mark.asyncio
async def test_create_multimodal_message_with_empty_files():
    message = "Hello"
    human_msg = await create_multimodal_message(message, file_paths=[])
    assert len(human_msg.content) == 1

@pytest.mark.asyncio
async def test_create_multimodal_message_with_pdf():
    # We mock the extract_file_content function in the core.multimodal module namespace
    # Note: Since it's imported as 'from ... import extract_file_content', we mock it there.
    with patch("src.multi_agent_rag.core.multimodal.extract_file_content") as mock_extract:
        mock_extract.return_value = "Extracted PDF content"

        message = "Analyze this PDF"
        file_paths = ["/path/to/document.pdf"]

        human_msg = await create_multimodal_message(message, file_paths)

        assert len(human_msg.content) == 2
        assert human_msg.content[1]["type"] == "text"
        assert "Extracted PDF content" in human_msg.content[1]["text"]
        assert "document.pdf" in human_msg.content[1]["text"]
