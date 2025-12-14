from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas.translate import TranslateResponse


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


class TestTranslateEndpoint:
    async def test_translate_success(self, client: AsyncClient):
        """Test successful translation."""
        mock_response = TranslateResponse(
            translated_text="Hola, como estas?",
            source_language="English",
            target_language="Spanish",
            model="gpt-3.5-turbo",
            usage={"prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30},
        )

        with patch("app.api.v1.translate.translate_text", new_callable=AsyncMock) as mock:
            mock.return_value = mock_response

            response = await client.post(
                "/api/v1/translate",
                json={
                    "text": "Hello, how are you?",
                    "source_language": "English",
                    "target_language": "Spanish",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["translated_text"] == "Hola, como estas?"
            assert data["target_language"] == "Spanish"

    async def test_translate_auto_detect(self, client: AsyncClient):
        """Test translation with auto language detection."""
        mock_response = TranslateResponse(
            translated_text="Hello",
            source_language="auto-detected",
            target_language="English",
            model="gpt-3.5-turbo",
            usage={"prompt_tokens": 20, "completion_tokens": 5, "total_tokens": 25},
        )

        with patch("app.api.v1.translate.translate_text", new_callable=AsyncMock) as mock:
            mock.return_value = mock_response

            response = await client.post(
                "/api/v1/translate",
                json={
                    "text": "Bonjour",
                    "source_language": "auto",
                    "target_language": "English",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["source_language"] == "auto-detected"

    async def test_translate_validation_empty_text(self, client: AsyncClient):
        """Test validation error for empty text."""
        response = await client.post(
            "/api/v1/translate",
            json={
                "text": "",
                "target_language": "Spanish",
            },
        )
        assert response.status_code == 422

    async def test_translate_missing_target_language(self, client: AsyncClient):
        """Test validation error for missing target language."""
        response = await client.post(
            "/api/v1/translate",
            json={
                "text": "Hello",
            },
        )
        assert response.status_code == 422

    async def test_translate_text_too_long(self, client: AsyncClient):
        """Test validation error for text exceeding max length."""
        response = await client.post(
            "/api/v1/translate",
            json={
                "text": "x" * 10001,  # Exceeds 10000 limit
                "target_language": "Spanish",
            },
        )
        assert response.status_code == 422
