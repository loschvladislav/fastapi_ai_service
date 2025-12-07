from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas.chat import ChatMessage, ChatResponse


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


class TestHealthCheck:
    async def test_health_check(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestChatEndpoint:
    async def test_chat_success(self, client: AsyncClient):
        """Test successful chat completion with mocked OpenAI."""
        mock_response = ChatResponse(
            message=ChatMessage(role="assistant", content="Python is a programming language."),
            model="gpt-3.5-turbo",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        )

        with patch("app.api.v1.chat.chat_completion", new_callable=AsyncMock) as mock:
            mock.return_value = mock_response

            response = await client.post(
                "/api/v1/chat",
                json={
                    "messages": [{"role": "user", "content": "What is Python?"}],
                    "model": "gpt-3.5-turbo",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["message"]["role"] == "assistant"
            assert "Python" in data["message"]["content"]

    async def test_chat_validation_error(self, client: AsyncClient):
        """Test validation error for empty messages."""
        response = await client.post(
            "/api/v1/chat",
            json={"messages": []},
        )
        assert response.status_code == 422

    async def test_chat_invalid_role(self, client: AsyncClient):
        """Test validation error for invalid role."""
        response = await client.post(
            "/api/v1/chat",
            json={
                "messages": [{"role": "invalid", "content": "Hello"}],
            },
        )
        assert response.status_code == 422

    async def test_chat_temperature_validation(self, client: AsyncClient):
        """Test temperature must be between 0 and 2."""
        with patch("app.api.v1.chat.chat_completion", new_callable=AsyncMock):
            response = await client.post(
                "/api/v1/chat",
                json={
                    "messages": [{"role": "user", "content": "Hello"}],
                    "temperature": 3.0,  # Invalid
                },
            )
            assert response.status_code == 422
