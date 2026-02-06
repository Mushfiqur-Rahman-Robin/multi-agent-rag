import pytest
import json
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
from main import app
from src.multi_agent_rag.core.config import APPLICATION_API_KEY

@pytest.mark.asyncio
async def test_chat_stream_endpoint_mocked():
    # Mock the ChatService.stream_chat_flow
    with patch("src.multi_agent_rag.api.routes.ChatService.stream_chat_flow") as mock_stream:
        # Mock generator yields
        async def mock_gen(*args, **kwargs):
            yield 'data: {"thread_id": "test-thread", "update": {"thought": "thinking..."}}\n\n'
            yield 'data: {"thread_id": "test-thread", "final": {"response": "done"}}\n\n'

        mock_stream.side_effect = mock_gen

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.post(
                "/chat/stream",
                data={"message": "Hello"},
                headers={"X-API-Key": APPLICATION_API_KEY}
            )

        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]


        # Read the stream content
        content = ""
        async for chunk in response.aiter_text():
            content += chunk

        assert "test-thread" in content
        assert "thinking..." in content
        assert '"response": "done"' in content
