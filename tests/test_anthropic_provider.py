"""Tests for Anthropic provider."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.schemas.chat import ChatMessage, ChatRequest
from app.schemas.summarize import SummarizeRequest
from app.schemas.translate import TranslateRequest
from app.services.anthropic_provider import AnthropicProvider


def mock_anthropic_response(content: str, input_tokens: int = 10, output_tokens: int = 20):
    """Create a mock Anthropic API response."""
    return httpx.Response(
        status_code=200,
        json={
            "content": [{"type": "text", "text": content}],
            "model": "claude-sonnet-4-20250514",
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            },
        },
        request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"),
    )


@pytest.fixture
def provider():
    """Create AnthropicProvider with mocked settings."""
    with patch("app.services.anthropic_provider.settings") as mock_settings:
        mock_settings.anthropic_api_key = "test-key"
        yield AnthropicProvider()


class TestAnthropicChat:
    async def test_chat_success(self, provider):
        """Test successful chat completion."""
        request = ChatRequest(
            messages=[
                ChatMessage(role="user", content="What is Python?"),
            ],
            model="claude-sonnet-4-20250514",
        )

        mock_resp = mock_anthropic_response("Python is a programming language.")

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
            response = await provider.chat(request)

        assert response.message.role == "assistant"
        assert response.message.content == "Python is a programming language."
        assert response.model == "claude-sonnet-4-20250514"
        assert response.usage["prompt_tokens"] == 10
        assert response.usage["completion_tokens"] == 20
        assert response.usage["total_tokens"] == 30

    async def test_chat_with_system_message(self, provider):
        """Test that system message is separated from user messages."""
        request = ChatRequest(
            messages=[
                ChatMessage(role="system", content="You are helpful."),
                ChatMessage(role="user", content="Hello"),
            ],
            model="claude-sonnet-4-20250514",
        )

        mock_resp = mock_anthropic_response("Hi there!")

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp) as mock_post:
            await provider.chat(request)

            # Verify system is passed separately (Anthropic format)
            call_kwargs = mock_post.call_args
            body = call_kwargs.kwargs["json"]
            assert body["system"] == "You are helpful."
            assert len(body["messages"]) == 1
            assert body["messages"][0]["role"] == "user"


class TestAnthropicSummarize:
    async def test_summarize_success(self, provider):
        """Test successful summarization."""
        request = SummarizeRequest(
            text="This is a long text that needs to be summarized.",
            style="concise",
        )

        mock_resp = mock_anthropic_response("Short summary.")

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
            response = await provider.summarize(request)

        assert response.summary == "Short summary."
        assert response.original_length == len(request.text)
        assert response.summary_length == len("Short summary.")


class TestAnthropicTranslate:
    async def test_translate_success(self, provider):
        """Test successful translation."""
        request = TranslateRequest(
            text="Hello world",
            target_language="Spanish",
        )

        mock_resp = mock_anthropic_response("Hola mundo")

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
            response = await provider.translate(request)

        assert response.translated_text == "Hola mundo"
        assert response.target_language == "Spanish"

    async def test_translate_auto_detect(self, provider):
        """Test translation with auto language detection."""
        request = TranslateRequest(
            text="Bonjour",
            source_language="auto",
            target_language="English",
        )

        mock_resp = mock_anthropic_response("Hello")

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
            response = await provider.translate(request)

        assert response.translated_text == "Hello"
        assert response.source_language == "auto-detected"


class TestBuildMessages:
    def test_separates_system_message(self, provider):
        """Test that system message is extracted correctly."""
        messages = [
            ChatMessage(role="system", content="Be helpful"),
            ChatMessage(role="user", content="Hi"),
            ChatMessage(role="assistant", content="Hello"),
            ChatMessage(role="user", content="How are you?"),
        ]

        system, api_messages = provider._build_messages(messages)

        assert system == "Be helpful"
        assert len(api_messages) == 3
        assert api_messages[0]["role"] == "user"
        assert api_messages[1]["role"] == "assistant"
        assert api_messages[2]["role"] == "user"

    def test_no_system_message(self, provider):
        """Test handling when no system message is provided."""
        messages = [
            ChatMessage(role="user", content="Hi"),
        ]

        system, api_messages = provider._build_messages(messages)

        assert system is None
        assert len(api_messages) == 1


class TestFactoryPattern:
    def test_factory_creates_anthropic(self):
        """Test that factory creates AnthropicProvider when configured."""
        with patch("app.config.settings") as mock_settings:
            mock_settings.ai_provider = "anthropic"
            mock_settings.anthropic_api_key = "test-key"

            from app.services.ai_provider import get_ai_provider

            provider = get_ai_provider()
            assert isinstance(provider, AnthropicProvider)

    def test_factory_raises_on_unknown(self):
        """Test that factory raises ValueError for unknown provider."""
        with patch("app.config.settings") as mock_settings:
            mock_settings.ai_provider = "unknown_provider"

            from app.services.ai_provider import get_ai_provider

            with pytest.raises(ValueError, match="Unknown AI provider"):
                get_ai_provider()
