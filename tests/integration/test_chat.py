import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock
from main import app
from src.multi_agent_rag.schemas.chat import ChatResponse

@pytest.mark.asyncio
async def test_chat_endpoint_mocked():
    # Mock the ChatService.run_chat_flow to avoid real API calls during tests
    with patch("src.multi_agent_rag.api.routes.ChatService.run_chat_flow") as mock_run:
        mock_run.return_value = ("test-thread-id", {"research": "test", "plan": "test", "code": "test"})

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.post(
                "/chat",
                data={"message": "Hello", "thread_id": "existing-thread"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["thread_id"] == "test-thread-id"
        assert "research" in data["response"]
