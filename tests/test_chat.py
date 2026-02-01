from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.schemas.chat import ChatMessage, ChatResponse
from app.services.ai_provider import ai_provider


class TestHealthCheck:
    async def test_health_check(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "cache" in data  # Cache status included


class TestChatEndpoint:
    async def test_chat_requires_api_key(self, client: AsyncClient):
        """Test that chat endpoint requires API key."""
        response = await client.post(
            "/api/v1/chat",
            json={
                "messages": [{"role": "user", "content": "Hello"}],
            },
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Missing API key"

    async def test_chat_invalid_api_key(self, client: AsyncClient):
        """Test that invalid API key is rejected."""
        response = await client.post(
            "/api/v1/chat",
            json={
                "messages": [{"role": "user", "content": "Hello"}],
            },
            headers={"X-API-Key": "invalid_key"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid API key"

    async def test_chat_success(self, client: AsyncClient, api_key_headers: dict):
        """Test successful chat completion with mocked OpenAI."""
        mock_response = ChatResponse(
            message=ChatMessage(role="assistant", content="Python is a programming language."),
            model="gpt-3.5-turbo",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        )

        with patch.object(ai_provider, "chat", new_callable=AsyncMock) as mock:
            mock.return_value = mock_response

            response = await client.post(
                "/api/v1/chat",
                json={
                    "messages": [{"role": "user", "content": "What is Python?"}],
                    "model": "gpt-3.5-turbo",
                },
                headers=api_key_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["message"]["role"] == "assistant"
            assert "Python" in data["message"]["content"]

    async def test_chat_validation_error(self, client: AsyncClient, api_key_headers: dict):
        """Test validation error for empty messages."""
        response = await client.post(
            "/api/v1/chat",
            json={"messages": []},
            headers=api_key_headers,
        )
        assert response.status_code == 422

    async def test_chat_invalid_role(self, client: AsyncClient, api_key_headers: dict):
        """Test validation error for invalid role."""
        response = await client.post(
            "/api/v1/chat",
            json={
                "messages": [{"role": "invalid", "content": "Hello"}],
            },
            headers=api_key_headers,
        )
        assert response.status_code == 422

    async def test_chat_temperature_validation(self, client: AsyncClient, api_key_headers: dict):
        """Test temperature must be between 0 and 2."""
        with patch.object(ai_provider, "chat", new_callable=AsyncMock):
            response = await client.post(
                "/api/v1/chat",
                json={
                    "messages": [{"role": "user", "content": "Hello"}],
                    "temperature": 3.0,  # Invalid
                },
                headers=api_key_headers,
            )
            assert response.status_code == 422


class TestChatStreamEndpoint:
    async def test_chat_stream_requires_api_key(self, client: AsyncClient):
        """Test that stream endpoint requires API key."""
        response = await client.post(
            "/api/v1/chat/stream",
            json={
                "messages": [{"role": "user", "content": "Hello"}],
            },
        )
        assert response.status_code == 401

    async def test_chat_stream_success(self, client: AsyncClient, api_key_headers: dict):
        """Test successful streaming chat completion."""

        async def mock_stream(*args, **kwargs):
            yield 'data: {"token": "Hello"}\n\n'
            yield 'data: {"token": " World"}\n\n'
            yield 'data: {"done": true, "full_text": "Hello World"}\n\n'

        with patch.object(ai_provider, "chat_stream", return_value=mock_stream()):
            response = await client.post(
                "/api/v1/chat/stream",
                json={
                    "messages": [{"role": "user", "content": "Say hello"}],
                    "model": "gpt-3.5-turbo",
                },
                headers=api_key_headers,
            )

            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

            # Check response contains streamed data
            content = response.text
            assert "Hello" in content
            assert "World" in content
            assert "done" in content

    async def test_chat_stream_validation_error(self, client: AsyncClient, api_key_headers: dict):
        """Test validation error for empty messages in stream."""
        response = await client.post(
            "/api/v1/chat/stream",
            json={"messages": []},
            headers=api_key_headers,
        )
        assert response.status_code == 422

    async def test_chat_stream_invalid_role(self, client: AsyncClient, api_key_headers: dict):
        """Test validation error for invalid role in stream."""
        response = await client.post(
            "/api/v1/chat/stream",
            json={
                "messages": [{"role": "invalid", "content": "Hello"}],
            },
            headers=api_key_headers,
        )
        assert response.status_code == 422
