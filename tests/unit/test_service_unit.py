import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.multi_agent_rag.services.chat_service import ChatService

@pytest.fixture
def mock_repo():
    return AsyncMock()

@pytest.fixture
def chat_service(mock_repo):
    # Patch create_multi_agent_graph to return a mock graph
    with patch('src.multi_agent_rag.services.chat_service.create_multi_agent_graph') as mock_create:
        mock_graph = AsyncMock()
        mock_create.return_value = mock_graph
        service = ChatService(mock_repo)
        return service

@pytest.mark.asyncio
async def test_run_chat_flow_new_session(chat_service, mock_repo):
    message = "Hello"
    thread_id = None
    files = []

    # Mock graph.ainvoke
    chat_service.graph.ainvoke.return_value = {
        "thought": "Direct answer",
        "final_response": "Hi there!",
        "research_output": "",
        "plan": "",
        "code": ""
    }
    # Mock repo.get_recent_messages and repo.create_conversation
    mock_repo.get_recent_messages.return_value = []
    mock_repo.get_messages.return_value = []
    mock_repo.create_conversation.return_value = AsyncMock()

    # Mock cost_service and callback

    with patch('src.multi_agent_rag.services.cost_service.cost_service') as mock_cost:
        mock_cost.calculate_cost.return_value = 0.05
        with patch('langchain_community.callbacks.get_openai_callback') as mock_cb:
            mock_cb_instance = MagicMock()
            mock_cb_instance.prompt_tokens = 10
            mock_cb_instance.completion_tokens = 20
            mock_cb.__enter__.return_value = mock_cb_instance

            new_thread_id, ai_content = await chat_service.run_chat_flow(message, thread_id, files)

    assert new_thread_id is not None
    assert ai_content["response"] == "Hi there!"

    print(f"\nDEBUG: CALL ARGS LIST: {mock_repo.add_message.call_args_list}")
    mock_repo.create_conversation.assert_called_once()
    mock_repo.add_message.assert_any_call(new_thread_id, "human", message)

    from unittest.mock import ANY
    mock_repo.add_message.assert_any_call(
        ANY,
        "ai",
        ANY,
        model_name=ANY,
        input_tokens=ANY,
        output_tokens=ANY,
        cost=ANY
    )




@pytest.mark.asyncio
async def test_get_all_sessions(chat_service, mock_repo):
    mock_repo.get_conversations.return_value = [{"thread_id": "1", "title": "test"}]

    sessions = await chat_service.get_all_sessions()

    assert len(sessions) == 1
    assert sessions[0]["thread_id"] == "1"
    mock_repo.get_conversations.assert_called_once()
