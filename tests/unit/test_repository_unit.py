import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.multi_agent_rag.repositories.chat_repository import ChatRepository
from src.multi_agent_rag.models.chat import Conversation, Message

@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.mark.asyncio
async def test_create_conversation(mock_session):
    repo = ChatRepository(mock_session)
    thread_id = "test-thread"
    title = "test-title"

    await repo.create_conversation(thread_id, title)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()

    # Check that it was called with a Conversation object with correct values
    # Actually, verify the attributes of the object added
    conv = mock_session.add.call_args[0][0]
    assert isinstance(conv, Conversation)
    assert conv.thread_id == thread_id
    assert conv.title == title

@pytest.mark.asyncio
async def test_get_conversations(mock_session):
    repo = ChatRepository(mock_session)
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [Conversation(thread_id="1")]

    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result

    sessions = await repo.get_conversations()

    assert len(sessions) == 1
    assert sessions[0].thread_id == "1"
    mock_session.execute.assert_called_once()

@pytest.mark.asyncio
async def test_add_message(mock_session):
    repo = ChatRepository(mock_session)
    thread_id = "test-thread"
    role = "human"
    content = "hello"

    # Mock conversation for total cost update
    mock_conv = MagicMock()
    mock_conv.total_cost = 0.0
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_conv
    mock_session.execute.return_value = mock_result

    await repo.add_message(thread_id, role, content)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()

    msg = mock_session.add.call_args[0][0]
    assert isinstance(msg, Message)
    assert msg.thread_id == thread_id
    assert msg.role == role
    assert msg.content == content
